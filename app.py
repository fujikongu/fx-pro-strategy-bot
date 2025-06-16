
REPO_OWNER = "your-github-username"
REPO_NAME = "your-repo-name"
FILE_PATH = "passwords.json"
GITHUB_TOKEN = "your-github-token"

from flask import Flask
import requests
import base64
import random
import string
from datetime import datetime

app = Flask(__name__)

def generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def fetch_passwords():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    content = response.json()
    if response.status_code == 200:
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), content['sha']
    else:
        return [], None

def update_github_file(passwords):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    current_passwords, sha = fetch_passwords()
    content = json.dumps(passwords, ensure_ascii=False, indent=2)
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    data = {
        "message": "パスワードを追加",
        "content": encoded_content,
        "sha": sha
    }
    requests.put(url, headers=headers, data=json.dumps(data))

@app.route("/issue-password", methods=["GET"])
def issue_password():
    passwords, _ = fetch_passwords()
    new_password = {
        "password": generate_password(),
        "used": False,
        "issued": datetime.now().strftime("%Y-%m-%d")
    }
    passwords.append(new_password)
    update_github_file(passwords)
    return (
        f"✅ あなたのパスワード：{new_password['password']}\n"
        f"📅 有効期限：発行日から1ヶ月間有効・使い放題"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
