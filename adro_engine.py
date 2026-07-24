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

def evaluate_adro():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    # 1. Fetch ADRO Equity Data
    df = yf.download("ADRO.JK", period="2y", progress=False, session=session)
    if df.empty:
        print("Failed to fetch ADRO data.")
        return
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # 2. Fetch USD/IDR Currency Data
    fx_df = yf.download("IDR=X", period="1y", progress=False, session=session)
    if isinstance(fx_df.columns, pd.MultiIndex):
        fx_df.columns = fx_df.columns.droplevel(1)
        
    fx_df["MA50"] = fx_df["Close"].rolling(50).mean()
    latest_fx = fx_df.dropna().iloc[-1]

    # Calculate Technicals for ADRO
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

    # 1. Equity Trend
    if latest["MA50"] > latest["MA200"]: buy_count += 1
    else: sell_count += 1

    # 2. % vs 200 DMA (Wider cyclical bands for ADRO)
    if latest["pct_vs_200ma"] <= -15: buy_count += 1
    elif latest["pct_vs_200ma"] >= 15: sell_count += 1

    # 3. RSI (14)
    if latest["RSI14"] <= 35: buy_count += 1
    elif latest["RSI14"] >= 70: sell_count += 1

    # 4. Bollinger %B
    if latest["BB_pctB"] <= 0: buy_count += 1
    elif latest["BB_pctB"] >= 1: sell_count += 1
    
    # 5. Macro Proxy: USD/IDR Strength
    if latest_fx["Close"] > latest_fx["MA50"]: buy_count += 1
    else: sell_count += 1

    # Score calculation: 3 or more flags required
    if buy_count >= 3:
        verdict = "CYCLICAL BUY ZONE"
        emoji = "🟢"
    elif sell_count >= 3:
        verdict = "CYCLICAL SELL ZONE"
        emoji = "🔴"
    else:
        verdict = "NEUTRAL REGIME"
        emoji = "⚪"

    if verdict != "NEUTRAL REGIME":
        msg = (
            f"{emoji} *Adaro Energy (ADRO.JK)*\n"
            f"Verdict: *{verdict}*\n\n"
            f"• Price: Rp{latest['Close']:,.0f}\n"
            f"• Trend: {'BULLISH' if latest['MA50'] > latest['MA200'] else 'BEARISH'}\n"
            f"• % vs 200DMA: {latest['pct_vs_200ma']:+.2f}%\n"
            f"• RSI (14): {latest['RSI14']:.1f}\n"
            f"• USD/IDR Tailwind: {'ACTIVE' if latest_fx['Close'] > latest_fx['MA50'] else 'INACTIVE'}"
        )
        send_telegram_msg(msg)
        print("ADRO alert triggered and sent.")
    else:
        print("ADRO regime is neutral; no alert sent.")

if __name__ == "__main__":
    evaluate_adro()
