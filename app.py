import os
import json
import random
import string
import datetime
import requests
from flask import Flask, request, render_template

app = Flask(__name__)

GITHUB_REPO = "your-username/your-repo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def generate_password():
    return "mem" + "".join(random.choices(string.digits, k=4))

def update_passwords_json(new_password):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/passwords.json"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False

    content = response.json()
    existing_data = json.loads(
        requests.get(content["download_url"]).text
    )

    # 有効期限付き（1ヶ月）パスワード形式で追記
    now = datetime.datetime.utcnow()
    expiration = (now + datetime.timedelta(days=30)).isoformat()
    existing_data.append({
        "password": new_password,
        "created_at": now.isoformat(),
        "expires_at": expiration
    })

    updated_content = json.dumps(existing_data, indent=2, ensure_ascii=False)
    encoded_content = updated_content.encode("utf-8").decode("utf-8")

    commit_message = f"Add new password: {new_password}"
    put_data = {
        "message": commit_message,
        "content": encoded_content.encode("utf-8").decode("utf-8").encode("base64").decode(),
        "sha": content["sha"]
    }

    response = requests.put(url, headers=headers, json=put_data)
    return response.status_code == 200

@app.route("/")
def index():
    return render_template("issue_password_template.html")

@app.route("/issue-password", methods=["POST"])
def issue_password():
    new_password = generate_password()
    if update_passwords_json(new_password):
        return f"✅ 発行されたパスワード：<strong>{new_password}</strong><br>有効期限：発行日より30日間"
    else:
        return "❌ パスワード発行に失敗しました。"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)