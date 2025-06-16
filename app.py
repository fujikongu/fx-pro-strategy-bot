
import os
import random
import string
import json
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPO")  # 例: "yourname/yourrepo"
FILE_PATH = "passwords.json"

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>パスワード発行</title>
    <style>
        body {
            text-align: center;
            font-size: 1.5em;
            margin-top: 100px;
        }
        button {
            font-size: 2em;
            padding: 20px 60px;
        }
        .password-box {
            margin-top: 30px;
            font-size: 2em;
            color: green;
        }
    </style>
</head>
<body>
    <h1>LINEログイン用パスワード発行</h1>
    <form method="POST">
        <button type="submit">ランダムパスワードを発行</button>
    </form>
    {% if password %}
    <div class="password-box">あなたのパスワード: <strong>{{ password }}</strong></div>
    {% endif %}
</body>
</html>
"""


def generate_password(length=8):
    return "mem" + ''.join(random.choices(string.digits, k=length - 3))


def update_passwords_on_github(new_password):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 既存のファイル取得
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("GitHubファイル取得失敗")

    content = response.json()
    sha = content["sha"]
    existing_data = json.loads(
        requests.utils.unquote(content["content"]).encode('utf-8').decode('base64'))

    # パスワードを追記（既存が list 前提）
    existing_data.append(new_password)

    new_content = json.dumps(existing_data, ensure_ascii=False, indent=2)
    encoded_content = new_content.encode("utf-8").decode("utf-8")

    update_response = requests.put(
        url,
        headers=headers,
        json={
            "message": "Add new password",
            "content": encoded_content.encode("utf-8").decode("utf-8").encode("base64"),
            "sha": sha
        }
    )
    if update_response.status_code not in [200, 201]:
        raise Exception("GitHubファイル更新失敗")


@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        password = generate_password()
        try:
            update_passwords_on_github(password)
        except Exception as e:
            return f"エラーが発生しました: {str(e)}", 500
    return render_template_string(TEMPLATE_HTML, password=password)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
