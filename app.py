"""
app.py — FastAPI server exposing the OpenEnv HTTP interface.

Endpoints:
  POST /reset        → reset environment, return initial observation
  POST /step         → take an action, return StepResult
  GET  /state        → return full episode state
  GET  /tasks        → list available tasks
  GET  /health       → health check
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from models import Action, StepResult, Observation, EpisodeState
from env import CodeReviewEnv
from task_data import TASKS

app = FastAPI(
    title="CodeReviewEnv",
    description=(
        "A real-world OpenEnv environment where an AI agent acts as a code reviewer. "
        "The agent reads PR diffs and submits structured review comments."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global environment instance (one per server for simplicity) ───────────────
_env: Optional[CodeReviewEnv] = None


def get_env() -> CodeReviewEnv:
    global _env
    if _env is None:
        _env = CodeReviewEnv(task_id="task_easy")
    return _env


# ── Request models ────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_easy"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "CodeReviewEnv"}


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata."""
    return {
        "tasks": [
            {
                "task_id": tid,
                "difficulty": td["difficulty"],
                "max_steps": td["max_steps"],
                "description": td["task_description"][:200] + "...",
            }
            for tid, td in TASKS.items()
        ]
    }


@app.post("/reset", response_model=Observation)
def reset(req: ResetRequest = None):
    """
    Reset the environment to a new episode.
    Optionally specify task_id (default: task_easy).
    """
    global _env
    task_id = (req.task_id if req else None) or "task_easy"
    if task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id: {task_id}")
    _env = CodeReviewEnv(task_id=task_id)
    return _env.reset()


@app.post("/step", response_model=StepResult)
def step(action: Action):
    """
    Take one action in the environment.
    Returns observation, reward, done, info.
    """
    env = get_env()
    return env.step(action)


@app.get("/state", response_model=EpisodeState)
def state():
    """Return the full current episode state (includes ground truth)."""
    return get_env().state()


@app.get("/")
def root():
    return {
        "name": "CodeReviewEnv",
        "version": "1.0.0",
        "description": "OpenEnv-compliant code review environment",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health"],
        "tasks": list(TASKS.keys()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
