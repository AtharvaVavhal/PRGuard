import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse

from app.config import settings
from app.models import PRContext
from app import github_client, formatter, auto_fixer, database, rules as repo_rules

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

DASHBOARD_HTML = Path(__file__).parent / "dashboard.html"


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    logger.info("PR Reviewer starting up (mock_ai=%s, threshold=%d)", USE_MOCK, settings.PASS_SCORE_THRESHOLD)
    yield
    logger.info("PR Reviewer shutting down")


app = FastAPI(title="PR Reviewer", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_line(line_range: str | None) -> int:
    if not line_range:
        return 1
    try:
        return int(line_range.replace("L", "").split("-")[0])
    except:
        return 1


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------
def _verify_signature(payload: bytes, signature_header: str | None) -> bool:
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
    logger.info("Starting review for %s#%d", ctx.repo_full_name, ctx.pr_number)

    # 1. Pending status
    github_client.set_commit_status(
        ctx.repo_full_name,
        ctx.head_sha,
        state="pending",
        description="PR review in progress…",
    )

    try:
        # 2. Fetch custom rules from prguard.yml
        repo_config = repo_rules.fetch_repo_rules(ctx.repo_full_name, ctx.head_sha)
        custom_rules = repo_config["rules"]
        threshold = repo_config["threshold"] or settings.PASS_SCORE_THRESHOLD

        if custom_rules:
            logger.info("Applying %d custom rules from prguard.yml", len(custom_rules))

        # 3. AI review
        result = review_pr(
            ctx.pr_title,
            ctx.diff,
            threshold=threshold,
            custom_rules=custom_rules,
        )

        # 4. Inline comments
        for issue in result.issues:
            try:
                line = extract_line(issue.line_range)
                github_client.post_inline_comment(
                    repo=ctx.repo_full_name,
                    pr_number=ctx.pr_number,
                    body=(
                        f"[{issue.severity.value.upper()}] {issue.category.upper()}\n\n"
                        f"{issue.description}\n\nFix:\n{issue.suggested_fix}"
                    ),
                    commit_id=ctx.head_sha,
                    path=issue.file,
                    line=line,
                )
            except Exception as e:
                logger.warning("Inline comment failed: %s", e)

        # 5. Summary comment
        comment = formatter.build_comment(result, threshold=threshold)
        github_client.post_pr_comment(ctx.repo_full_name, ctx.pr_number, comment)

        # 6. Auto-fix — only run if PR failed review
        fix_branch = None
        if not result.passed:
            logger.info("PR failed review, running auto-fixer...")
            fix_branch = auto_fixer.run_auto_fix(
                repo=ctx.repo_full_name,
                pr_number=ctx.pr_number,
                head_sha=ctx.head_sha,
                base_branch=ctx.base_branch,
                result=result,
            )

            if fix_branch:
                fix_comment = (
                    f"🤖 **PRGuard Auto-Fix**\n\n"
                    f"I've created a fix branch with suggested corrections:\n\n"
                    f"**Branch:** `{fix_branch}`\n\n"
                    f"To review and apply the fixes:\n"
                    f"```bash\n"
                    f"git fetch origin {fix_branch}\n"
                    f"git checkout {fix_branch}\n"
                    f"```\n\n"
                    f"> ⚠️ Always review AI-generated fixes before merging."
                )
                github_client.post_pr_comment(ctx.repo_full_name, ctx.pr_number, fix_comment)

        # 7. Save to database
        database.save_review(
            repo=ctx.repo_full_name,
            pr_number=ctx.pr_number,
            pr_title=ctx.pr_title,
            score=result.score,
            passed=result.passed,
            issues=[i.model_dump() for i in result.issues],
            fix_branch=fix_branch,
        )

        # 8. Final status
        if result.passed:
            github_client.set_commit_status(
                ctx.repo_full_name,
                ctx.head_sha,
                state="success",
                description=f"Quality score {result.score:.1f}/10 — passed ✅",
            )
        else:
            github_client.set_commit_status(
                ctx.repo_full_name,
                ctx.head_sha,
                state="failure",
                description=f"Quality score {result.score:.1f}/10 — below threshold of {threshold} ❌",
            )

        logger.info("Review posted: score=%.1f passed=%s", result.score, result.passed)

    except Exception as exc:
        logger.exception("Review pipeline failed: %s", exc)
        github_client.set_commit_status(
            ctx.repo_full_name,
            ctx.head_sha,
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

    sig = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(payload_bytes, sig):
        logger.warning("Invalid webhook signature — rejecting request")
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return JSONResponse({"status": "ignored", "event": event})

    payload = await request.json()
    action = payload.get("action", "")

    if action not in ("opened", "synchronize", "reopened"):
        return JSONResponse({"status": "ignored", "action": action})

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    head_sha = pr["head"]["sha"]
    pr_title = pr["title"]
    base_branch = pr["base"]["ref"]

    logger.info("Received PR event: %s action=%s pr=#%d", repo, action, pr_number)

    try:
        diff = github_client.get_pr_diff(repo, pr_number)
    except Exception as exc:
        logger.exception("Failed to fetch diff: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to fetch PR diff")

    if not diff.strip():
        return JSONResponse({"status": "skipped", "reason": "empty diff"})

    ctx = PRContext(
        repo_full_name=repo,
        pr_number=pr_number,
        pr_title=pr_title,
        head_sha=head_sha,
        base_branch=base_branch,
        diff=diff,
    )

    background_tasks.add_task(_run_review, ctx)
    return JSONResponse({"status": "accepted", "pr": pr_number})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML.read_text(), status_code=200)


@app.get("/api/stats")
def api_stats():
    return JSONResponse(database.get_stats())


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "threshold": settings.PASS_SCORE_THRESHOLD,
        "mock_ai": USE_MOCK,
    }
