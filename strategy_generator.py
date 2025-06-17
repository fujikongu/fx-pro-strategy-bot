import os
import requests
import datetime
import openai

# TwelveData から為替レートを取得
def fetch_forex_rate(symbol):
    api_key = os.getenv("TWELVE_API_KEY")

    pair_map = {
        "USDJPY": "USD/JPY",
        "EURUSD": "EUR/USD",
        "GBPJPY": "GBP/JPY",
        "AUDJPY": "AUD/JPY",
        "EURJPY": "EUR/JPY"
    }

    if symbol not in pair_map:
        return None

    formatted = pair_map[symbol]
    url = f"https://api.twelvedata.com/price?symbol={formatted}&apikey={api_key}"
    res = requests.get(url)

    try:
        data = res.json()
        return float(data["price"]) if "price" in data else None
    except:
        return None

# ChatGPTで戦略コメントを生成
def generate_chatgpt_comment(symbol, rate, term):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
以下はFXの上級トレーダー向け分析コメントを生成するタスクです。

条件:
- 通貨ペア: {symbol}
- 日付: {today}
- 現在レート: {rate}
- トレード期間: {term}

内容:
- トレード期間（{term}）に合わせた戦略分析
- トレンドの方向性（上昇・下降・レンジ）
- 買いまたは売り戦略の根拠
- 損切りと利確のポイント案
- テクニカル指標に基づいた戦略提案（RSI, MA, フィボナッチ等）
- 明確で論理的な戦略アドバイス（200文字以内）

出力形式：
「■戦略コメント：」から始めて、トレーダー向けコメントを出力。
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message["content"].strip()

# 順張り/逆張りのAI判定コメント生成
def determine_trading_type(symbol, rate, term):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
以下の条件に基づき、現在の為替相場における戦略として「順張り」または「逆張り」のどちらを採用すべきか判断し、簡潔にコメントしてください。

条件:
- 通貨ペア: {symbol}
- レート: {rate}
- トレード期間: {term}
- 指標は仮定で構いません（例：RSIやMA、トレンド方向等）

出力形式（50文字以内）：
「■AI戦略タイプ判定：…」から始めて1文で。
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message["content"].strip()

# 総合戦略生成
def generate_strategy(symbol, term="中期"):
    rate = fetch_forex_rate(symbol)
    if rate is None:
        return f"❌ {symbol} の為替データを取得できませんでした。"

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    comment = generate_chatgpt_comment(symbol, rate, term)
    trading_type = determine_trading_type(symbol, rate, term)

    return f"""📅 日付: {today}
■現在レート: {rate:.3f}
■トレード期間: {term}

{comment}

{trading_type}
"""
