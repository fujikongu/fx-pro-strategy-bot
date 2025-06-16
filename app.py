
import os
import json
import base64
import requests
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "fujikongu"
REPO_NAME = "fx-pro-strategy-bot"
FILE_PATH = "passwords.json"

def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_expiration_date():
    return (datetime.now() + timedelta(days=30)).date().isoformat()

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return json.loads(res.text), res.json().get("sha")
    else:
        return [], None

def update_passwords_on_github(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    content = json.dumps(passwords, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": b64,
        "branch": "main",
        "sha": sha
    }

    res = requests.put(url, headers=headers, json=data)
    return res.status_code in [200, 201]

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    error_message = None
    if request.method == "POST":
        try:
            password = generate_password()
            today = datetime.now().date().isoformat()
            passwords, sha = get_existing_passwords()

            passwords.append({
                "password": password,
                "used": False,
                "issued": today
            })

            if not update_passwords_on_github(passwords, sha):
                error_message = "GitHubへの書き込み失敗"

        except Exception as e:
            error_message = f"エラーが発生しました: {e}"

    html = '''
    <html><head><meta charset="UTF-8"></head>
    <body style="font-size: 300%;">
        <h2>🔐 ランダムパスワード発行フォーム</h2>
        <form method="post">
            <button type="submit" style="font-size: 300%;">🪙 発行する</button>
        </form>
        {% if password %}
            <p>✅ あなたのパスワード：<b>{{ password }}</b></p>
            <p>📅 このパスワードは1ヶ月間有効・1回限り使用可能です。</p>
        {% elif error_message %}
            <p style="color:red;">❌ {{ error_message }}</p>
        {% endif %}
    </body></html>
    '''
    return render_template_string(html, password=password, error_message=error_message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
