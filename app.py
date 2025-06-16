
import os
import json
import random
import string
from datetime import datetime
from flask import Flask, request, render_template_string
import requests
import base64

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/fx-pro-strategy-bot"
FILE_PATH = "passwords.json"
BRANCH = "main"

HTML_FORM = open("issue_password_template.html", encoding="utf-8").read()

def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded), res.json()["sha"]
    return [], None

def update_passwords_on_github(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    new_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Add new password",
        "content": new_content,
        "branch": BRANCH,
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=data)
    return res.status_code in [200, 201]

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        password = generate_password()
        today = datetime.today().date().isoformat()
        passwords, sha = get_existing_passwords()
        passwords.append({
            "password": password,
            "used": False,
            "issued": today
        })
        if not update_passwords_on_github(passwords, sha):
            password = None
    return render_template_string(HTML_FORM, password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
