import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.title("Investment Command Center")
st.caption("Executive overview and macro pulse across crypto and equities.")

# --- FETCH LIVE DATA FOR SUMMARY SNAPSHOT ---
@st.cache_data(ttl=3600)
def get_snapshot_data():
    # BTC Price
    btc_price = 0.0
    try:
        url = "https://api.blockchain.info/charts/market-price"
        res = requests.get(url, params={"timespan": "30days", "format": "json"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        btc_price = float(res["values"][-1]["y"])
    except:
        pass

    # BBCA Price & 200MA
    bbca_price, bbca_ma200 = 0.0, 0.0
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        df = yf.download("BBCA.JK", period="1y", progress=False, session=session)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        bbca_price = float(df["Close"].iloc[-1])
        bbca_ma200 = float(df["Close"].rolling(200).mean().iloc[-1])
    except:
        pass

    # Fear & Greed
    fng_val, fng_class = 50, "Neutral"
    try:
        res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()["data"][0]
        fng_val, fng_class = int(res["value"]), res["value_classification"]
    except:
        pass

    return btc_price, bbca_price, bbca_ma200, fng_val, fng_class

btc_p, bbca_p, bbca_m200, fng, fng_c = get_snapshot_data()

# --- LAYOUT: QUICK METRICS SNAPSHOT ---
st.subheader("Market Pulse Snapshot")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Bitcoin Spot Price", value=f"${btc_p:,.0f}" if btc_p > 0 else "N/A")
with col2:
    st.metric(label="BBCA.JK Spot Price", value=f"Rp {bbca_p:,.0f}" if bbca_p > 0 else "N/A")
with col3:
    st.metric(label="Crypto Sentiment", value=f"{fng}/100", delta=fng_c, delta_color="off")

st.divider()

# --- SYSTEM DIRECTORY ---
st.subheader("Available Research Engines")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 📊 BTC Macro")
    st.write("On-chain valuation, Puell Multiple, Pi Cycle Top, and technical momentum indicators.")
    st.info("Select **BTC Macro Dashboard** from the sidebar.")

with c2:
    st.markdown("### 🏦 BBCA Matrix")
    st.write("Quantitative equity screening, Moving Average regimes, RSI, and Bollinger bands for Bank Central Asia.")
    st.info("Select **BBCA Equity Matrix** from the sidebar.")

with c3:
    st.markdown("### ⚖️ Allocator")
    st.write("Mathematical sizing and rebalancing model to optimize capital allocation across your portfolio.")
    st.info("Select **Portfolio Allocator** from the sidebar.")
