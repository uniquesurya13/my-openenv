"""
inference.py — Baseline inference script for CodeReviewEnv
===================================
MANDATORY variables (set in environment before running):
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

Usage:
    export API_BASE_URL="https://router.huggingface.co/v1"
    export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
    export HF_TOKEN="hf_..."
    python inference.py
"""

import os
import sys
import json
import time
import requests
from typing import Optional

from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
MAX_STEPS    = 12
TEMPERATURE  = 0.1

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

TASK_IDS = ["task_easy", "task_medium", "task_hard"]


# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert code reviewer. You will be given a pull request diff to review.

Your job is to:
1. Read the diff carefully.
2. Identify issues (bugs, security vulnerabilities, style problems, logic errors).
3. Add a comment for each issue using the add_comment action.
4. Set a verdict (approve or request_changes).
5. Submit your review with a summary.

You must respond with a single JSON object representing one action. Valid action types:

1. Add a comment:
{
  "action_type": "add_comment",
  "comment": {
    "filename": "path/to/file.py",
    "line_number": 42,
    "severity": "error",
    "category": "bug",
    "message": "Description of the issue",
    "suggestion": "How to fix it"
  }
}

2. Set verdict:
{
  "action_type": "set_verdict",
  "verdict": "request_changes"
}

3. Submit review (final action):
{
  "action_type": "submit_review",
  "summary": "Overall review summary"
}

Severity levels: info, warning, error, critical
Categories for style tasks: style, formatting, naming, convention
Categories for bug tasks: bug, logic, defect
Categories for security tasks: security, vulnerability

Only output the JSON object — no markdown, no explanation.
"""


def call_llm(messages: list) -> str:
    """Call the LLM and return the response text."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def parse_action(text: str) -> Optional[dict]:
    """Parse LLM output into an action dict."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


def run_task(task_id: str) -> float:
    """Run one episode on a task and return the final score."""
    print(f"\n{'='*60}")
    print(f"Task: {task_id}")
    print(f"{'='*60}")

    # Reset environment
    resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
    if resp.status_code != 200:
        print(f"ERROR: Failed to reset env: {resp.text}")
        return 0.0

    obs = resp.json()
    print(f"PR: {obs['pr_metadata']['title']}")
    print(f"Files: {len(obs['files'])}")
    print(f"Max steps: {obs['max_steps']}")

    # Build initial context for LLM
    diff_text = ""
    for f in obs["files"]:
        diff_text += f"\n### {f['filename']} ({f['language']})\n```diff\n{f['diff']}\n```\n"

    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"TASK: {obs['task_description']}\n\n"
                f"PR: {obs['pr_metadata']['title']}\n"
                f"Author: {obs['pr_metadata']['author']}\n"
                f"Description: {obs['pr_metadata']['description']}\n\n"
                f"DIFF TO REVIEW:\n{diff_text}\n\n"
                f"Start reviewing. Add comments for each issue you find."
            ),
        },
    ]

    final_score = 0.0
    submitted = False

    for step_num in range(1, MAX_STEPS + 1):
        # Get LLM action
        llm_output = call_llm(conversation)
        print(f"\nStep {step_num}: {llm_output[:120]}...")

        action_dict = parse_action(llm_output)
        if action_dict is None:
            print("  → Could not parse action, using noop")
            action_dict = {"action_type": "noop"}

        # Force submit on last step
        if step_num == MAX_STEPS and not submitted:
            action_dict = {
                "action_type": "submit_review",
                "summary": "Review complete.",
            }

        # Step the environment
        step_resp = requests.post(f"{ENV_URL}/step", json=action_dict)
        if step_resp.status_code != 200:
            print(f"  → Step error: {step_resp.text}")
            action_dict = {"action_type": "noop"}
            step_resp = requests.post(f"{ENV_URL}/step", json=action_dict)

        result = step_resp.json()
        reward = result["reward"]
        done = result["done"]

        print(f"  reward={reward['value']:.3f}  partial={reward['partial_score']:.3f}  "
              f"feedback={reward['feedback'][:80]}")

        if action_dict.get("action_type") == "submit_review":
            final_score = reward["partial_score"]
            submitted = True

        # Update conversation with feedback
        conversation.append({"role": "assistant", "content": llm_output})
        conversation.append({
            "role": "user",
            "content": (
                f"Action result: {reward['feedback']}\n"
                f"Comments added so far: {len(result['observation']['existing_comments'])}\n"
                f"Steps remaining: {obs['max_steps'] - step_num}\n\n"
                + (
                    "Continue reviewing. Add more comments or submit when done."
                    if not done else ""
                )
            ),
        })

        if done:
            if not submitted:
                final_score = reward["partial_score"]
            break

        time.sleep(0.3)  # Rate limiting

    print(f"\n→ Final score for {task_id}: {final_score:.4f}")
    return final_score


def main():
    print("CodeReviewEnv — Baseline Inference")
    print(f"Model: {MODEL_NAME}")
    print(f"Env URL: {ENV_URL}")

    # Verify env is running
    try:
        health = requests.get(f"{ENV_URL}/health", timeout=10)
        if health.status_code != 200:
            print(f"ERROR: Environment not healthy at {ENV_URL}")
            sys.exit(1)
        print(f"Environment: {health.json()}")
    except Exception as e:
        print(f"ERROR: Cannot reach environment at {ENV_URL}: {e}")
        print("Make sure the server is running: python app.py")
        sys.exit(1)

    scores = {}
    total_start = time.time()

    for task_id in TASK_IDS:
        start = time.time()
        score = run_task(task_id)
        elapsed = time.time() - start
        scores[task_id] = {"score": score, "time_seconds": round(elapsed, 1)}

    total_elapsed = time.time() - total_start

    print("\n" + "="*60)
    print("BASELINE RESULTS")
    print("="*60)
    for task_id, result in scores.items():
        print(f"  {task_id:15s}  score={result['score']:.4f}  time={result['time_seconds']}s")

    avg = sum(r["score"] for r in scores.values()) / len(scores)
    print(f"\n  Average score: {avg:.4f}")
    print(f"  Total time:    {total_elapsed:.1f}s")

    # Save results to file
    with open("baseline_results.json", "w") as f:
        json.dump({
            "model": MODEL_NAME,
            "scores": scores,
            "average": avg,
            "total_time_seconds": round(total_elapsed, 1),
        }, f, indent=2)

    print("\nResults saved to baseline_results.json")
    return scores


if __name__ == "__main__":
    main()
