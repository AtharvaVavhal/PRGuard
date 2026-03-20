import base64
import logging
import httpx
import yaml

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.github.com"

DEFAULT_RULES = {
    "rules": [],
    "threshold": None,  # None means use global settings.PASS_SCORE_THRESHOLD
}


def _headers():
    token = settings.GITHUB_TOKEN
    if not token:
        raise ValueError("GITHUB_TOKEN is missing")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_repo_rules(repo: str, ref: str) -> dict:
    """
    Fetch and parse prguard.yml from the repo root at the given ref.
    Returns a dict with 'rules' (list[str]) and 'threshold' (int | None).
    Falls back to DEFAULT_RULES if the file doesn't exist or is invalid.
    """
    url = f"{BASE_URL}/repos/{repo}/contents/prguard.yml"

    try:
        with httpx.Client(headers=_headers(), timeout=10) as client:
            resp = client.get(url, params={"ref": ref})

            if resp.status_code == 404:
                logger.info("No prguard.yml found in %s — using default rules", repo)
                return DEFAULT_RULES.copy()

            resp.raise_for_status()
            data = resp.json()

        raw_content = base64.b64decode(data["content"]).decode("utf-8")
        parsed = yaml.safe_load(raw_content)

        if not isinstance(parsed, dict):
            logger.warning("prguard.yml in %s is not a valid YAML dict — ignoring", repo)
            return DEFAULT_RULES.copy()

        rules = parsed.get("rules", [])
        threshold = parsed.get("threshold", None)

        # Validate rules is a list of strings
        if not isinstance(rules, list):
            rules = []
        rules = [str(r) for r in rules if r]

        # Validate threshold is an int between 0-10
        if threshold is not None:
            try:
                threshold = int(threshold)
                threshold = max(0, min(10, threshold))
            except (ValueError, TypeError):
                threshold = None

        logger.info(
            "Loaded prguard.yml from %s: %d custom rules, threshold=%s",
            repo, len(rules), threshold
        )

        return {"rules": rules, "threshold": threshold}

    except Exception as exc:
        logger.warning("Failed to fetch prguard.yml from %s: %s", repo, exc)
        return DEFAULT_RULES.copy()
