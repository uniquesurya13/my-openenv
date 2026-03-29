---
title: CodeReviewEnv
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - code-review
  - rl-environment
  - agent-evaluation
---

# 🔍 CodeReviewEnv

**A real-world OpenEnv environment for training and evaluating AI code review agents.**

An AI agent acts as a code reviewer: it reads pull request diffs and submits structured review comments identifying bugs, security vulnerabilities, and style issues.

---

## 🌍 Environment Description

Code review is a critical software engineering task that experienced developers perform daily. This environment models the full review loop:

1. The agent receives a pull request diff with metadata
2. The agent adds line-level comments identifying issues (severity + category + suggestion)
3. The agent sets a verdict (approve / request\_changes)
4. The agent submits the review and receives a final score

The grader compares the agent's findings against a ground-truth set of known issues, rewarding precision, severity accuracy, and helpful fix suggestions.

---

## 📋 Tasks

| Task ID       | Difficulty | Max Steps | Domain                          |
|---------------|------------|-----------|----------------------------------|
| `task_easy`   | Easy       | 10        | PEP8 style & formatting review  |
| `task_medium` | Medium     | 15        | Logic bug & defect detection    |
| `task_hard`   | Hard       | 20        | Security vulnerability review   |

### Task 1 — Style & Formatting Review (Easy)
Review a small Python file for PEP8 violations: wrong naming conventions, missing docstrings, missing context managers, unused variables, cramped imports.  
**Expected score for a good agent:** 0.70–0.85

### Task 2 — Bug Detection Review (Medium)
Review a Python API client with subtle logic bugs: 0-indexed pagination on a 1-indexed API, off-by-one in retry loop, bare except swallowing errors, division-by-zero on empty list, dict mutation.  
**Expected score for a good agent:** 0.55–0.75

### Task 3 — Security Vulnerability Review (Hard)
Review a Flask backend with 10 security vulnerabilities: SQL injection, XSS, insecure deserialization (pickle), hardcoded secrets, broken access control, session without timeout, timing attack, debug mode in production, stack trace leakage, credentials in config.  
**Expected score for a good agent:** 0.40–0.65

---

## 🎬 Action Space

```json
{
  "action_type": "add_comment | set_verdict | submit_review | noop",
  "comment": {
    "filename": "path/to/file.py",
    "line_number": 42,
    "severity": "info | warning | error | critical",
    "category": "style | bug | security | logic | performance",
    "message": "Description of the issue",
    "suggestion": "Optional suggested fix"
  },
  "verdict": "approve | request_changes | comment",
  "summary": "Overall review summary (for submit_review)"
}
```

## 👁️ Observation Space

```json
{
  "task_id": "task_easy",
  "task_description": "Natural language instructions for the agent",
  "pr_metadata": {
    "pr_id": "PR-001",
    "title": "Add user registration utility functions",
    "author": "junior_dev",
    "base_branch": "main",
    "head_branch": "feature/user-utils",
    "description": "...",
    "files_changed": 1,
    "total_additions": 42,
    "total_deletions": 0
  },
  "files": [
    {
      "filename": "user_utils.py",
      "language": "python",
      "diff": "...unified diff...",
      "added_lines": 42,
      "removed_lines": 0
    }
  ],
  "existing_comments": [...],
  "step_number": 3,
  "max_steps": 10,
  "done": false,
  "message": "Comment added (warning/style)."
}
```

---

## 🏆 Reward Function

| Signal | Value | When |
|--------|-------|------|
| Comment added | +0.05 | Each new, non-duplicate comment |
| Verdict set | +0.02 | When verdict is set |
| Duplicate comment | -0.15 | Same file+line+category seen twice |
| Noop action | -0.05 | Each no-op step |
| Invalid action | -0.10 | Malformed action |
| Final score | [-1.0, +1.0] | On submit (mapped from grader score) |

The grader provides partial scores at every step for reward shaping (not just binary end-of-episode).

---

## 🚀 Setup & Usage

### Local Development

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/code-review-env
cd code-review-env

pip install -r requirements.txt
python app.py   # starts on port 7860
```

### Docker

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### Run Inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_..."
export ENV_URL="http://localhost:7860"

python inference.py
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`      | Environment info |
| `GET`  | `/health` | Health check |
| `GET`  | `/tasks` | List all tasks |
| `POST` | `/reset` | Reset episode (`{"task_id": "task_easy"}`) |
| `POST` | `/step`  | Take action, get observation + reward |
| `GET`  | `/state` | Full episode state |

---

## 📊 Baseline Scores

Baseline agent: `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference API

| Task          | Score  |
|---------------|--------|
| task\_easy    | ~0.62  |
| task\_medium  | ~0.48  |
| task\_hard    | ~0.33  |
| **Average**   | **~0.48** |

---

## 📁 Project Structure

```
code-review-env/
├── app.py              # FastAPI server (OpenEnv HTTP API)
├── env.py              # Core environment logic (step/reset/state)
├── models.py           # Pydantic typed models (Observation/Action/Reward)
├── inference.py        # Baseline inference script
├── openenv.yaml        # OpenEnv metadata
├── requirements.txt
├── Dockerfile
├── tasks/
│   └── task_data.py    # PR scenarios + ground truth
└── graders/
    └── graders.py      # Deterministic graders for all 3 tasks
```
