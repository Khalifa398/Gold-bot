import yfinance as yf
import pandas as pd
from telegram import Bot
import os

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
bot = Bot(token=TOKEN)

df = yf.download("GC=F", period="60d", interval="15m", progress=False)
if len(df) > 60:
    df["ema9"]  = df["Close"].ewm(span=9).mean()
    df["ema21"] = df["Close"].ewm(span=21).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    df["rsi"] = 100 - 100 / (1 + gain / loss)
    tr = pd.concat([df["High"]-df["Low"],
                    (df["High"]-df["Close"].shift()).abs(),
                    (df["Low"]-df["Close"].shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()

    last, prev = df.iloc[-1], df.iloc[-2]
    price, rsi, atr = float(last["Close"]), float(last["rsi"]), float(last["atr"])
    trend = "UP 📈" if last["ema9"] > last["ema21"] else "DOWN 📉"

    crossed_up   = prev["ema9"] <= prev["ema21"] and last["ema9"] > last["ema21"]
    crossed_down = prev["ema9"] >= prev["ema21"] and last["ema9"] < last["ema21"]

    msg = None
    if crossed_up and rsi < 65:
        msg = (f"🟢 LONG XAU/USD (15m)\n💰 Entry: {price:.2f}\n"
               f"🛑 SL: {price - 2*atr:.2f}\n🎯 TP: {price + 3*atr:.2f}\n\n"
               f"📊 Trend: {trend} | RSI: {rsi:.1f}")
    elif crossed_down and rsi > 35:
        msg = (f"🔴 SHORT XAU/USD (15m)\n💰 Entry: {price:.2f}\n"
               f"🛑 SL: {price + 2*atr:.2f}\n🎯 TP: {price - 3*atr:.2f}\n\n"
               f"📊 Trend: {trend} | RSI: {rsi:.1f}")
    if msg:
        bot.send_message(chat_id=CHAT_ID, text=msg + "\n\n⚠️ Not financial advice")
