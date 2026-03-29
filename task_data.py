"""
tasks/task_data.py — The three PR scenarios used in the environment.
Each task includes: PR metadata, file diffs, and ground truth issues for grading.
"""

from models import PRMetadata, FileDiff, ReviewComment, Severity

# ─── TASK 1: EASY — Style & Formatting ───────────────────────────────────────

TASK_EASY = {
    "task_id": "task_easy",
    "difficulty": "easy",
    "max_steps": 10,
    "task_description": (
        "Review this Python pull request for PEP8 style violations, naming convention issues, "
        "missing docstrings, and basic formatting problems. "
        "Add a comment for each issue you find with severity 'info' or 'warning'. "
        "When done, submit your review with verdict 'request_changes' if issues exist, "
        "or 'approve' if the code is clean."
    ),
    "pr_metadata": PRMetadata(
        pr_id="PR-001",
        title="Add user registration utility functions",
        author="junior_dev",
        base_branch="main",
        head_branch="feature/user-utils",
        description="Adds helper functions for user registration flow.",
        files_changed=1,
        total_additions=42,
        total_deletions=0,
    ),
    "files": [
        FileDiff(
            filename="user_utils.py",
            language="python",
            added_lines=42,
            removed_lines=0,
            diff='''\
+import os, sys, json
+from datetime import datetime
+
+def ValidateEmail(e):
+    if "@" in e and "." in e:
+        return True
+    else:
+        return False
+
+def createUser(USERNAME,PASSWORD,Email):
+    u = {}
+    u["username"] = USERNAME
+    u["password"] = PASSWORD
+    u["email"] = Email
+    u["created_at"] = datetime.now()
+    u["active"]=True
+    return u
+
+def Save_User_To_File(user,filepath):
+    f=open(filepath,"w")
+    json.dump(user,f)
+    f.close()
+
+def loadUser(fp):
+    f = open(fp)
+    data=json.load(f)
+    f.close
+    return data
+
+x = 10  # unused variable
+l = [1,2,3,4,5]
''',
        )
    ],
    # Ground truth: what issues SHOULD be found
    "ground_truth": {
        "required_categories": ["style"],
        "expected_issue_count": 8,
        "key_issues": [
            {"line_hint": 1, "keyword": "import", "desc": "multiple imports on one line"},
            {"line_hint": 4, "keyword": "ValidateEmail", "desc": "function name should be snake_case (validate_email)"},
            {"line_hint": 4, "keyword": "docstring", "desc": "missing docstring"},
            {"line_hint": 10, "keyword": "createUser", "desc": "function name should be snake_case (create_user)"},
            {"line_hint": 10, "keyword": "USERNAME", "desc": "parameter names should be lowercase"},
            {"line_hint": 17, "keyword": "active", "desc": "missing space around assignment"},
            {"line_hint": 21, "keyword": "Save_User_To_File", "desc": "mixed case function name"},
            {"line_hint": 23, "keyword": "open", "desc": "file not opened with context manager (with statement)"},
            {"line_hint": 28, "keyword": "f.close", "desc": "f.close not called (missing parentheses)"},
            {"line_hint": 33, "keyword": "unused", "desc": "unused variable x"},
        ],
        "correct_verdict": "request_changes",
    },
}

# ─── TASK 2: MEDIUM — Bug Detection ──────────────────────────────────────────

TASK_MEDIUM = {
    "task_id": "task_medium",
    "difficulty": "medium",
    "max_steps": 15,
    "task_description": (
        "Review this Python module for logic bugs, off-by-one errors, incorrect exception handling, "
        "and other functional defects. This code will be deployed to production — find all bugs. "
        "Add a comment with severity 'error' for each bug. "
        "Submit with verdict 'request_changes'."
    ),
    "pr_metadata": PRMetadata(
        pr_id="PR-042",
        title="Implement paginator and retry logic for API client",
        author="mid_dev",
        base_branch="main",
        head_branch="feature/api-client-v2",
        description="Adds pagination support and retry logic to the internal API client.",
        files_changed=1,
        total_additions=68,
        total_deletions=12,
    ),
    "files": [
        FileDiff(
            filename="api_client.py",
            language="python",
            added_lines=68,
            removed_lines=12,
            diff='''\
+import time
+import requests
+
+MAX_RETRIES = 3
+PAGE_SIZE = 100
+
+def get_all_records(base_url, endpoint, auth_token):
+    """Fetch all paginated records from the API."""
+    records = []
+    page = 0  # BUG: API pages are 1-indexed
+    
+    while True:
+        url = f"{base_url}/{endpoint}?page={page}&size={PAGE_SIZE}"
+        response = requests.get(url, headers={"Authorization": auth_token})
+        data = response.json()
+        
+        records.extend(data["items"])
+        
+        if len(data["items"]) < PAGE_SIZE:
+            break
+        page += 1
+    
+    return records
+
+
+def retry_request(url, max_retries=MAX_RETRIES):
+    """Make a request with exponential backoff retry."""
+    for attempt in range(max_retries):
+        try:
+            response = requests.get(url)
+            response.raise_for_status()
+            return response
+        except requests.HTTPError as e:
+            if attempt == max_retries:  # BUG: should be max_retries - 1
+                raise
+            wait = 2 ** attempt
+            time.sleep(wait)
+        except Exception:  # BUG: swallows all exceptions silently
+            pass
+
+
+def calculate_average(values):
+    """Return the average of a list of numbers."""
+    total = 0
+    for v in values:
+        total += v
+    return total / len(values)  # BUG: ZeroDivisionError if values is empty
+
+
+def find_duplicates(items):
+    """Return list of duplicate items."""
+    seen = []
+    duplicates = []
+    for item in items:
+        if item in seen:
+            duplicates.append(item)
+        seen.append(item)  # BUG: should append before the check, or use set
+    return list(set(duplicates))
+
+
+def merge_configs(default, override):
+    """Merge two config dicts; override takes precedence."""
+    result = default  # BUG: mutates default dict (should be default.copy())
+    result.update(override)
+    return result
+''',
        )
    ],
    "ground_truth": {
        "required_categories": ["bug", "logic"],
        "expected_issue_count": 5,
        "key_issues": [
            {"line_hint": 9,  "keyword": "page",        "desc": "page starts at 0 but API is 1-indexed"},
            {"line_hint": 33, "keyword": "max_retries", "desc": "off-by-one: should be max_retries-1"},
            {"line_hint": 37, "keyword": "Exception",   "desc": "bare except swallows all exceptions"},
            {"line_hint": 44, "keyword": "ZeroDivision","desc": "division by zero when values is empty"},
            {"line_hint": 58, "keyword": "default",     "desc": "mutates default dict instead of copying"},
        ],
        "correct_verdict": "request_changes",
    },
}

# ─── TASK 3: HARD — Security Vulnerability Review ────────────────────────────

TASK_HARD = {
    "task_id": "task_hard",
    "difficulty": "hard",
    "max_steps": 20,
    "task_description": (
        "Review this Flask web application backend for security vulnerabilities. "
        "This is a critical security review — the app handles user authentication and "
        "database queries. Find ALL security vulnerabilities including: SQL injection, "
        "XSS, insecure deserialization, broken authentication, secrets in code, "
        "missing rate limiting, improper error handling. "
        "Mark each with severity 'critical' or 'error' and the category 'security'. "
        "Provide a suggested fix for each issue. Submit with verdict 'request_changes'."
    ),
    "pr_metadata": PRMetadata(
        pr_id="PR-099",
        title="New Flask backend: auth + user search endpoints",
        author="backend_lead",
        base_branch="main",
        head_branch="feature/flask-backend",
        description=(
            "Implements user login, session management, and a search endpoint. "
            "Ready for production deployment."
        ),
        files_changed=2,
        total_additions=95,
        total_deletions=0,
    ),
    "files": [
        FileDiff(
            filename="app.py",
            language="python",
            added_lines=60,
            removed_lines=0,
            diff='''\
+from flask import Flask, request, session, jsonify
+import sqlite3
+import pickle
+import os
+
+app = Flask(__name__)
+app.secret_key = "supersecret123"  # VULN: hardcoded secret key
+
+DB_PATH = "users.db"
+
+def get_db():
+    return sqlite3.connect(DB_PATH)
+
+@app.route("/login", methods=["POST"])
+def login():
+    username = request.form.get("username")
+    password = request.form.get("password")
+    
+    db = get_db()
+    # VULN: SQL injection
+    query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"
+    cursor = db.execute(query)
+    user = cursor.fetchone()
+    
+    if user:
+        session["user"] = username
+        session.permanent = True  # VULN: no session timeout configured
+        return jsonify({"status": "ok", "user": username})
+    
+    # VULN: timing attack — different code paths for wrong user vs wrong password
+    cursor2 = db.execute(f"SELECT id FROM users WHERE username=\'{username}\'")
+    if cursor2.fetchone():
+        return jsonify({"error": "Wrong password"}), 401
+    return jsonify({"error": "User not found"}), 401
+
+@app.route("/search")
+def search():
+    q = request.args.get("q", "")
+    # VULN: XSS — user input reflected without escaping
+    return f"<html><body>Results for: {q}</body></html>"
+
+@app.route("/load_profile", methods=["POST"])
+def load_profile():
+    # VULN: insecure deserialization
+    data = request.get_data()
+    profile = pickle.loads(data)
+    return jsonify(profile)
+
+@app.route("/admin")
+def admin():
+    # VULN: broken access control — no auth check
+    db = get_db()
+    users = db.execute("SELECT * FROM users").fetchall()
+    return jsonify(users)
+
+@app.errorhandler(Exception)
+def handle_error(e):
+    # VULN: leaks stack trace to client
+    return jsonify({"error": str(e), "trace": str(e.__traceback__)}), 500
+
+if __name__ == "__main__":
+    app.run(debug=True)  # VULN: debug mode enabled in production
''',
        ),
        FileDiff(
            filename="config.py",
            language="python",
            added_lines=15,
            removed_lines=0,
            diff='''\
+# VULN: credentials hardcoded in source
+DATABASE_URL = "postgresql://admin:Password123@prod-db.internal:5432/users"
+ADMIN_PASSWORD = "admin123"
+AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
+SMTP_PASSWORD = "mailpassword99"
+
+# No rate limiting configured
+# No CSRF protection
+# No Content Security Policy headers
''',
        ),
    ],
    "ground_truth": {
        "required_categories": ["security"],
        "expected_issue_count": 10,
        "key_issues": [
            {"line_hint": 7,  "keyword": "secret_key",      "desc": "hardcoded Flask secret key"},
            {"line_hint": 20, "keyword": "SQL injection",    "desc": "f-string SQL query — SQL injection"},
            {"line_hint": 25, "keyword": "session",          "desc": "no session timeout"},
            {"line_hint": 31, "keyword": "timing",           "desc": "timing attack on login"},
            {"line_hint": 37, "keyword": "XSS",              "desc": "reflected XSS in search endpoint"},
            {"line_hint": 42, "keyword": "pickle",           "desc": "insecure deserialization via pickle"},
            {"line_hint": 47, "keyword": "admin",            "desc": "broken access control on /admin"},
            {"line_hint": 52, "keyword": "traceback",        "desc": "stack trace leaked to client"},
            {"line_hint": 56, "keyword": "debug",            "desc": "debug=True in production"},
            {"line_hint": 2,  "keyword": "credentials",      "desc": "hardcoded credentials in config.py"},
        ],
        "correct_verdict": "request_changes",
    },
}

TASKS = {
    "task_easy": TASK_EASY,
    "task_medium": TASK_MEDIUM,
    "task_hard": TASK_HARD,
}
