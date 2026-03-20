from app.models import ReviewResult, Severity

SEVERITY_EMOJI = {
    Severity.HIGH:   "🔴",
    Severity.MEDIUM: "🟡",
    Severity.LOW:    "🟢",
}

CATEGORY_LABEL = {
    "naming":         "🏷️  Naming",
    "complexity":     "🧩  Complexity",
    "duplication":    "♻️  Duplication",
    "error_handling": "⚠️  Error Handling",
    "magic_values":   "🔢  Magic Values",
    "security":       "🔐  Security",
    "type_safety":    "🛡️  Type Safety",
    "dead_code":      "💀  Dead Code",
    "custom":         "📋  Custom Rule",
}


def _score_bar(score: float) -> str:
    filled = round(score)
    empty  = 10 - filled
    if score >= 7:
        block = "█"
        color_start = ""
    elif score >= 5:
        block = "▓"
        color_start = ""
    else:
        block = "░"
        color_start = ""

    bar = block * filled + "·" * empty
    return f"`{bar}` **{score:.1f} / 10**"


def build_comment(result: ReviewResult, threshold: int) -> str:
    score  = result.score
    passed = result.passed

    # ── Header ──────────────────────────────────────────────────────────────
    if passed:
        header = (
            f"## ✅ PRGuard — Quality Gate **PASSED**\n\n"
            f"{_score_bar(score)}\n\n"
            f"> Score **{score:.1f}/10** meets the threshold of **{threshold}/10**. Ready to merge. 🚀"
        )
    else:
        header = (
            f"## ❌ PRGuard — Quality Gate **FAILED**\n\n"
            f"{_score_bar(score)}\n\n"
            f"> Score **{score:.1f}/10** is below the threshold of **{threshold}/10**. Fix the issues below before merging."
        )

    # ── Summary ─────────────────────────────────────────────────────────────
    summary = f"### 📋 Verdict\n{result.summary}"

    # ── Issues ──────────────────────────────────────────────────────────────
    if not result.issues:
        issues_section = "### ✨ No Issues Found\nThis PR is clean. Well done."
    else:
        high   = [i for i in result.issues if i.severity == Severity.HIGH]
        medium = [i for i in result.issues if i.severity == Severity.MEDIUM]
        low    = [i for i in result.issues if i.severity == Severity.LOW]

        counts_str = " · ".join(filter(None, [
            f"🔴 {len(high)} High"   if high   else "",
            f"🟡 {len(medium)} Med"  if medium else "",
            f"🟢 {len(low)} Low"     if low    else "",
        ]))

        issues_section = f"### 🐛 Issues — {counts_str}\n\n"

        # Group by severity: high first
        for issue in sorted(result.issues, key=lambda i: ["high","medium","low"].index(i.severity.value)):
            sev_emoji  = SEVERITY_EMOJI.get(issue.severity, "⚪")
            cat_label  = CATEGORY_LABEL.get(issue.category, f"🔍 {issue.category.title()}")
            location   = f"`{issue.file}`"
            if issue.line_range:
                location += f" · {issue.line_range}"

            issues_section += (
                f"<details>\n"
                f"<summary>{sev_emoji} &nbsp;<strong>{cat_label}</strong> &nbsp;—&nbsp; {location}</summary>\n\n"
                f"**🔍 Problem**\n\n{issue.description}\n\n"
                f"**🔧 Fix**\n\n{issue.suggested_fix}\n\n"
                f"</details>\n\n"
            )

    # ── Auto-fix hint ────────────────────────────────────────────────────────
    if not passed:
        cta = (
            "### 🤖 Need Help?\n"
            "- A fix branch will be created automatically — check the next comment.\n"
            "- Ask me anything: comment `/prguard <your question>`\n"
            "- Example: `/prguard how do I fix the complexity issue in main.py?`"
        )
    else:
        cta = "💬 Questions? Comment `/prguard <your question>` and I'll answer."

    # ── Footer ───────────────────────────────────────────────────────────────
    footer = (
        f"---\n"
        f"<sub>🛡️ **PRGuard** · {len(result.issues)} issue{'s' if len(result.issues) != 1 else ''} · "
        f"Threshold {threshold}/10 · "
        f"[View Dashboard](/dashboard)</sub>"
    )

    return "\n\n".join([header, summary, issues_section, cta, footer])
