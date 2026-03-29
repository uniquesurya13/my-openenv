"""
graders/graders.py — Deterministic graders for all three tasks.
Each grader takes the agent's comments + verdict and returns a score in [0.0, 1.0].
"""

from typing import List, Optional, Dict, Any
from models import ReviewComment, Verdict, Severity


def _comment_matches_issue(comment: ReviewComment, issue: Dict[str, Any]) -> bool:
    """
    Check if a comment covers a known ground-truth issue.
    Uses keyword matching against message + suggestion text.
    """
    text = (comment.message + " " + (comment.suggestion or "")).lower()
    keyword = issue["keyword"].lower()
    # Accept if any significant word from the keyword appears in the comment
    keywords = keyword.replace("/", " ").replace("-", " ").split()
    return any(kw in text for kw in keywords if len(kw) > 3)


def grade_task(
    task_id: str,
    ground_truth: Dict[str, Any],
    comments: List[ReviewComment],
    verdict: Optional[Verdict],
    summary: Optional[str],
    step_number: int,
    max_steps: int,
) -> Dict[str, Any]:
    """
    Master grader dispatcher. Returns:
    {
        "score": float [0.0–1.0],
        "breakdown": dict,
        "feedback": str
    }
    """
    if task_id == "task_easy":
        return _grade_style(ground_truth, comments, verdict, step_number, max_steps)
    elif task_id == "task_medium":
        return _grade_bugs(ground_truth, comments, verdict, step_number, max_steps)
    elif task_id == "task_hard":
        return _grade_security(ground_truth, comments, verdict, step_number, max_steps)
    else:
        return {"score": 0.0, "breakdown": {}, "feedback": "Unknown task."}


# ─── TASK 1 GRADER: Style Review ─────────────────────────────────────────────

def _grade_style(
    ground_truth: Dict,
    comments: List[ReviewComment],
    verdict: Optional[Verdict],
    step_number: int,
    max_steps: int,
) -> Dict:
    key_issues = ground_truth["key_issues"]
    correct_verdict = ground_truth["correct_verdict"]
    n_expected = ground_truth["expected_issue_count"]

    # 1. Issue detection score (60%)
    found = 0
    matched_indices = set()
    for comment in comments:
        # Only count style/info/warning comments
        if comment.category not in ("style", "formatting", "naming", "convention"):
            continue
        for i, issue in enumerate(key_issues):
            if i not in matched_indices and _comment_matches_issue(comment, issue):
                found += 1
                matched_indices.add(i)
                break

    detection_score = min(found / max(n_expected, 1), 1.0)

    # 2. Severity appropriateness (20%) — style issues should NOT be marked critical/error
    severity_ok = sum(
        1 for c in comments
        if c.severity in (Severity.INFO, Severity.WARNING)
    )
    total_comments = max(len(comments), 1)
    severity_score = severity_ok / total_comments

    # 3. Verdict correctness (20%)
    verdict_score = 1.0 if verdict and verdict.value == correct_verdict else 0.0

    # 4. Efficiency bonus/penalty: penalize using too many steps for an easy task
    step_efficiency = max(0.0, 1.0 - (step_number / max_steps) * 0.3)

    score = (
        0.60 * detection_score
        + 0.20 * severity_score
        + 0.20 * verdict_score
    ) * step_efficiency

    feedback_parts = [
        f"Found {found}/{n_expected} style issues.",
        f"Severity usage: {severity_ok}/{total_comments} appropriately rated.",
        f"Verdict: {'correct' if verdict_score else 'incorrect'} (expected {correct_verdict}).",
    ]

    return {
        "score": round(min(score, 1.0), 4),
        "breakdown": {
            "issue_detection": round(detection_score, 4),
            "severity_appropriateness": round(severity_score, 4),
            "verdict": verdict_score,
            "step_efficiency": round(step_efficiency, 4),
        },
        "feedback": " ".join(feedback_parts),
    }


# ─── TASK 2 GRADER: Bug Detection ────────────────────────────────────────────

def _grade_bugs(
    ground_truth: Dict,
    comments: List[ReviewComment],
    verdict: Optional[Verdict],
    step_number: int,
    max_steps: int,
) -> Dict:
    key_issues = ground_truth["key_issues"]
    correct_verdict = ground_truth["correct_verdict"]
    n_expected = ground_truth["expected_issue_count"]

    # 1. Bug detection (70%) — must use "bug" or "logic" category, error severity
    found = 0
    matched_indices = set()
    for comment in comments:
        if comment.category not in ("bug", "logic", "error", "defect"):
            continue
        for i, issue in enumerate(key_issues):
            if i not in matched_indices and _comment_matches_issue(comment, issue):
                found += 1
                matched_indices.add(i)
                break

    detection_score = min(found / max(n_expected, 1), 1.0)

    # 2. Severity correctness (15%) — bugs should be error or critical
    severity_ok = sum(
        1 for c in comments
        if c.severity in (Severity.ERROR, Severity.CRITICAL)
    )
    total_comments = max(len(comments), 1)
    severity_score = severity_ok / total_comments

    # 3. Verdict correctness (15%)
    verdict_score = 1.0 if verdict and verdict.value == correct_verdict else 0.0

    score = (
        0.70 * detection_score
        + 0.15 * severity_score
        + 0.15 * verdict_score
    )

    feedback_parts = [
        f"Detected {found}/{n_expected} bugs.",
        f"High-severity ratings: {severity_ok}/{total_comments}.",
        f"Verdict: {'correct' if verdict_score else 'incorrect'}.",
    ]

    return {
        "score": round(min(score, 1.0), 4),
        "breakdown": {
            "bug_detection": round(detection_score, 4),
            "severity_correctness": round(severity_score, 4),
            "verdict": verdict_score,
        },
        "feedback": " ".join(feedback_parts),
    }


# ─── TASK 3 GRADER: Security Review ──────────────────────────────────────────

def _grade_security(
    ground_truth: Dict,
    comments: List[ReviewComment],
    verdict: Optional[Verdict],
    step_number: int,
    max_steps: int,
) -> Dict:
    key_issues = ground_truth["key_issues"]
    correct_verdict = ground_truth["correct_verdict"]
    n_expected = ground_truth["expected_issue_count"]

    # 1. Vulnerability detection (65%)
    found = 0
    matched_indices = set()
    for comment in comments:
        if comment.category not in ("security", "vulnerability", "vuln"):
            continue
        for i, issue in enumerate(key_issues):
            if i not in matched_indices and _comment_matches_issue(comment, issue):
                found += 1
                matched_indices.add(i)
                break

    detection_score = min(found / max(n_expected, 1), 1.0)

    # 2. Severity correctness (15%) — security issues must be critical or error
    severity_ok = sum(
        1 for c in comments
        if c.severity in (Severity.CRITICAL, Severity.ERROR)
    )
    total_comments = max(len(comments), 1)
    severity_score = severity_ok / total_comments

    # 3. Fix suggestions provided (10%) — security review requires fixes
    with_suggestion = sum(
        1 for c in comments
        if c.suggestion and len(c.suggestion) > 10
    )
    suggestion_score = min(with_suggestion / max(n_expected, 1), 1.0)

    # 4. Verdict correctness (10%)
    verdict_score = 1.0 if verdict and verdict.value == correct_verdict else 0.0

    score = (
        0.65 * detection_score
        + 0.15 * severity_score
        + 0.10 * suggestion_score
        + 0.10 * verdict_score
    )

    feedback_parts = [
        f"Found {found}/{n_expected} security vulnerabilities.",
        f"Critical/error severity: {severity_ok}/{total_comments}.",
        f"Fixes suggested: {with_suggestion}/{n_expected}.",
        f"Verdict: {'correct' if verdict_score else 'incorrect'}.",
    ]

    return {
        "score": round(min(score, 1.0), 4),
        "breakdown": {
            "vulnerability_detection": round(detection_score, 4),
            "severity_correctness": round(severity_score, 4),
            "fix_suggestions": round(suggestion_score, 4),
            "verdict": verdict_score,
        },
        "feedback": " ".join(feedback_parts),
    }
