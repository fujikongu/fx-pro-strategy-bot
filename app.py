
import os
import json
import random
import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

PASSWORD_FILE = "passwords.json"

# パスワード生成関数
def generate_password():
    return f"mem{random.randint(1, 9999):04d}"

# HTMLフォームテンプレート
HTML_FORM = """
<!doctype html>
<title>パスワード発行</title>
<h2>ランダムパスワード発行フォーム</h2>
<form method="post">
  <button type="submit">発行する</button>
</form>
{% if password %}
  <p>✅ あなたのパスワード：<strong>{{ password }}</strong></p>
  <p>※このパスワードは1ヶ月間有効・1回限り使用可能です。</p>
{% endif %}
"""

# パスワード保存関数
def save_password(password):
    today = datetime.date.today().isoformat()
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append({
        "password": password,
        "used": False,
        "issued": today
    })

    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ルート：フォーム表示と発行処理
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
