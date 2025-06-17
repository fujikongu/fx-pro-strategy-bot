import os
import requests
import openai


def fetch_forex_rate(symbol):
    """
    TwelveData APIを使用して指定された通貨ペアのリアルタイム為替レートを取得
    """
    api_key = os.getenv("TWELVE_API_KEY")
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"
    res = requests.get(url)
    data = res.json()
    return float(data["price"]) if "price" in data else None


def generate_strategy(symbol):
    """
    為替レートを取得し、それに基づいた戦略をChatGPTで生成
    """
    price = fetch_forex_rate(symbol)
    if not price:
        return f"❌ {symbol} の為替データを取得できませんでした。"

    prompt = f"""
現在の為替レート {symbol} = {price} に基づいて、以下の形式でFX戦略を作成してください：

■現状分析：
■戦略提案：
- トレンド方向：
- 損切りライン：
- 利確ポイント：

■AIコメント：
    """.strip()

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
