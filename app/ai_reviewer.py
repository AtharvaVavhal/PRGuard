import json
import logging
import os
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.models import ReviewResult, CodeIssue, Severity

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = """You are a strict, senior software engineer performing a mandatory code quality gate review.
Your job is NOT to be helpful or encouraging. Your job is to enforce quality standards.

SCORING RULES (be consistent and harsh):
- 9-10: Near-perfect. Clean logic, excellent naming, no duplication, handles edge cases.
- 7-8:  Acceptable for production. Minor issues only. No structural problems.
- 5-6:  Borderline. Has real problems that need fixing before merge.
- 3-4:  Poor quality. Multiple critical issues. Do not merge.
- 0-2:  Unacceptable. Rewrite required.

WHAT YOU MUST FLAG (never skip these):
1. NAMING: Variables/functions named with single letters, abbreviations (e.g. `d`, `tmp`, `res`, `mgr`), or misleading names.
2. COMPLEXITY: Functions longer than 30 lines, deeply nested conditionals (>3 levels), or a function doing more than one thing.
3. DUPLICATION: Any block of logic repeated more than once without abstraction.
4. ERROR HANDLING: Missing try/except on I/O, network, or DB calls. Silent `except: pass` blocks. Bare exceptions.
5. MAGIC VALUES: Hardcoded strings/numbers that should be constants or config.
6. SECURITY: Secrets in code, SQL string interpolation, missing input validation.
7. TYPE SAFETY: Missing type hints in Python, implicit `any` in TypeScript.
8. DEAD CODE: Commented-out code blocks, unused imports, unused variables.

STRICT INSTRUCTIONS:
- Be specific. Never say "consider refactoring". Say exactly what is wrong and exactly how to fix it.
- Reference exact file names and approximate line ranges from the diff.
- Do not praise good code. Only report problems.
- Do not soften language. Be direct.
- Score must reflect issue severity and count. Multiple HIGH issues cannot score above 6.

OUTPUT FORMAT — respond ONLY with a valid JSON object, no markdown, no explanation, no ```json fences:
{
  "score": <float 0-10>,
  "summary": "<2-3 sentence verdict on overall PR quality>",
  "issues": [
    {
      "file": "<filename>",
      "line_range": "<e.g. L12-L28 or null>",
      "category": "<naming|complexity|duplication|error_handling|magic_values|security|type_safety|dead_code>",
      "severity": "<low|medium|high>",
      "description": "<exact problem, no vagueness>",
      "suggested_fix": "<exact fix, with code snippet if needed>"
    }
  ]
}"""


def _build_prompt(pr_title: str, diff: str) -> str:
    MAX_DIFF_CHARS = 12_000
    truncated = diff[:MAX_DIFF_CHARS]
    if len(diff) > MAX_DIFF_CHARS:
        truncated += f"\n\n[DIFF TRUNCATED — {len(diff) - MAX_DIFF_CHARS} additional chars not shown]"
    return f"{SYSTEM_PROMPT}\n\nPR TITLE: {pr_title}\n\nDIFF:\n{truncated}\n\nReturn only the JSON object."


def review_pr(pr_title: str, diff: str, threshold: Optional[int] = None) -> ReviewResult:
    if threshold is None:
        threshold = settings.PASS_SCORE_THRESHOLD

    logger.info("Sending diff to Gemini for review (diff_len=%d)", len(diff))

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    response = model.generate_content(_build_prompt(pr_title, diff))
    raw = response.text.strip()

    # Strip markdown fences if Gemini adds them despite mime type
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    logger.debug("Raw Gemini response: %s", raw[:500])
    data = json.loads(raw)

    issues = [
        CodeIssue(
            file=i["file"],
            line_range=i.get("line_range"),
            category=i["category"],
            severity=Severity(i["severity"]),
            description=i["description"],
            suggested_fix=i["suggested_fix"],
        )
        for i in data.get("issues", [])
    ]

    result = ReviewResult(
        score=float(data["score"]),
        summary=data["summary"],
        issues=issues,
        passed=float(data["score"]) >= threshold,
    )

    logger.info("Review complete: score=%.1f passed=%s issues=%d", result.score, result.passed, len(result.issues))
    return result


def mock_review_pr(pr_title: str, diff: str, threshold: Optional[int] = None) -> ReviewResult:
    if threshold is None:
        threshold = settings.PASS_SCORE_THRESHOLD
    issues = [
        CodeIssue(
            file="src/handler.py",
            line_range="L14-L22",
            category="complexity",
            severity=Severity.HIGH,
            description="Function `process` is 45 lines long and handles both validation and DB writes. Split into two functions.",
            suggested_fix="Extract DB logic into `_persist_record(data)` and keep `process()` as orchestrator only.",
        ),
        CodeIssue(
            file="src/utils.py",
            line_range="L3",
            category="naming",
            severity=Severity.MEDIUM,
            description="Variable `d` is used as the main data dictionary. Name conveys no meaning.",
            suggested_fix="Rename `d` to `user_payload` or `request_data` depending on context.",
        ),
        CodeIssue(
            file="src/handler.py",
            line_range="L30",
            category="error_handling",
            severity=Severity.HIGH,
            description="`requests.post()` call has no try/except. A network failure will crash the worker.",
            suggested_fix="Wrap in try/except requests.RequestException and log + return error response.",
        ),
    ]
    score = 4.5
    return ReviewResult(
        score=score,
        summary="This PR has structural and reliability problems. Two HIGH severity issues must be resolved before merge.",
        issues=issues,
        passed=score >= threshold,
    )
