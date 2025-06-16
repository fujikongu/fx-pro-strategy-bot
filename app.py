import os
import json
import datetime
import requests
import random
import string
from flask import Flask, request, render_template

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fx-strategy-bot"
FILE_PATH = "passwords.json"
GITHUB_API_URL = f"https://api.github.com/repos/fujikongu/{REPO_NAME}/contents/{FILE_PATH}"

def generate_password(length=8):
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_existing_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    res = requests.get(GITHUB_API_URL, headers=headers)
    if res.status_code == 200:
        content = res.json()
        file_content = json.loads(
            requests.get(content["download_url"]).text)
        sha = content["sha"]
        return file_content, sha
    return [], None

def update_passwords_on_github(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "message": "Update passwords.json",
        "content": base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode()).decode(),
        "sha": sha
    }
    res = requests.put(GITHUB_API_URL, headers=headers, json=data)
    return res.status_code == 200

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
    return render_template("large_button_template.html", password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
