from flask import Flask, request, jsonify
import random
import json
import datetime
import os

app = Flask(__name__)

PASSWORD_FILE = "passwords.json"

def issue_new_password():
    password = "mem" + str(random.randint(1000, 9999))
    today = datetime.date.today().isoformat()
    new_entry = {
        "password": password,
        "used": False,
        "issued": today
    }

    with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
        passwords = json.load(f)

    passwords.append(new_entry)

    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

    return password

@app.route("/issue-password", methods=["POST"])
def issue_password():
    new_password = issue_new_password()
    return jsonify({"password": new_password})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
