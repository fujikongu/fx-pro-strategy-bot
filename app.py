
import os
import json
import base64
import requests
import random
import string
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/fx-pro-strategy-bot"
FILE_PATH = "passwords.json"
BRANCH = "main"

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔐 ランダムパスワード発行フォーム</title>
</head>
<body>
    <h2>🔐 ランダムパスワード発行フォーム</h2>
    <form method="post">
        <button type="submit">📛 発行する</button>
    </form>
    {% if password %}
        <p style="color:green;">✅ あなたのパスワード：<strong>{{ password }}</strong></p>
        <p style="color:green;">📅 このパスワードは1ヶ月間有効・1回限り使用可能です。</p>
    {% endif %}
</body>
</html>
"""

def generate_password(length=8):
    return "mem" + ''.join(random.choices(string.digits, k=4))

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
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
        today = datetime.today().date().isoformat()
        try:
            passwords, sha = get_existing_passwords()
            passwords.append({
                "password": password,
                "used": False,
                "issued": today
            })
            success = update_passwords_on_github(passwords, sha)
            if not success:
                password = None
        except Exception as e:
            return f"エラーが発生しました: GitHubファイル取得失敗<br>{str(e)}"
    return render_template_string(HTML_FORM, password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
