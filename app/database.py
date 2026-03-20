import json
import logging
import os
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def _conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db() -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id          SERIAL PRIMARY KEY,
                    repo        TEXT NOT NULL,
                    pr_number   INTEGER NOT NULL,
                    pr_title    TEXT,
                    score       REAL NOT NULL,
                    passed      BOOLEAN NOT NULL,
                    issues      TEXT NOT NULL,
                    fix_branch  TEXT,
                    reviewed_at TEXT NOT NULL
                )
            """)
        conn.commit()
    logger.info("PostgreSQL database initialised")


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
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reviews (repo, pr_number, pr_title, score, passed, issues, fix_branch, reviewed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    repo,
                    pr_number,
                    pr_title,
                    score,
                    passed,
                    json.dumps(issues),
                    fix_branch,
                    datetime.utcnow().isoformat(),
                ),
            )
        conn.commit()
    logger.info("Saved review for %s#%d (score=%.1f)", repo, pr_number, score)


def get_latest_review(repo: str, pr_number: int) -> dict | None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM reviews
                WHERE repo = %s AND pr_number = %s
                ORDER BY reviewed_at DESC
                LIMIT 1
                """,
                (repo, pr_number),
            )
            row = cur.fetchone()

    if not row:
        return None

    review = dict(row)
    review["issues"] = json.loads(review["issues"])
    return review


def get_stats() -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM reviews ORDER BY reviewed_at DESC")
            rows = cur.fetchall()

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
    for r in reviews:
        r["issues"] = json.loads(r["issues"])
        r["passed"] = bool(r["passed"])

    total     = len(reviews)
    passed    = sum(1 for r in reviews if r["passed"])
    avg_score = sum(r["score"] for r in reviews) / total

    score_trend = [
        {"date": r["reviewed_at"][:10], "score": r["score"], "repo": r["repo"], "pr": r["pr_number"]}
        for r in reversed(reviews[:20])
    ]

    category_counts: dict[str, int] = {}
    for r in reviews:
        for issue in r["issues"]:
            cat = issue.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

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
        "reviews": reviews[:50],
        "score_trend": score_trend,
        "category_counts": category_counts,
        "repo_stats": repo_stats,
    }
