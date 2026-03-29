# OpenEnv: Email Triage

This environment simulates a real-world email triage and support inbox. The AI agent must read through customer emails, move them to the correct categorical folders, mark items as read, and reply to specific high-priority inquiries (such as refund requests).

## Observation Space
The agent receives:
- `current_folder`: The folder currently being viewed.
- `available_folders`: A list of folders the agent can switch to or move emails to.
- `emails`: A list of emails in the current folder, containing subject, sender, full body, reading status, and ID.
- `last_action_status`: Human-readable feedback regarding the success of the last action.

## Action Space
`action_type`: Literal['move', 'reply', 'mark_read', 'switch_folder']
- `email_id` (optional): The ID of the target email.
- `target_folder` (optional): The target folder to move an email to or switch view to.
- `reply_text` (optional): The content of the reply to an email.

## Tasks and Difficulty
1. **Move specific spam emails (Easy)**: The agent must move 2 distinct spam emails from the Inbox to the Spam folder.
2. **Categorize emails (Medium)**: The agent reads 5 emails and categorizes them correctly into Billing, Technical Support, and Spam.
3. **Refund Requests (Hard)**: The agent searches for a refund request, verifies policy status from another email, moves the refund to "Refunds" folder, and replies with the extracted order number and disposition.

## Setup Instructions

1. Clone the repository natively or build the docker container:
   ```bash
   docker build -t email-env .
   docker run -p 7860:7860 email-env
   ```
2. For local testing, ensure you have Python 3.11+. Create a virtualenv:
   ```bash
   pip install -r requirements.txt
   openenv validate
   ```

## Baseline Run
A baseline script `inference.py` is provided to benchmark an autonomous agent using the OpenAI API spec.
Run it using your preferred endpoint (default points to HuggingFace serverless inference if configured or standard API host).

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-api-key"
python inference.py
```
*Expected baseline score with gpt-4o-mini: 3.0 / 3.0*
