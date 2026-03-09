import os
import pandas as pd
import requests
import yfinance as yf
import time

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# ----------------------
# telegram
# ----------------------
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)


# ----------------------
# yahoo session (차단 회피)
# ----------------------
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ----------------------
# data fetch (retry)
# ----------------------
def get_data(symbol, period):

    for i in range(5):

        try:

            ticker = yf.Ticker(symbol, session=session)
            data = ticker.history(period=period)

            if not data.empty:
                return data

        except Exception as e:
            print(e)

        time.sleep(3)

    return pd.DataFrame()


# ----------------------
# QQQ data
# ----------------------
qqq = get_data("QQQ", "3mo")

if qqq.empty:
    send("🚨 ERROR: QQQ data download failed")
    exit()

close = qqq["Close"]


# ----------------------
# RSI 계산
# ----------------------
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


# ----------------------
# daily change
# ----------------------
change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100


# ----------------------
# VIX data
# ----------------------
vix = get_data("^VIX", "5d")

if vix.empty:
    send("🚨 ERROR: VIX data download failed")
    exit()

vix_val = vix["Close"].iloc[-1]


# ----------------------
# SIGNAL
# ----------------------
signal = "Regular Buy (50만원)"

if rsi_val <= 30 or vix_val >= 30 or change <= -3:
    signal = "Double Buy (100만원)"


# ----------------------
# MESSAGE
# ----------------------
msg = f"""
📊 QLD Investment Signal

QQQ change: {change:.2f}%
RSI: {rsi_val:.2f}
VIX: {vix_val:.2f}

Action:
{signal}
"""

send(msg)
