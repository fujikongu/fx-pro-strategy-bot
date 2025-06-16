import os
import json
import base64
import random
from datetime import datetime
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# GitHub環境変数
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/fx-pro-strategy-bot"
FILE_PATH = "passwords.json"
BRANCH = "main"

# HTMLテンプレート
HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>パスワード発行</title></head>
<body>
    <h2>🔐 ランダムパスワード発行フォーム</h2>
    <form method="post">
        <button type="submit">🔑 発行する</button>
    </form>
    {% if password %}
        <p><strong>✅ 発行されたパスワード: {{ password }}</strong></p>
    {% endif %}
</body>
</html>
"""

def generate_password():
    return f"mem{random.randint(1000, 9999)}"

def get_existing_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content_json = res.json()
        if isinstance(content_json, dict) and "content" in content_json:
            content = content_json["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded), content_json["sha"]
    return [], None

def update_passwords_on_github(new_passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    new_content = base64.b64encode(json.dumps(new_passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": new_content,
        "branch": BRANCH,
        "sha": sha
    }
    res = requests.put(url, headers=headers, data=json.dumps(data))
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
        success = update_passwords_on_github(passwords, sha)
        if not success:
            password = None
    return render_template_string(HTML_FORM, password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
