
import os
import json
import datetime
import openai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数から取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# 認証状態を保持
user_state = {}

# パスワードファイルの読み込み
def load_passwords():
    with open("passwords.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 認証チェック
def verify_password(user_id, input_pw):
    passwords = load_passwords()
    today = datetime.date.today()

    for pw in passwords:
        if pw["password"] == input_pw:
            expire = datetime.datetime.strptime(pw["issued"], "%Y-%m-%d").date() + datetime.timedelta(days=30)
            if pw["used"] and today <= expire:
                user_state[user_id] = {"authenticated": True, "step": "awaiting_pair"}
                return True
            else:
                return False
    return False

# クイックリプライ作成
def create_currency_quick_reply():
    pairs = ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]
    items = [QuickReplyButton(action=MessageAction(label=p, text=p)) for p in pairs]
    return QuickReply(items=items)

# ChatGPTで戦略生成
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

# LINEイベント処理
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message = event.message.text.strip()

    # 未認証の場合：パス入力と判定
    if user_id not in user_state or not user_state[user_id].get("authenticated"):
        if verify_password(user_id, message):
            reply = TextSendMessage(text="✅ 認証成功！分析したい通貨ペアを選んでください：", quick_reply=create_currency_quick_reply())
        else:
            reply = TextSendMessage(text="❌ 無効なパスワード、または期限切れです。")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # 通貨ペアの選択 → 戦略生成
    if message in ["USDJPY", "EURUSD", "GBPJPY", "AUDJPY", "EURJPY"]:
        strategy = generate_strategy(message)
        reply = TextSendMessage(text=f"📊 {message}の戦略\n\n{strategy}")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # それ以外のメッセージ
    reply = TextSendMessage(text="通貨ペアを選んでください。", quick_reply=create_currency_quick_reply())
    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ← この行を追加
    app.run(host="0.0.0.0", port=port)        # ← ポートとホストを明示
