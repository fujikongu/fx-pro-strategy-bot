
from flask import Flask, request, render_template
import json
import random
import string
import datetime
import base64
import os
import requests

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/fx-pro-strategy-bot"
FILE_PATH = "passwords.json"
BRANCH = "main"

def generate_password(length=6):
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        if isinstance(content, dict) and "content" in content:
            decoded = base64.b64decode(content["content"]).decode("utf-8")
            return json.loads(decoded), content["sha"]
    return [], None

def update_passwords_on_github(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    new_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
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
        today = datetime.date.today().isoformat()
        passwords, sha = get_existing_passwords()
        passwords.append({
            "password": password,
            "used": False,
            "issued": today
        })
        success = update_passwords_on_github(passwords, sha)
        if not success:
            password = None
    return render_template("issue_password_template.html", password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
