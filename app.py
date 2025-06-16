from flask import Flask, request, jsonify
import os
import json
import random
import datetime
import string

app = Flask(__name__)

GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PASSWORD_FILE = "passwords.json"

# ランダムパスワード生成
def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 新規パスワードを作成し、1ヶ月有効として保存
def issue_new_password():
    new_password = generate_password()
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    if not os.path.exists(PASSWORD_FILE):
        passwords = []
    else:
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            passwords = json.load(f)

    passwords.append({
        "password": new_password,
        "issued": today,
        "used": True
    })

    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

    return new_password

@app.route("/issue-password", methods=["GET"])
def issue_password():
    new_password = issue_new_password()
    return jsonify({"password": new_password})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
