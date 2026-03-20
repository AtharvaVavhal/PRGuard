import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import PRContext
from app import github_client, formatter

# Use real or mock reviewer based on env flag
USE_MOCK = os.getenv("USE_MOCK_AI", "false").lower() == "true"
if USE_MOCK:
    from app.ai_reviewer import mock_review_pr as review_pr
else:
    from app.ai_reviewer import review_pr

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PR Reviewer starting up (mock_ai=%s, threshold=%d)", USE_MOCK, settings.PASS_SCORE_THRESHOLD)
    yield
    logger.info("PR Reviewer shutting down")


app = FastAPI(title="PR Reviewer", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------
def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """Validate GitHub's X-Hub-Signature-256 header."""
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("No GITHUB_WEBHOOK_SECRET set — skipping signature check")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ---------------------------------------------------------------------------
# Core review pipeline
# ---------------------------------------------------------------------------
def _run_review(ctx: PRContext) -> None:
    """Synchronous pipeline: fetch diff → AI review → comment + status."""
    logger.info("Starting review for %s#%d", ctx.repo_full_name, ctx.pr_number)

    # 1. Set status to pending immediately
    github_client.set_commit_status(
        ctx.repo_full_name, ctx.head_sha,
        state="pending",
        description="PR review in progress…",
    )

    try:
        # 2. AI review
        result = review_pr(ctx.pr_title, ctx.diff, threshold=settings.PASS_SCORE_THRESHOLD)

        # 3. Format and post comment
        comment = formatter.build_comment(result, threshold=settings.PASS_SCORE_THRESHOLD)
        github_client.post_pr_comment(ctx.repo_full_name, ctx.pr_number, comment)

        # 4. Set final commit status
        if result.passed:
            github_client.set_commit_status(
                ctx.repo_full_name, ctx.head_sha,
                state="success",
                description=f"Quality score {result.score:.1f}/10 — passed ✅",
            )
        else:
            github_client.set_commit_status(
                ctx.repo_full_name, ctx.head_sha,
                state="failure",
                description=f"Quality score {result.score:.1f}/10 — below threshold of {settings.PASS_SCORE_THRESHOLD} ❌",
            )

        logger.info("Review posted: score=%.1f passed=%s", result.score, result.passed)

    except Exception as exc:
        logger.exception("Review pipeline failed: %s", exc)
        github_client.set_commit_status(
            ctx.repo_full_name, ctx.head_sha,
            state="error",
            description="PR reviewer encountered an internal error",
        )
        raise


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------
@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_bytes = await request.body()

    # Signature check
    sig = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(payload_bytes, sig):
        logger.warning("Invalid webhook signature — rejecting request")
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        logger.debug("Ignoring event type: %s", event)
        return JSONResponse({"status": "ignored", "event": event})

    payload = await request.json()
    action = payload.get("action", "")

    # Only review on open / synchronize (new commits pushed)
    if action not in ("opened", "synchronize", "reopened"):
        logger.debug("Ignoring PR action: %s", action)
        return JSONResponse({"status": "ignored", "action": action})

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    pr_title = pr["title"]

    logger.info("Received PR event: %s action=%s pr=#%d", repo, action, pr_number)

    # Fetch diff (do this in the request handler so errors surface early)
    try:
        diff = github_client.get_pr_diff(repo, pr_number)
    except Exception as exc:
        logger.exception("Failed to fetch diff: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to fetch PR diff from GitHub")

    if not diff.strip():
        logger.info("Empty diff — skipping review")
        return JSONResponse({"status": "skipped", "reason": "empty diff"})

    ctx = PRContext(
        repo_full_name=repo,
        pr_number=pr_number,
        pr_title=pr_title,
        head_sha=head_sha,
        diff=diff,
    )

    # Run review in background so webhook returns quickly (GitHub expects <10s)
    background_tasks.add_task(_run_review, ctx)

    return JSONResponse({"status": "accepted", "pr": pr_number})


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "threshold": settings.PASS_SCORE_THRESHOLD, "mock_ai": USE_MOCK}
