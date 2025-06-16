import os
import json
import random
import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)
PASSWORD_FILE = "passwords.json"

# HTMLテンプレートを外部ファイルから読み込み
with open("issue_password_template.html", encoding="utf-8") as f:
    HTML_FORM = f.read()

def generate_password():
    return f"mem{random.randint(1, 9999):04d}"

def save_password(password):
    today = datetime.date.today().isoformat()
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    data.append({"password": password, "used": False, "issued": today})
    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        password = generate_password()
        save_password(password)
    return render_template_string(HTML_FORM, password=password)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)