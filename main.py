import os
import json
import base64
import datetime
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from strategy_generator import generate_strategy  # 通貨戦略生成関数

app = Flask(__name__)

# 環境変数からLINEチャンネル情報
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')  # 例: fujikongu/fx-pro-strategy-bot
FILE_PATH = "passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーステート
user_state = {}

# 通貨クイックリプライ
currency_quick_reply = QuickReply(items=[
    QuickReplyButton(action=MessageAction(label="USDJPY", text="USDJPY")),
    QuickReplyButton(action=MessageAction(label="EURUSD", text="EURUSD")),
    QuickReplyButton(action=MessageAction(label="GBPJPY", text="GBPJPY")),
    QuickReplyButton(action=MessageAction(label="AUDJPY", text="AUDJPY")),
    QuickReplyButton(action=MessageAction(label="EURJPY", text="EURJPY")),
])

# GitHubのpasswords.jsonを読み込む
def load_passwords():
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
            return json.loads(decoded)
    return []

# GitHubへpasswords.jsonを更新
def update_passwords(passwords):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return False

    sha = res.json()["sha"]
    encoded = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode()).decode()

    data = {
        "message": "Mark password as used",
        "content": encoded,
        "sha": sha
    }
    put_res = requests.put(url, headers=headers, json=data)
    return put_res.status_code == 200

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text.strip()
    passwords = load_passwords()

    # 認証未完了
    if user_id not in user_state:
        for pw in passwords:
            if pw["password"] == message_text:
                issued_date = datetime.datetime.strptime(pw["issued"], "%Y-%m-%d")
                if datetime.datetime.now() > issued_date + datetime.timedelta(days=30):
                    reply_text = "❌ 無効なパスワード、または期限切れです。"
                    break
                if pw["used"]:
                    reply_text = "❌ このパスワードはすでに使用されています。"
                else:
                    pw["used"] = True
                    update_passwords(passwords)  # ✅ GitHubに反映
                    user_state[user_id] = {
                        "authenticated": True,
                        "step": "await_currency_pair"
                    }
                    reply_text = "✅ 認証成功！分析したい通貨ペアを選んでください："
                break
        else:
            reply_text = "❌ 無効なパスワード、または期限切れです。"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=currency_quick_reply)
        )
        return

    # 通貨ペア選択 → 戦略出力
    if user_state.get(user_id, {}).get("step") == "await_currency_pair":
        if message_text in ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]:
            strategy = generate_strategy(message_text)
            reply = TextSendMessage(text=f"📊 {message_text}の戦略\n\n{strategy}")
            line_bot_api.reply_message(event.reply_token, reply)
            user_state.pop(user_id, None)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ 有効な通貨ペアを選択してください。", quick_reply=currency_quick_reply)
            )
        return

    # 認証後でも無関係なメッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="通貨ペアを選んでください：", quick_reply=currency_quick_reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
