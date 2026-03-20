import json
import logging
from groq import Groq
from app.config import settings
from app.models import ReviewResult, CodeIssue
from app import github_client

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)

FIX_SYSTEM_PROMPT = """You are a senior software engineer. You will be given a file's content and a specific issue found in it.
Your job is to return the ENTIRE fixed file content with the issue resolved.

STRICT RULES:
- Return ONLY the raw file content. No markdown, no backticks, no explanation.
- Do not remove any functionality. Only fix the specific issue described.
- Keep all existing imports, logic, and structure intact.
- If you cannot fix the issue confidently, return the original file content unchanged."""


def _fix_file(file_content: str, issue: CodeIssue) -> str:
    prompt = (
        f"FILE CONTENT:\n{file_content}\n\n"
        f"ISSUE TO FIX:\n"
        f"Category: {issue.category}\n"
        f"Description: {issue.description}\n"
        f"Suggested Fix: {issue.suggested_fix}\n\n"
        f"Return the entire fixed file content only."
    )

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": FIX_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content.strip()


def run_auto_fix(
    repo: str,
    pr_number: int,
    head_sha: str,
    base_branch: str,
    result: ReviewResult,
) -> str | None:
    """
    Creates a fix branch, applies AI fixes for each issue, pushes the changes,
    and returns the fix branch name. Returns None if nothing was fixed.
    """

    fix_branch = f"prguard/fix-pr-{pr_number}-{head_sha[:7]}"

    # Group issues by file so we fetch each file only once
    issues_by_file: dict[str, list[CodeIssue]] = {}
    for issue in result.issues:
        if issue.file:
            issues_by_file.setdefault(issue.file, []).append(issue)

    if not issues_by_file:
        logger.info("No fixable issues found for PR #%d", pr_number)
        return None

    # Create the fix branch from the PR head SHA
    try:
        github_client.create_branch(repo, fix_branch, head_sha)
        logger.info("Created fix branch '%s'", fix_branch)
    except Exception as exc:
        logger.error("Failed to create fix branch: %s", exc)
        return None

    fixed_files = []

    for file_path, issues in issues_by_file.items():
        try:
            # Fetch current file content
            file_content, file_sha = github_client.get_file(repo, file_path, head_sha)

            # Apply fixes sequentially for all issues in this file
            fixed_content = file_content
            for issue in issues:
                logger.info("Fixing issue in %s: %s", file_path, issue.category)
                fixed_content = _fix_file(fixed_content, issue)

            # Push the fixed file to the fix branch
            github_client.push_file(
                repo=repo,
                branch=fix_branch,
                path=file_path,
                content=fixed_content,
                file_sha=file_sha,
                commit_message=f"fix: auto-fix {len(issues)} issue(s) in {file_path} [PRGuard]",
            )

            fixed_files.append(file_path)
            logger.info("Pushed fix for %s", file_path)

        except Exception as exc:
            logger.warning("Could not fix %s: %s", file_path, exc)
            continue

    if not fixed_files:
        logger.warning("No files were successfully fixed")
        return None

    logger.info("Auto-fix complete. Fixed files: %s", fixed_files)
    return fix_branch
