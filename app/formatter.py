from app.models import ReviewResult, Severity

SEVERITY_EMOJI = {
    Severity.HIGH:   "🔴",
    Severity.MEDIUM: "🟡",
    Severity.LOW:    "🟢",
}

CATEGORY_EMOJI = {
    "naming":         "🏷️",
    "complexity":     "🧩",
    "duplication":    "♻️",
    "error_handling": "⚠️",
    "magic_values":   "🔢",
    "security":       "🔐",
    "type_safety":    "🛡️",
    "dead_code":      "💀",
    "custom":         "📋",
}


def build_comment(result: ReviewResult, threshold: int) -> str:
    score = result.score
    passed = result.passed

    # Header
    if passed:
        status_line = f"## ✅ PRGuard Review — PASSED ({score:.1f}/10)"
        bar = _score_bar(score)
        header = f"{status_line}\n\n{bar}\n\n> Quality score **{score:.1f}/10** meets the threshold of **{threshold}/10**. This PR is good to merge."
    else:
        status_line = f"## ❌ PRGuard Review — FAILED ({score:.1f}/10)"
        bar = _score_bar(score)
        header = f"{status_line}\n\n{bar}\n\n> Quality score **{score:.1f}/10** is below the threshold of **{threshold}/10**. Fix the issues below before merging."

    # Summary
    summary_section = f"### 📋 Summary\n{result.summary}"

    # Issues breakdown
    if not result.issues:
        issues_section = "### ✨ Issues\nNo issues found."
    else:
        high   = [i for i in result.issues if i.severity == Severity.HIGH]
        medium = [i for i in result.issues if i.severity == Severity.MEDIUM]
        low    = [i for i in result.issues if i.severity == Severity.LOW]

        counts = []
        if high:   counts.append(f"🔴 **{len(high)} High**")
        if medium: counts.append(f"🟡 **{len(medium)} Medium**")
        if low:    counts.append(f"🟢 **{len(low)} Low**")

        issues_section = f"### 🐛 Issues Found — {' · '.join(counts)}\n\n"

        for issue in result.issues:
            sev_emoji  = SEVERITY_EMOJI.get(issue.severity, "⚪")
            cat_emoji  = CATEGORY_EMOJI.get(issue.category, "🔍")
            location   = f"`{issue.file}`"
            if issue.line_range:
                location += f" {issue.line_range}"

            issues_section += (
                f"<details>\n"
                f"<summary>{sev_emoji} {cat_emoji} <strong>{issue.category.upper()}</strong> — {location}</summary>\n\n"
                f"**Problem:** {issue.description}\n\n"
                f"**Fix:**\n{issue.suggested_fix}\n\n"
                f"</details>\n\n"
            )

    # Stats footer
    total_issues = len(result.issues)
    footer = (
        f"---\n"
        f"<sub>🛡️ PRGuard · {total_issues} issue{'s' if total_issues != 1 else ''} found · "
        f"Threshold: {threshold}/10 · "
        f"💬 Ask me anything: `/prguard <question>`</sub>"
    )

    return "\n\n".join([header, summary_section, issues_section, footer])


def _score_bar(score: float) -> str:
    filled = round(score)
    empty  = 10 - filled

    if score >= 7:
        color = "🟩"
    elif score >= 5:
        color = "🟨"
    else:
        color = "🟥"

    bar = color * filled + "⬜" * empty
    return f"`{bar}` **{score:.1f}/10**"
