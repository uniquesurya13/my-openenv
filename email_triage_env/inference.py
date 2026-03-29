import os
import json
import jsonref
from openai import OpenAI
from typing import List, Optional, Dict
from pydantic import BaseModel
from email_env import EmailEnvironment, Action, Observation

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_STEPS = 15

tasks = [
    "task_1_easy_spam",
    "task_2_medium_categorize",
    "task_3_hard_refund"
]

def format_observation(obs: Observation) -> str:
    obs_dict = obs.model_dump()
    return json.dumps(obs_dict, indent=2)

def run_task(env: EmailEnvironment, client: OpenAI, task_id: str):
    print(f"\\n--- Running {task_id} ---")
    obs = env.reset(task_id)
    done = False
    
    # We will build a system prompt for the agent
    system_prompt = \"\"\"You are an autonomous AI Agent performing email triage.
You can move emails, mark them as read, reply to them, or switch folders.
ALWAYS return your action as a valid JSON matching the Action schema. 
Action schema:
- action_type (string): 'move', 'reply', 'mark_read', 'switch_folder'
- email_id (string, optional): ID of the email
- target_folder (string, optional): Folder to move to or switch to
- reply_text (string, optional): Text of your reply
\"\"\"
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    while not done:
        user_msg = f"Current Observation:\\n{format_observation(obs)}\\nWhat is your next action?"
        messages.append({"role": "user", "content": user_msg})
        
        # Call OpenAI with structured outputs or JSON mode
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            action_json = response.choices[0].message.content
            print(f"Agent decided: {action_json}")
            action_data = json.loads(action_json)
            action = Action(**action_data)
            
            # Record assistant msg
            messages.append({"role": "assistant", "content": action_json})
            
            obs, reward, done, info = env.step(action)
            print(f"Reward: {reward.value} - Reason: {reward.reason}")
            
        except Exception as e:
            print(f"Error during step: {e}")
            break

    # After done, run grader
    import tasks_def
    grader_func_name = task_id.replace("task_1_easy_spam", "grader_easy").replace("task_2_medium_categorize", "grader_medium").replace("task_3_hard_refund", "grader_hard")
    grader = getattr(tasks_def, grader_func_name)
    score = grader(env.state())
    print(f"Task final score: {score}")
    return score

def main():
    if not API_KEY:
        print("API_KEY or HF_TOKEN environment variable not set. Exiting.")
        return
        
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )
    
    env = EmailEnvironment()
    
    total_score = 0
    for task_id in tasks:
        score = run_task(env, client, task_id)
        total_score += score
        
    print(f"\\nTotal Evaluation Score: {total_score} / {len(tasks)}")

if __name__ == "__main__":
    main()
