from email_env import EmailEnvironment

def grader_easy(env_state: dict) -> float:
    \"\"\"
    Check if email_2 and email_4 are in the Spam folder.
    Max score: 1.0 (0.5 for each correct)
    \"\"\"
    score = 0.0
    emails = env_state.get("emails", {})
    if emails.get("email_2", {}).get("folder") == "Spam":
        score += 0.5
    if emails.get("email_4", {}).get("folder") == "Spam":
        score += 0.5
    return score

def grader_medium(env_state: dict) -> float:
    \"\"\"
    Check correct categorization of 5 emails.
    Max score: 1.0 (0.2 for each correct)
    \"\"\"
    correct_mapping = {
        "email_1": "Billing",
        "email_2": "Technical Support",
        "email_3": "Spam",
        "email_4": "Billing",
        "email_5": "Technical Support"
    }
    score = 0.0
    emails = env_state.get("emails", {})
    for e_id, target in correct_mapping.items():
        if emails.get(e_id, {}).get("folder") == target:
            score += 0.2
    return score

def grader_hard(env_state: dict) -> float:
    \"\"\"
    Check if email_10 is in 'Refund Requests', and a reply was sent mentioning 'ORD-A992' and 'approved'.
    Max score: 1.0
    \"\"\"
    score = 0.0
    emails = env_state.get("emails", {})
    replies = env_state.get("replies", {})
    
    if emails.get("email_10", {}).get("folder") == "Refund Requests":
        score += 0.3
        
    reply_text = replies.get("email_10", "").lower()
    if reply_text:
        score += 0.3
        if "ord-a992" in reply_text:
            score += 0.2
        if "approv" in reply_text:  # matches approve, approved
            score += 0.2
            
    return score
