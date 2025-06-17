import os
import json
import base64
import datetime
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)

from strategy_generator import generate_strategy  # 通貨戦略生成関数

app = Flask(__name__)

# 環境変数からLINEチャンネル情報を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('REPO_NAME')  # 例: fujikongu/fx-pro-strategy-bot
FILE_PATH = "passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーステートを保持
user_state = {}

# クイックリプライの定義（通貨ペア選択）
currency_quick_reply = QuickReply(items=[
    QuickReplyButton(action=MessageAction(label="USDJPY", text="USDJPY")),
    QuickReplyButton(action=MessageAction(label="EURUSD", text="EURUSD")),
    QuickReplyButton(action=MessageAction(label="GBPJPY", text="GBPJPY")),
    QuickReplyButton(action=MessageAction(label="AUDJPY", text="AUDJPY")),
    QuickReplyButton(action=MessageAction(label="EURJPY", text="EURJPY")),
])

# クイックリプライ（戦略タイプ選択）
strategy_quick_reply = QuickReply(items=[
    QuickReplyButton(action=MessageAction(label="短期", text="短期")),
    QuickReplyButton(action=MessageAction(label="中期", text="中期")),
    QuickReplyButton(action=MessageAction(label="長期", text="長期")),
])

# GitHubからpasswords.jsonを読み込む
def load_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content_json = res.json()
        if isinstance(content_json, dict) and "content" in content_json:
            content = content_json["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
    return []

# Webhookのエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# メッセージイベント処理
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
                else:
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

    # 通貨ペア入力待ち
    if user_state.get(user_id, {}).get("step") == "await_currency_pair":
        if message_text in ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]:
            user_state[user_id]["pair"] = message_text
            user_state[user_id]["step"] = "await_strategy_type"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="分析したい戦略のタイプを選んでください：", quick_reply=strategy_quick_reply)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ 有効な通貨ペアを選択してください。", quick_reply=currency_quick_reply)
            )
        return

    # 戦略タイプ選択待ち
    if user_state.get(user_id, {}).get("step") == "await_strategy_type":
        if message_text in ["短期", "中期", "長期"]:
            pair = user_state[user_id]["pair"]
            strategy = generate_strategy(pair, message_text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"📊 {pair} の{message_text}戦略\n\n{strategy}")
            )
            user_state.pop(user_id, None)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ 短期・中期・長期のいずれかを選んでください。", quick_reply=strategy_quick_reply)
            )
        return

    # その他のメッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="通貨ペアを選んでください：", quick_reply=currency_quick_reply)
    )

# アプリ実行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
