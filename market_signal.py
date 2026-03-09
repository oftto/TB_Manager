import yfinance as yf
import requests
import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


WATCHLIST = [
    {"ticker": "005930.KS", "name": "삼성전자", "below": 70000},  # 7만원 이하면 알람
    {"ticker": "AAPL",      "name": "애플",     "above": 200},    # 200달러 이상이면 알람
]

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    )

def check_stock(item):
    ticker = yf.Ticker(item["ticker"])
    price = ticker.fast_info["last_price"]

    if "above" in item and price >= item["above"]:
        return f'📈 <b>{item["name"]}</b> 목표가 돌파!\n현재가: {price:,.0f}'
    if "below" in item and price <= item["below"]:
        return f'📉 <b>{item["name"]}</b> 하한가 도달!\n현재가: {price:,.0f}'

    return None

if __name__ == "__main__":
    alerts = []
    for item in WATCHLIST:
        result = check_stock(item)
        if result:
            alerts.append(result)

    if alerts:
        send_telegram("🔔 <b>주가 알람</b>\n\n" + "\n\n".join(alerts))
        print("알람 전송!")
    else:
        print("조건 미충족, 알람 없음")

