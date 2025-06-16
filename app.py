
import os
import json
import random
import string
import base64
import requests
from flask import Flask, request
from datetime import datetime, timedelta

app = Flask(__name__)

# GitHub設定
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "fujikongu"
REPO_NAME = "fx-pro-strategy-bot"
FILE_PATH = "passwords.json"

# パスワード生成
def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

# 有効期限の設定（1ヶ月）
def get_expiration_date():
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

# GitHubからpasswords.jsonを取得
def fetch_passwords():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"
    res = requests.get(url)
    if res.status_code == 200:
        return json.loads(res.text)
    return []

# GitHubへpasswords.jsonをアップロード
def update_passwords(passwords):
    get_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_res = requests.get(get_url, headers=headers)
    if get_res.status_code != 200:
        return False

    sha = get_res.json()["sha"]
    encoded = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode()).decode()

    data = {
        "message": "Update passwords.json",
        "content": encoded,
        "sha": sha
    }
    put_res = requests.put(get_url, headers=headers, json=data)
    return put_res.status_code == 200

@app.route("/issue-password", methods=["GET"])
def issue_password():
    try:
        passwords = fetch_passwords()
    except Exception:
        return "エラーが発生しました: GitHubファイル取得失敗"

    new_pass = generate_password()
    new_entry = {
        "password": new_pass,
        "issued": datetime.now().strftime("%Y-%m-%d")
    }
    passwords.append(new_entry)

    if update_passwords(passwords):
        return f"""
        <html>
            <body style="text-align:center; padding-top:50px;">
                <div style="font-size: 36px; font-weight: bold;">✅ あなたのパスワード:</div>
                <div style="font-size: 72px; font-weight: bold; color: #007BFF;">{new_pass}</div>
                <div style="font-size: 24px; margin-top:20px;">
                    📅 このパスワードは1ヶ月間有効・何度でも使用可能です。
                </div>
            </body>
        </html>
        """
    else:
        return "❌ GitHubへの保存に失敗しました。"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
