import logging
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.GROQ_API_KEY)

CHAT_SYSTEM_PROMPT = """You are PRGuard, an AI code review assistant. You have just reviewed a Pull Request and have access to the full review results.

Your job is to answer the developer's question about their PR clearly and helpfully.

RULES:
- Be direct and specific. Reference exact files, line numbers, and issues from the review.
- If the question is about fixing an issue, give concrete code-level advice.
- If the question is unrelated to the PR review, politely say you can only help with this PR.
- Keep responses concise — under 300 words unless a detailed explanation is truly needed.
- Format your response in GitHub Markdown."""


def _build_context(review: dict) -> str:
    issues_text = ""
    for i, issue in enumerate(review.get("issues", []), 1):
        issues_text += (
            f"{i}. [{issue['severity'].upper()}] {issue['category'].upper()} "
            f"in `{issue['file']}` {issue.get('line_range') or ''}\n"
            f"   Problem: {issue['description']}\n"
            f"   Fix: {issue['suggested_fix']}\n\n"
        )

    return (
        f"PR TITLE: {review.get('pr_title', 'Unknown')}\n"
        f"SCORE: {review.get('score', '?')}/10\n"
        f"RESULT: {'PASSED ✅' if review.get('passed') else 'FAILED ❌'}\n"
        f"SUMMARY: {review.get('summary', '')}\n\n"
        f"ISSUES FOUND:\n{issues_text or 'No issues found.'}"
    )


def answer_question(question: str, review: dict) -> str:
    """
    Given a user's question and the review dict from DB, return an answer.
    """
    context = _build_context(review)

    prompt = (
        f"Here is the PR review context:\n\n"
        f"{context}\n\n"
        f"Developer's question: {question}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        answer = response.choices[0].message.content.strip()
        logger.info("Chat answer generated (%d chars)", len(answer))
        return answer

    except Exception as exc:
        logger.error("Chat answer failed: %s", exc)
        return "Sorry, I couldn't generate a response right now. Please try again in a moment."
