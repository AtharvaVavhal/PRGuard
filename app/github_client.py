import base64
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"


def _headers():
    token = settings.GITHUB_TOKEN
    if not token:
        raise ValueError("GITHUB_TOKEN is missing")

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _client() -> httpx.Client:
    return httpx.Client(headers=_headers(), timeout=30)


# -------------------- PR DATA --------------------

def get_pr_diff(repo: str, pr_number: int) -> str:
    url = f"{BASE_URL}/repos/{repo}/pulls/{pr_number}"

    with _client() as client:
        resp = client.get(
            url,
            headers={**_headers(), "Accept": "application/vnd.github.v3.diff"},
        )
        resp.raise_for_status()

        diff = resp.text
        logger.info("Fetched diff for %s#%d (%d chars)", repo, pr_number, len(diff))
        return diff


def get_pr_metadata(repo: str, pr_number: int) -> dict:
    url = f"{BASE_URL}/repos/{repo}/pulls/{pr_number}"

    with _client() as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

        return {
            "title": data["title"],
            "head_sha": data["head"]["sha"],
            "author": data["user"]["login"],
        }


# -------------------- COMMENTS --------------------

def post_pr_comment(repo: str, pr_number: int, body: str) -> None:
    url = f"{BASE_URL}/repos/{repo}/issues/{pr_number}/comments"

    with _client() as client:
        resp = client.post(url, json={"body": body})
        resp.raise_for_status()
        logger.info("Posted summary comment on %s#%d", repo, pr_number)


def post_inline_comment(
    repo: str,
    pr_number: int,
    body: str,
    commit_id: str,
    path: str,
    line: int,
):
    url = f"{BASE_URL}/repos/{repo}/pulls/{pr_number}/comments"

    payload = {
        "body": body,
        "commit_id": commit_id,
        "path": path,
        "line": line,
        "side": "RIGHT",
    }

    with _client() as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        logger.info("Inline comment posted on %s:%d", path, line)


# -------------------- COMMIT STATUS --------------------

def set_commit_status(
    repo: str,
    sha: str,
    state: str,
    description: str = "",
    context: str = "pr-review",
) -> None:
    """
    state: pending | success | failure | error
    """
    url = f"{BASE_URL}/repos/{repo}/statuses/{sha}"

    payload = {
        "state": state,
        "description": description,
        "context": context,
    }

    with _client() as client:
        resp = client.post(url, json=payload)

        try:
            resp.raise_for_status()
            logger.info("Set commit status '%s' on %s@%s", state, repo, sha[:7])
        except httpx.HTTPStatusError:
            logger.error("Commit status failed: %s", resp.text)
            raise


# -------------------- CHECKS API --------------------

def create_check_run(
    repo: str,
    sha: str,
    name: str,
    status: str,
    conclusion: str | None,
    output: dict,
):
    """
    status: queued | in_progress | completed
    conclusion: success | failure | neutral (only when completed)
    """
    url = f"{BASE_URL}/repos/{repo}/check-runs"

    payload = {
        "name": name,
        "head_sha": sha,
        "status": status,
        "output": {
            "title": output.get("title", "PR Review"),
            "summary": output.get("summary", ""),
        },
    }

    if status == "completed":
        payload["conclusion"] = conclusion

    with _client() as client:
        resp = client.post(url, json=payload)

        try:
            resp.raise_for_status()
            logger.info(
                "Check run '%s' (%s) created for %s@%s",
                name,
                status,
                repo,
                sha[:7],
            )
        except httpx.HTTPStatusError:
            logger.error("Check run failed: %s", resp.text)
            raise


# -------------------- AUTO-FIX HELPERS --------------------

def get_file(repo: str, path: str, ref: str) -> tuple[str, str]:
    """
    Fetch file content and its SHA from GitHub.
    Returns (decoded_content, file_sha).
    """
    url = f"{BASE_URL}/repos/{repo}/contents/{path}"

    with _client() as client:
        resp = client.get(url, params={"ref": ref})
        resp.raise_for_status()
        data = resp.json()

    file_sha = data["sha"]
    decoded_content = base64.b64decode(data["content"]).decode("utf-8")
    logger.info("Fetched file %s @ %s", path, ref[:7])
    return decoded_content, file_sha


def create_branch(repo: str, branch_name: str, sha: str) -> None:
    """
    Create a new branch pointing at the given SHA.
    """
    url = f"{BASE_URL}/repos/{repo}/git/refs"

    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    }

    with _client() as client:
        resp = client.post(url, json=payload)

        try:
            resp.raise_for_status()
            logger.info("Created branch '%s' at %s", branch_name, sha[:7])
        except httpx.HTTPStatusError:
            logger.error("Create branch failed: %s", resp.text)
            raise


def push_file(
    repo: str,
    branch: str,
    path: str,
    content: str,
    file_sha: str,
    commit_message: str,
) -> None:
    """
    Push updated file content to a branch.
    """
    url = f"{BASE_URL}/repos/{repo}/contents/{path}"

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "sha": file_sha,
        "branch": branch,
    }

    with _client() as client:
        resp = client.put(url, json=payload)

        try:
            resp.raise_for_status()
            logger.info("Pushed fix to %s on branch '%s'", path, branch)
        except httpx.HTTPStatusError:
            logger.error("Push file failed: %s", resp.text)
            raise
