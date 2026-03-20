import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _client() -> httpx.Client:
    return httpx.Client(headers=HEADERS, timeout=30)


def get_pr_diff(repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a pull request."""
    url = f"{BASE_URL}/repos/{repo}/pulls/{pr_number}"
    with _client() as client:
        resp = client.get(url, headers={**HEADERS, "Accept": "application/vnd.github.v3.diff"})
        resp.raise_for_status()
        diff = resp.text
        logger.info("Fetched diff for %s#%d (%d chars)", repo, pr_number, len(diff))
        return diff


def get_pr_metadata(repo: str, pr_number: int) -> dict:
    """Fetch PR title, head SHA, and other metadata."""
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


def post_pr_comment(repo: str, pr_number: int, body: str) -> None:
    """Post a comment on the pull request."""
    url = f"{BASE_URL}/repos/{repo}/issues/{pr_number}/comments"
    with _client() as client:
        resp = client.post(url, json={"body": body})
        resp.raise_for_status()
        logger.info("Posted comment on %s#%d", repo, pr_number)


def set_commit_status(repo: str, sha: str, state: str, description: str, context: str = "pr-reviewer/quality") -> None:
    """
    Set a GitHub commit status.
    state: 'success' | 'failure' | 'pending' | 'error'
    """
    url = f"{BASE_URL}/repos/{repo}/statuses/{sha}"
    payload = {
        "state": state,
        "description": description[:140],   # GitHub limit
        "context": context,
    }
    with _client() as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        logger.info("Set commit status '%s' on %s@%s", state, repo, sha[:7])
