import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("prguard.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                repo        TEXT NOT NULL,
                pr_number   INTEGER NOT NULL,
                pr_title    TEXT,
                score       REAL NOT NULL,
                passed      INTEGER NOT NULL,
                issues      TEXT NOT NULL,   -- JSON array
                fix_branch  TEXT,
                reviewed_at TEXT NOT NULL
            )
        """)
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


def save_review(
    repo: str,
    pr_number: int,
    pr_title: str,
    score: float,
    passed: bool,
    issues: list[dict],
    fix_branch: str | None = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO reviews (repo, pr_number, pr_title, score, passed, issues, fix_branch, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo,
                pr_number,
                pr_title,
                score,
                int(passed),
                json.dumps(issues),
                fix_branch,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    logger.info("Saved review for %s#%d (score=%.1f)", repo, pr_number, score)


def get_stats() -> dict:
    with _conn() as conn:
        # All reviews ordered by time
        rows = conn.execute(
            "SELECT * FROM reviews ORDER BY reviewed_at DESC"
        ).fetchall()

    if not rows:
        return {
            "total": 0,
            "pass_rate": 0,
            "avg_score": 0,
            "reviews": [],
            "score_trend": [],
            "category_counts": {},
            "repo_stats": {},
        }

    reviews = [dict(r) for r in rows]

    # Parse issues JSON
    for r in reviews:
        r["issues"] = json.loads(r["issues"])

    total = len(reviews)
    passed = sum(1 for r in reviews if r["passed"])
    avg_score = sum(r["score"] for r in reviews) / total

    # Score trend (last 20 reviews, oldest first)
    score_trend = [
        {"date": r["reviewed_at"][:10], "score": r["score"], "repo": r["repo"], "pr": r["pr_number"]}
        for r in reversed(reviews[:20])
    ]

    # Issue category counts across all reviews
    category_counts: dict[str, int] = {}
    for r in reviews:
        for issue in r["issues"]:
            cat = issue.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # Per-repo stats
    repo_stats: dict[str, dict] = {}
    for r in reviews:
        repo = r["repo"]
        if repo not in repo_stats:
            repo_stats[repo] = {"total": 0, "passed": 0, "scores": []}
        repo_stats[repo]["total"] += 1
        repo_stats[repo]["passed"] += int(r["passed"])
        repo_stats[repo]["scores"].append(r["score"])

    for repo, stats in repo_stats.items():
        stats["avg_score"] = round(sum(stats["scores"]) / len(stats["scores"]), 1)
        stats["pass_rate"] = round(stats["passed"] / stats["total"] * 100)
        del stats["scores"]

    return {
        "total": total,
        "pass_rate": round(passed / total * 100),
        "avg_score": round(avg_score, 1),
        "reviews": reviews[:50],  # latest 50 for table
        "score_trend": score_trend,
        "category_counts": category_counts,
        "repo_stats": repo_stats,
    }
