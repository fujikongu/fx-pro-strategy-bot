import os
import json
import base64
import datetime
import requests
import openai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub リポジトリ情報
REPO_NAME = "fujikongu/fx-pro-strategy-bot"
FILE_PATH = "passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

user_state = {}

# GitHub上のpasswords.jsonを読み込む関数
def load_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        # GitHub APIが直接JSON配列を返す（v3.rawを指定しているため）
        try:
            return res.json()
        except:
            return []
    return []

# パスワード認証
def verify_password(user_id, input_pw):
    passwords = load_passwords()
    today = datetime.date.today()

    for pw in passwords:
        if pw["password"] == input_pw:
            issued_date = datetime.datetime.strptime(pw["issued"], "%Y-%m-%d").date()
            if not pw["used"] and today <= issued_date + datetime.timedelta(days=30):
                user_state[user_id] = {"authenticated": True, "step": "awaiting_pair"}
                return True
            return False
    return False

# 通貨ペアの選択肢（クイックリプライ）
def create_currency_quick_reply():
    pairs = ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]
    items = [QuickReplyButton(action=MessageAction(label=p, text=p)) for p in pairs]
    return QuickReply(items=items)

# ChatGPTでFX戦略を生成
def generate_strategy(pair):
    prompt = f"""
あなたはプロのFXトレーダーです。以下の形式で「{pair}」の今日の戦略を出力してください：

1. 【環境認識】（例：日足→上昇トレンド、4H→調整下げ中）
2. 【戦略提案】（例：押し目買いを狙いたい。○○のラインが意識されている）
3. 【根拠解説】（使用テクニカル：RSI・移動平均線・水平線等）
4. 【シナリオ分岐】
　A：○○ならロング
　B：○○ならノートレード
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

# LINE Webhookエントリーポイント
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
    message = event.message.text.strip()

    # 未認証ユーザー → パスワード処理
    if user_id not in user_state or not user_state[user_id].get("authenticated"):
        if verify_password(user_id, message):
            reply = TextSendMessage(
                text="✅ 認証成功！分析したい通貨ペアを選んでください：",
                quick_reply=create_currency_quick_reply()
            )
        else:
            reply = TextSendMessage(text="❌ 無効なパスワード、または期限切れです。")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # 通貨ペア選択 → 戦略生成
    if message in ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]:
        strategy = generate_strategy(message)
        reply = TextSendMessage(text=f"📊 {message}の戦略\n\n{strategy}")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # その他
    reply = TextSendMessage(text="通貨ペアを選んでください。", quick_reply=create_currency_quick_reply())
    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
