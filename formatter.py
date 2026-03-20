from app.models import ReviewResult, Severity

_SEVERITY_EMOJI = {
    Severity.HIGH: "🔴",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🔵",
}

_SCORE_BAR_FILLED = "█"
_SCORE_BAR_EMPTY = "░"


def _score_bar(score: float) -> str:
    filled = round(score)
    return _SCORE_BAR_FILLED * filled + _SCORE_BAR_EMPTY * (10 - filled)


def build_comment(result: ReviewResult, threshold: int) -> str:
    status_line = (
        "## ✅ PR Review — PASSED" if result.passed
        else "## ❌ PR Review — FAILED"
    )

    bar = _score_bar(result.score)
    score_line = f"**Score:** `{result.score:.1f} / 10`  `{bar}`  _(threshold: {threshold})_"

    lines = [
        status_line,
        "",
        score_line,
        "",
        f"> {result.summary}",
        "",
    ]

    if not result.issues:
        lines.append("_No issues detected._")
    else:
        # Group by severity
        for severity in [Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            group = [i for i in result.issues if i.severity == severity]
            if not group:
                continue

            emoji = _SEVERITY_EMOJI[severity]
            lines.append(f"### {emoji} {severity.value.upper()} severity ({len(group)})")
            lines.append("")

            for issue in group:
                loc = f"`{issue.file}`"
                if issue.line_range:
                    loc += f" {issue.line_range}"
                lines.append(f"**[{issue.category}]** {loc}")
                lines.append(f"- **Problem:** {issue.description}")
                lines.append(f"- **Fix:** {issue.suggested_fix}")
                lines.append("")

    lines += [
        "---",
        "_Powered by [pr-reviewer](https://github.com/your-org/pr-reviewer). "
        "Score must be ≥ {} to merge._".format(threshold),
    ]

    return "\n".join(lines)
