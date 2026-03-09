import os
import pandas as pd
import requests
import yfinance as yf
yf.set_tz_cache_location("/tmp")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# QQQ data
# qqq = yf.download("QQQ", period="6mo", progress=False, threads=False)
ticker = yf.Ticker("QQQ")
qqq = ticker.history(period="6mo")

if qqq.empty or len(qqq) < 30:
    print("QQQ data download failed")
    exit()

close = qqq["Close"]

delta = close.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

if rsi.empty:
    print("RSI calculation failed")
    exit()

rsi_val = rsi.iloc[-1]

change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100

# VIX
# vix = yf.download("^VIX", period="5d", progress=False, threads=False)
vix = yf.Ticker("^VIX").history(period="5d")

if vix.empty:
    print("VIX data failed")
    exit()

vix_val = vix["Close"].iloc[-1]

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
