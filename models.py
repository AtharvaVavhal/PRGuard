from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CodeIssue(BaseModel):
    file: str
    line_range: Optional[str] = None       # e.g. "L12-L18" or None if file-level
    category: str                          # e.g. "naming", "complexity", "duplication"
    severity: Severity
    description: str
    suggested_fix: str


class ReviewResult(BaseModel):
    score: float = Field(..., ge=0, le=10)
    summary: str
    issues: List[CodeIssue]
    passed: bool                           # score >= threshold


class PRContext(BaseModel):
    repo_full_name: str                    # e.g. "owner/repo"
    pr_number: int
    pr_title: str
    head_sha: str
    diff: str                              # raw unified diff text
