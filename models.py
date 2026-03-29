"""
models.py — Typed Pydantic models for CodeReviewEnv
Implements the OpenEnv spec: Observation, Action, Reward
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Verdict(str, Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


class ActionType(str, Enum):
    ADD_COMMENT = "add_comment"
    SET_VERDICT = "set_verdict"
    SUBMIT_REVIEW = "submit_review"
    NOOP = "noop"


# ─── Sub-models ──────────────────────────────────────────────────────────────

class FileDiff(BaseModel):
    filename: str = Field(..., description="Name of the file being reviewed")
    language: str = Field(..., description="Programming language")
    diff: str = Field(..., description="Unified diff of the file changes")
    added_lines: int = Field(0, description="Number of lines added")
    removed_lines: int = Field(0, description="Number of lines removed")


class ReviewComment(BaseModel):
    filename: str = Field(..., description="File the comment applies to")
    line_number: Optional[int] = Field(None, description="Line number (None = general comment)")
    severity: Severity = Field(..., description="Severity level of the issue")
    category: str = Field(..., description="Category: style/bug/security/logic/performance")
    message: str = Field(..., description="The review comment text")
    suggestion: Optional[str] = Field(None, description="Optional suggested fix")


class PRMetadata(BaseModel):
    pr_id: str
    title: str
    author: str
    base_branch: str
    head_branch: str
    description: str
    files_changed: int
    total_additions: int
    total_deletions: int


# ─── Core OpenEnv Models ──────────────────────────────────────────────────────

class Observation(BaseModel):
    """What the agent sees at each step."""
    task_id: str = Field(..., description="Current task identifier")
    task_description: str = Field(..., description="Natural language task instructions")
    pr_metadata: PRMetadata = Field(..., description="Pull request metadata")
    files: List[FileDiff] = Field(..., description="List of file diffs to review")
    existing_comments: List[ReviewComment] = Field(
        default_factory=list,
        description="Comments the agent has already added this episode"
    )
    step_number: int = Field(0, description="Current step in the episode")
    max_steps: int = Field(20, description="Maximum steps allowed")
    done: bool = Field(False, description="Whether the episode is complete")
    message: str = Field("", description="System message or feedback from last action")


class Action(BaseModel):
    """What the agent does at each step."""
    action_type: ActionType = Field(..., description="Type of action to perform")
    comment: Optional[ReviewComment] = Field(
        None,
        description="Comment to add (required for add_comment action)"
    )
    verdict: Optional[Verdict] = Field(
        None,
        description="Overall verdict (required for set_verdict action)"
    )
    summary: Optional[str] = Field(
        None,
        description="Overall review summary (used with submit_review)"
    )


class Reward(BaseModel):
    """Reward signal returned after each step."""
    value: float = Field(..., ge=-1.0, le=1.0, description="Reward value in [-1, 1]")
    partial_score: float = Field(..., ge=0.0, le=1.0, description="Progress toward task completion")
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-component reward breakdown"
    )
    feedback: str = Field("", description="Human-readable feedback on the action")


class StepResult(BaseModel):
    """Full result of a step() call."""
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class EpisodeState(BaseModel):
    """Full internal state — returned by state()."""
    task_id: str
    step_number: int
    max_steps: int
    done: bool
    comments: List[ReviewComment]
    verdict: Optional[Verdict]
    summary: Optional[str]
    cumulative_reward: float
    ground_truth: Dict[str, Any]  # hidden from agent in production
