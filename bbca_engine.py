import os
import requests
import pandas as pd
import yfinance as yf

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram environment variables not found.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def evaluate_bbca():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    df = yf.download("BBCA.JK", period="2y", progress=False, session=session)
    if df.empty:
        print("Failed to fetch BBCA data.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["pct_vs_200ma"] = (df["Close"] / df["MA200"] - 1) * 100

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    ma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    upper_bb = ma20 + (2 * std20)
    lower_bb = ma20 - (2 * std20)
    df["BB_pctB"] = (df["Close"] - lower_bb) / (upper_bb - lower_bb)

    latest = df.dropna().iloc[-1]

    buy_count, sell_count = 0, 0

    # 1. Trend 50 vs 200
    if latest["MA50"] > latest["MA200"]: buy_count += 1
    else: sell_count += 1

    # 2. % vs 200 DMA
    if latest["pct_vs_200ma"] <= -5: buy_count += 1
    elif latest["pct_vs_200ma"] >= 10: sell_count += 1

    # 3. RSI (14)
    if latest["RSI14"] <= 35: buy_count += 1
    elif latest["RSI14"] >= 70: sell_count += 1

    # 4. Bollinger %B
    if latest["BB_pctB"] <= 0: buy_count += 1
    elif latest["BB_pctB"] >= 1: sell_count += 1

    # Score calculation: 2 or more flags required
    if buy_count >= 3:
        verdict = "STRONG BUY ZONE"
        emoji = "🟢"
    elif sell_count >= 3:
        verdict = "STRONG SELL ZONE"
        emoji = "🔴"
    else:
        verdict = "NEUTRAL REGIME"
        emoji = "⚪"

    # Only send alert if actionable signal is present
    if verdict != "NEUTRAL REGIME":
        msg = (
            f"{emoji} *Bank Central Asia (BBCA.JK)*\n"
            f"Verdict: *{verdict}*\n\n"
            f"• Price: Rp{latest['Close']:,.0f}\n"
            f"• Trend: {'BULLISH' if latest['MA50'] > latest['MA200'] else 'BEARISH'}\n"
            f"• % vs 200DMA: {latest['pct_vs_200ma']:+.2f}%\n"
            f"• RSI (14): {latest['RSI14']:.1f}\n"
            f"• Bollinger %B: {latest['BB_pctB']:.2f}"
        )
        send_telegram_msg(msg)
        print("BBCA alert triggered and sent.")
    else:
        print("BBCA regime is neutral; no alert sent.")

if __name__ == "__main__":
    evaluate_bbca()
