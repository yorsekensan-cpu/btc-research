import os
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    
    print(f"Attempting to send message to Chat ID: {CHAT_ID}")
    response = requests.post(url, json=payload)
    
    print(f"Telegram API Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Telegram Error Details: {response.json()}")

def check_signal(ticker, name):
    df = yf.download(ticker, period="60d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    yesterday, today = df.iloc[-2], df.iloc[-1]
    
    if yesterday['Close'] < yesterday['MA20'] and today['Close'] > today['MA20']:
        return f"📈 *{name}* crossed ABOVE its 20-day Moving Average. Signal changed to: *BUY*"
    elif yesterday['Close'] > yesterday['MA20'] and today['Close'] < today['MA20']:
        return f"📉 *{name}* crossed BELOW its 20-day Moving Average. Signal changed to: *SELL*"
    return None

if __name__ == "__main__":
    # FORCE DIAGNOSTIC PING FIRST
    send_telegram_msg("🚀 *Diagnostic Test:* Pipeline network connection is active.")

    messages = []
    bbca_msg = check_signal("BBCA.JK", "Bank Central Asia (BBCA)")
    if bbca_msg: messages.append(bbca_msg)
        
    btc_msg = check_signal("BTC-USD", "Bitcoin (BTC)")
    if btc_msg: messages.append(btc_msg)
        
    if messages:
        final_text = "🔔 *Market Signal Alert*\n\n" + "\n\n".join(messages)
        send_telegram_msg(final_text)
        print("Alert triggered and sent.")
    else:
        print("Market status unchanged. No alerts triggered today.")
