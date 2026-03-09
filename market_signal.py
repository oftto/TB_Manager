import os
import pandas as pd
import requests
import yfinance as yf
import time

yf.set_tz_cache_location("/tmp")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)


# -------------------------
# 데이터 가져오기 (Yahoo → Stooq fallback)
# -------------------------
def get_data(symbol, period="1mo"):

    for _ in range(3):
        try:
            data = yf.Ticker(symbol).history(period=period)
            if not data.empty:
                return data
        except:
            pass
        time.sleep(3)

    # fallback: stooq
    try:
        url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"
        data = pd.read_csv(url)

        data["Date"] = pd.to_datetime(data["Date"])
        data.set_index("Date", inplace=True)

        return data
    except:
        return pd.DataFrame()


# -------------------------
# QQQ data
# -------------------------
qqq = get_data("QQQ")

if qqq.empty or len(qqq) < 30:
    msg = "🚨 ERROR: QQQ data download failed"
    send(msg)
    exit()

close = qqq["Close"]

delta = close.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

if rsi.dropna().empty:
    send("🚨 ERROR: RSI calculation failed")
    exit()

rsi_val = rsi.dropna().iloc[-1]

change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100


# -------------------------
# VIX data
# -------------------------
vix = get_data("^VIX", "5d")

if vix.empty:
    send("🚨 ERROR: VIX data failed")
    exit()

vix_val = vix["Close"].iloc[-1]


# -------------------------
# SIGNAL
# -------------------------
signal = "Regular Buy (50만원)"

if rsi_val <= 30 or vix_val >= 30 or change <= -3:
    signal = "Double Buy (100만원)"

msg = f"""
📊 QLD Investment Signal

QQQ change: {change:.2f}%
RSI: {rsi_val:.2f}
VIX: {vix_val:.2f}

Action:
{signal}
"""

send(msg)
