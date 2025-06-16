import os
import json
import base64
import random
import datetime
from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "fujikongu/fx-pro-strategy-bot"
BRANCH = "main"
FILE_PATH = "passwords.json"

# HTMLテンプレート読み込み
with open("issue_password_template.html", encoding="utf-8") as f:
    HTML_FORM = f.read()

def generate_password():
    return f"mem{random.randint(1, 9999):04d}"

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        decoded = base64.b64decode(content["content"]).decode("utf-8")
        sha = content["sha"]
        return json.loads(decoded), sha
    else:
        return [], None

def update_passwords_on_github(passwords, sha=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    new_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Add new password",
        "content": new_content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
    res = requests.put(url, headers=headers, json=data)
    return res.status_code in [200, 201]

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        password = generate_password()
        today = datetime.date.today().isoformat()
        passwords, sha = get_existing_passwords()
        passwords.append({
            "password": password,
            "used": False,
            "issued": today
        })
        success = update_passwords_on_github(passwords, sha)
        if not success:
            password = None  # 表示しない
    return render_template_string(HTML_FORM, password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)