import os
import json
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

PASSWORD_FILE = "passwords.json"

def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

def load_passwords():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_passwords(passwords):
    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

@app.route("/issue-password")
def issue_password():
    password = generate_password()
    expiration_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    passwords = load_passwords()
    passwords.append({
        "password": password,
        "issued": datetime.now().strftime("%Y-%m-%d"),
        "expires": expiration_date
    })
    save_passwords(passwords)

    return render_template("issue_password_template.html", password=password, expiration=expiration_date)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
