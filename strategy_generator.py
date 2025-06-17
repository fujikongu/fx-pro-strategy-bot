import os
import requests
import datetime

def fetch_forex_rate(symbol):
    api_key = os.getenv("TWELVE_API_KEY")

    # TwelveDataの正しい通貨ペア形式に変換
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

def generate_strategy(symbol):
    rate = fetch_forex_rate(symbol)
    if rate is None:
        return f"❌ {symbol} の為替データを取得できませんでした。"

    # ロジック例（ダミー）
    direction = "押し目買い" if rate % 2 > 1 else "戻り売り"
    stop_loss = "直近安値下抜け" if direction == "押し目買い" else "直近高値上抜け"
    profit_point = "フィボナッチ 38.2%" if direction == "押し目買い" else "フィボナッチ 61.8%"
    comment = "トレンドに沿った順張り戦略が有効です。リスク管理も徹底しましょう。"

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    return f"""📅 日付: {today}
■現在レート: {rate:.3f}

■戦略提案：
- トレンド方向: {direction}
- 損切りライン: {stop_loss}
- 利確ポイント: {profit_point}

■AIコメント：
{comment}"""
