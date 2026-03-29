from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    date: str
    read: bool = False
    folder: str = "Inbox"

class Observation(BaseModel):
    current_folder: str = Field(description="The folder currently being viewed")
    available_folders: List[str] = Field(description="List of available folders")
    emails: List[Dict[str, Any]] = Field(description="Emails in the current folder")
    last_action_status: str = Field(description="Status message of the last action taken")

class Action(BaseModel):
    action_type: Literal['move', 'reply', 'mark_read', 'switch_folder'] = Field(description="Action to perform: move, reply, mark_read, switch_folder")
    email_id: Optional[str] = Field(None, description="The ID of the target email")
    target_folder: Optional[str] = Field(None, description="The target folder to move an email to or switch to")
    reply_text: Optional[str] = Field(None, description="The content of the reply")

class Reward(BaseModel):
    value: float = Field(0.0, description="Reward value between 0.0 and 1.0 representing partial or full task completion")
    reason: str = Field("", description="Reason for the reward")

class EmailEnvironment:
    def __init__(self):
        self.available_folders = ["Inbox", "Technical Support", "Billing", "Refund Requests", "Spam", "Archived"]
        self.current_folder = "Inbox"
        self.emails: Dict[str, Email] = {}
        self.last_action_status = "Environment initialized."
        self.current_task_id = "task_1_easy_spam"
        self._step_count = 0
        self._max_steps = 15
        
    def _create_initial_emails(self, task_id: str):
        emails = []
        if task_id == "task_1_easy_spam":
            emails = [
                Email(id="email_1", sender="support@company.com", subject="Welcome", body="Welcome to our service!", date="2026-03-28"),
                Email(id="email_2", sender="lottery@scam.com", subject="You won!", body="Click here for 1M dollars", date="2026-03-28"),
                Email(id="email_3", sender="billing@stripe.com", subject="Your Invoice", body="Invoice attached.", date="2026-03-28"),
                Email(id="email_4", sender="prince@nigeria.com", subject="Urgent help", body="Send me money.", date="2026-03-28"),
                Email(id="email_5", sender="user@gmail.com", subject="Bug report", body="The app crashes on startup.", date="2026-03-28"),
            ]
        elif task_id == "task_2_medium_categorize":
            emails = [
                Email(id="email_1", sender="user1@mail.com", subject="Charge on my card", body="I don't recognize this charge clearly.", date="2026-03-28"),
                Email(id="email_2", sender="user2@mail.com", subject="App is slow", body="The loading screen takes 10 seconds.", date="2026-03-28"),
                Email(id="email_3", sender="scam@free-money.com", subject="Claim your prize", body="Win big today!", date="2026-03-28"),
                Email(id="email_4", sender="user4@mail.com", subject="Update billing", body="How do I change my credit card?", date="2026-03-28"),
                Email(id="email_5", sender="user5@mail.com", subject="Login failed", body="I keep getting 400 Bad Request on login.", date="2026-03-28"),
            ]
        elif task_id == "task_3_hard_refund":
            emails = [
                Email(id="email_1", sender="internal@company.com", subject="Policy Update", body="All refund requests for orders starting with 'ORD-A' are approved. Others are denied.", date="2026-03-28"),
                Email(id="email_10", sender="angry@user.com", subject="I want a refund!", body="Please refund my order ORD-A992 immediately, the product is broken.", date="2026-03-28"),
                Email(id="email_3", sender="user@gmail.com", subject="Hello", body="Just wanted to say hi.", date="2026-03-28"),
            ]
        self.emails = {e.id: e for e in emails}
        self.replies: Dict[str, str] = {}
        
    def reset(self, task_id: str = "task_1_easy_spam") -> Observation:
        self.current_task_id = task_id
        self._create_initial_emails(task_id)
        self.current_folder = "Inbox"
        self.last_action_status = f"Environment reset for task: {task_id}"
        self._step_count = 0
        return self._get_observation()
        
    def _get_observation(self) -> Observation:
        folder_emails = [
            e.model_dump() for e in self.emails.values() if e.folder == self.current_folder
        ]
        return Observation(
            current_folder=self.current_folder,
            available_folders=self.available_folders,
            emails=folder_emails,
            last_action_status=self.last_action_status
        )
        
    def state(self) -> Dict[str, Any]:
        return {
            "current_folder": self.current_folder,
            "emails": {k: v.model_dump() for k, v in self.emails.items()},
            "replies": self.replies,
            "step_count": self._step_count
        }
        
    def step(self, action: Action) -> tuple[Observation, Reward, bool, Dict[str, Any]]:
        self._step_count += 1
        reward_val = 0.0
        reward_reason = ""
        done = False
        
        status = "Invalid action."
        if action.action_type == 'switch_folder':
            if action.target_folder in self.available_folders:
                self.current_folder = action.target_folder
                status = f"Switched to folder: {self.current_folder}"
                reward_val = 0.01  # small reward for exploring
                reward_reason = "Explored folders"
            else:
                status = f"Folder '{action.target_folder}' does not exist."
                reward_val = -0.05
                reward_reason = "Invalid folder"
                
        elif action.action_type == 'mark_read':
            if action.email_id in self.emails:
                if self.emails[action.email_id].folder == self.current_folder:
                    self.emails[action.email_id].read = True
                    status = f"Email {action.email_id} marked as read."
                    reward_val = 0.05
                    reward_reason = "Read an email"
                else:
                    status = f"Email {action.email_id} is not in the current folder."
            else:
                status = f"Email {action.email_id} not found."
                
        elif action.action_type == 'move':
            if action.email_id in self.emails and action.target_folder in self.available_folders:
                if self.emails[action.email_id].folder == self.current_folder:
                    self.emails[action.email_id].folder = action.target_folder
                    status = f"Moved {action.email_id} to {action.target_folder}."
                    
                    # Partial reward logic for moving correct emails
                    if self.current_task_id == "task_1_easy_spam" and action.target_folder == "Spam":
                        if action.email_id in ["email_2", "email_4"]:
                            reward_val = 0.4
                            reward_reason = "Correctly identified spam"
                        else:
                            reward_val = -0.2
                            reward_reason = "Moved non-spam to spam"
                            
                    elif self.current_task_id == "task_2_medium_categorize":
                        correct_mapping = {
                            "email_1": "Billing", "email_2": "Technical Support",
                            "email_3": "Spam", "email_4": "Billing", "email_5": "Technical Support"
                        }
                        if correct_mapping.get(action.email_id) == action.target_folder:
                            reward_val = 0.2
                            reward_reason = "Correctly categorized email"
                        else:
                            reward_val = -0.1
                            reward_reason = "Incorrect categorization"
                            
                    elif self.current_task_id == "task_3_hard_refund":
                        if action.email_id == "email_10" and action.target_folder == "Refund Requests":
                            reward_val = 0.3
                            reward_reason = "Moved refund request correctly"
                else:
                    status = f"Email {action.email_id} is not in the current folder."
            else:
                status = "Invalid email ID or target folder for move."
                
        elif action.action_type == 'reply':
            if action.email_id in self.emails:
                self.replies[action.email_id] = action.reply_text or ""
                status = f"Replied to {action.email_id}."
                if self.current_task_id == "task_3_hard_refund" and action.email_id == "email_10":
                    if "ORD-A992" in str(action.reply_text):
                        reward_val = 0.5
                        reward_reason = "Sent reply with correct order number"
                    else:
                        reward_val = 0.1
                        reward_reason = "Replied, but missing order number"
            else:
                status = f"Email {action.email_id} not found."
                
        self.last_action_status = status
        
        # Check termination condition
        if self._step_count >= self._max_steps:
            done = True
            
        reward = Reward(value=reward_val, reason=reward_reason)
        info = {"step_count": self._step_count}
        
        return self._get_observation(), reward, done, info
