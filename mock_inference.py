import requests
import json
import time
import sys

ENV_URL = "http://localhost:7860"
TASK_IDS = ["task_easy", "task_medium", "task_hard"]

def main():
    print("Mock Inference (No LLM API Key required)")
    try:
        requests.get(f"{ENV_URL}/health", timeout=5)
    except:
        print("Server not running. Run 'python app.py' first.")
        sys.exit(1)

    for task_id in TASK_IDS:
        print(f"\\n{'='*40}\\nhardcoded Test: {task_id}\\n{'='*40}")
        resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
        obs = resp.json()
        print(f"PR: {obs['pr_metadata']['title']}")
        
        # 1. Add a dummy comment
        action_1 = {
            "action_type": "add_comment",
            "comment": {
                "filename": obs["files"][0]["filename"],
                "line_number": 1,
                "severity": "warning",
                "category": "style",
                "message": "Mock comment for testing",
                "suggestion": "Fix this"
            }
        }
        resp1 = requests.post(f"{ENV_URL}/step", json=action_1).json()
        print(f"Added comment. Partial Score: {resp1['reward']['partial_score']}")

        # 2. Set verdict
        action_2 = {"action_type": "set_verdict", "verdict": "request_changes"}
        resp2 = requests.post(f"{ENV_URL}/step", json=action_2).json()
        print(f"Set verdict. Partial Score: {resp2['reward']['partial_score']}")

        # 3. Submit
        action_3 = {"action_type": "submit_review", "summary": "LGTM!"}
        resp3 = requests.post(f"{ENV_URL}/step", json=action_3).json()
        
        print(f"Submitted. Final Score: {resp3['reward']['partial_score']}\\nFeedback: {resp3['reward']['feedback']}")

if __name__ == "__main__":
    main()
