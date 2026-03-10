import os
import pandas as pd
import requests
import time

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# -------------------------
# total stocks
# -------------------------
url = os.environ["TARGET_SHEET"]
df = pd.readcsv(url)
holding=df.iloc[0,-1]


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)


# -------------------------
# stooq data fetch
# -------------------------
def get_stooq(symbol):

    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"

    try:
        df = pd.read_csv(url)

        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

        return df.sort_index()

    except:
        return pd.DataFrame()

# -------------------------
# Fear & Greed
# -------------------------

import requests

def get_fear_greed():

    url = "https://api.alternative.me/fng/?limit=1"

    try:

        r = requests.get(url, timeout=10)

        data = r.json()

        score = int(data["data"][0]["value"])
        rating = data["data"][0]["value_classification"]

        return score, rating

    except Exception as e:

        print("FearGreed error:", e)

        return None, None

fear_greed = get_fear_greed()

if fear_greed is None:
    send("🚨 ERROR: Fear & Greed data failed")
    #exit()


# -------------------------
# QQQ data
# -------------------------
qqq = get_stooq("qqq.us")

if qqq.empty:
    send("🚨 ERROR: QQQ data download failed")
    exit()

close = qqq["Close"].tail(60)



# -------------------------
# RSI data
# -------------------------
delta = close.diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss

rsi = 100 - (100 / (1 + rs))

rsi_val = rsi.dropna().iloc[-1]


# -------------------------
# change
# -------------------------
change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100


# -------------------------
# VIX
# -------------------------
vix = get_stooq("vi.c").tail(10)

if vix.empty:
    send("🚨 ERROR: VIX data failed")
    #exit()

vix_val = vix["Close"].iloc[-1]


# -------------------------
# QLD
# -------------------------
qld = get_stooq("qld.us").tail(10)

if qld.empty:
    send("🚨 ERROR: QLD data failed")
    #exit()

qld_val = qld["Close"].iloc[-1]


# -------------------------
# SIGNAL
# -------------------------
signal = "Regular Buy (50만원)"

if rsi_val <= 30 or vix_val >= 30 or change <= -3:
    signal = "Double Buy (100만원)"
elif  rsi_val <= 25 or vix_val >= 35:
    signal = "TQQQ Buy (100만원) RSI 50 or 10days"


msg = f"""
📊 QLD Investment Signal
Holding: {holding}

QQQ change: {change:.2f}%
QLD: {qld_val:.2f}
RSI: {rsi_val:.2f}
VIX: {vix_val:.2f}
Crypto Fear & Greed: {fear_greed}

Action:
{signal}
"""

send(msg)
