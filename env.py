"""
env.py — CodeReviewEnv: implements the OpenEnv step()/reset()/state() interface.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Optional, List
from models import (
    Observation, Action, Reward, StepResult, EpisodeState,
    ActionType, Verdict, ReviewComment, PRMetadata, FileDiff
)
from task_data import TASKS
from graders import grade_task


class CodeReviewEnv:
    """
    Real-world Code Review environment.
    The agent acts as a code reviewer, reading PR diffs and
    submitting structured review comments.
    """

    VALID_TASK_IDS = list(TASKS.keys())

    def __init__(self, task_id: str = "task_easy"):
        if task_id not in self.VALID_TASK_IDS:
            raise ValueError(f"Unknown task_id: {task_id}. Choose from {self.VALID_TASK_IDS}")
        self.task_id = task_id
        self._task_data = TASKS[task_id]
        self._reset_state()

    def _reset_state(self):
        td = self._task_data
        self._step = 0
        self._max_steps = td["max_steps"]
        self._done = False
        self._comments: List[ReviewComment] = []
        self._verdict: Optional[Verdict] = None
        self._summary: Optional[str] = None
        self._cumulative_reward = 0.0
        self._ground_truth = td["ground_truth"]
        self._last_message = "Review started. Read the diff and start adding comments."

    def reset(self) -> Observation:
        """Reset the environment and return the initial observation."""
        self._reset_state()
        return self._build_observation()

    def step(self, action: Action) -> StepResult:
        """
        Process one action and return (observation, reward, done, info).
        """
        if self._done:
            return StepResult(
                observation=self._build_observation(),
                reward=Reward(value=0.0, partial_score=0.0, breakdown={}, feedback="Episode already done."),
                done=True,
                info={"warning": "step() called after episode ended"},
            )

        self._step += 1
        reward, message = self._process_action(action)

        # Check termination conditions
        if action.action_type == ActionType.SUBMIT_REVIEW:
            self._done = True
        elif self._step >= self._max_steps:
            self._done = True
            message += " [Max steps reached — auto-submitting.]"
            # Final grade on timeout
            grade = grade_task(
                self.task_id, self._ground_truth,
                self._comments, self._verdict, self._summary,
                self._step, self._max_steps
            )
            reward = Reward(
                value=grade["score"] * 2 - 1,  # map [0,1] to [-1,1]
                partial_score=grade["score"],
                breakdown=grade["breakdown"],
                feedback=grade["feedback"],
            )

        self._cumulative_reward += reward.value
        self._last_message = message

        return StepResult(
            observation=self._build_observation(),
            reward=reward,
            done=self._done,
            info={
                "step": self._step,
                "cumulative_reward": self._cumulative_reward,
                "comments_so_far": len(self._comments),
            },
        )

    def state(self) -> EpisodeState:
        """Return the full internal state (includes ground truth)."""
        return EpisodeState(
            task_id=self.task_id,
            step_number=self._step,
            max_steps=self._max_steps,
            done=self._done,
            comments=self._comments,
            verdict=self._verdict,
            summary=self._summary,
            cumulative_reward=self._cumulative_reward,
            ground_truth=self._ground_truth,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _process_action(self, action: Action):
        """Execute an action and return (Reward, message)."""

        if action.action_type == ActionType.NOOP:
            return (
                Reward(
                    value=-0.05,
                    partial_score=self._partial_score(),
                    breakdown={"noop_penalty": -0.05},
                    feedback="No-op action. Use your steps wisely.",
                ),
                "No action taken.",
            )

        elif action.action_type == ActionType.ADD_COMMENT:
            if not action.comment:
                return (
                    Reward(
                        value=-0.1,
                        partial_score=self._partial_score(),
                        breakdown={"invalid_action": -0.1},
                        feedback="add_comment requires a 'comment' field.",
                    ),
                    "Invalid action: missing comment.",
                )

            # Duplicate comment detection
            for existing in self._comments:
                if (
                    existing.filename == action.comment.filename
                    and existing.line_number == action.comment.line_number
                    and existing.category == action.comment.category
                ):
                    return (
                        Reward(
                            value=-0.15,
                            partial_score=self._partial_score(),
                            breakdown={"duplicate_penalty": -0.15},
                            feedback="Duplicate comment detected. Penalizing.",
                        ),
                        "Duplicate comment — already commented on this location.",
                    )

            self._comments.append(action.comment)
            # Small positive signal for adding a comment
            return (
                Reward(
                    value=0.05,
                    partial_score=self._partial_score(),
                    breakdown={"comment_added": 0.05},
                    feedback=f"Comment added ({action.comment.severity}/{action.comment.category}).",
                ),
                f"Added comment on {action.comment.filename}:{action.comment.line_number}.",
            )

        elif action.action_type == ActionType.SET_VERDICT:
            if not action.verdict:
                return (
                    Reward(
                        value=-0.1,
                        partial_score=self._partial_score(),
                        breakdown={"invalid_action": -0.1},
                        feedback="set_verdict requires a 'verdict' field.",
                    ),
                    "Invalid action: missing verdict.",
                )
            self._verdict = action.verdict
            return (
                Reward(
                    value=0.02,
                    partial_score=self._partial_score(),
                    breakdown={"verdict_set": 0.02},
                    feedback=f"Verdict set to '{action.verdict.value}'.",
                ),
                f"Verdict set: {action.verdict.value}.",
            )

        elif action.action_type == ActionType.SUBMIT_REVIEW:
            self._summary = action.summary
            grade = grade_task(
                self.task_id, self._ground_truth,
                self._comments, self._verdict, self._summary,
                self._step, self._max_steps,
            )
            final_score = grade["score"]
            # Map [0,1] → [-1, 1] for reward signal
            reward_value = final_score * 2 - 1
            return (
                Reward(
                    value=round(reward_value, 4),
                    partial_score=final_score,
                    breakdown=grade["breakdown"],
                    feedback=grade["feedback"],
                ),
                f"Review submitted. Final score: {final_score:.3f}. {grade['feedback']}",
            )

        else:
            return (
                Reward(
                    value=-0.1,
                    partial_score=self._partial_score(),
                    breakdown={"unknown_action": -0.1},
                    feedback="Unknown action type.",
                ),
                "Unknown action type.",
            )

    def _partial_score(self) -> float:
        """Compute current partial score for reward shaping."""
        if not self._comments:
            return 0.0
        grade = grade_task(
            self.task_id, self._ground_truth,
            self._comments, self._verdict, self._summary,
            self._step, self._max_steps,
        )
        return grade["score"]

    def _build_observation(self) -> Observation:
        td = self._task_data
        return Observation(
            task_id=self.task_id,
            task_description=td["task_description"],
            pr_metadata=td["pr_metadata"],
            files=td["files"],
            existing_comments=list(self._comments),
            step_number=self._step,
            max_steps=self._max_steps,
            done=self._done,
            message=self._last_message,
        )
