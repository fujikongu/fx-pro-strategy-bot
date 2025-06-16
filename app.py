
import os
import json
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "fujikongu"
REPO_NAME = "line-tarot-bot-2"
FILE_PATH = "passwords.json"

def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_expiration_date():
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

def fetch_passwords():
    import requests
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    return []

def update_github_file(passwords):
    import base64
    import requests

    get_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    get_response = requests.get(get_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = get_response.json()["sha"]

    new_content = json.dumps(passwords, ensure_ascii=False, indent=2)
    b64_content = base64.b64encode(new_content.encode()).decode()

    data = {
        "message": "Add new password",
        "content": b64_content,
        "sha": sha
    }

    response = requests.put(get_url, headers={"Authorization": f"token {GITHUB_TOKEN}"}, json=data)
    return response.status_code == 200 or response.status_code == 201

@app.route("/issue-password", methods=["GET"])
def issue_password():
    passwords = fetch_passwords()
    new_password = generate_password()
    expiration = get_expiration_date()
    passwords.append({"password": new_password, "expires": expiration})

    if update_github_file(passwords):
        return f"✅ 発行されたパスワード：{new_password}（有効期限：{expiration}まで）"
    else:
        return "❌ パスワードの発行に失敗しました。"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
