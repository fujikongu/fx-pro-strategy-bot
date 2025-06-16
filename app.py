
import os
import json
import base64
import datetime
import random
import string
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")  # 例: fujikongu/fx-pro-strategy-bot
FILE_PATH = "passwords.json"

# GitHubからpasswords.jsonを読み込み
def load_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content_json = res.json()
        if isinstance(content_json, dict) and "content" in content_json:
            content = content_json["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded), content_json.get("sha", "")
    return [], ""

# GitHubのpasswords.jsonを更新
def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    content_str = json.dumps(passwords, ensure_ascii=False, indent=2)
    content_b64 = base64.b64encode(content_str.encode()).decode()
    data = {
        "message": "Add new password",
        "content": content_b64,
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=data)
    return res.status_code == 200

# ランダムパス生成
def generate_random_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

# HTMLフォーム表示・処理
@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    if request.method == "POST":
        passwords, sha = load_passwords()
        new_pass = generate_random_password()
        new_password = {
            "password": new_pass,
            "issued": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        passwords.append(new_password)
        success = update_passwords(passwords, sha)
        if success:
            return f"<h2>✅ パスワード発行完了：{new_pass}</h2>"
        else:
            return "<h2>❌ 更新に失敗しました。</h2>", 500

    # GET表示用HTML
    return render_template_string("""
        <h2>パスワード発行</h2>
        <form method="post">
            <button type="submit">発行する</button>
        </form>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
