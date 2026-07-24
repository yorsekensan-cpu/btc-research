import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Market Dashboard", layout="wide")

st.title("Market Intelligence Dashboard")
st.caption("Quantitative regime monitoring.")

# --- LIVE PRICE FETCHING ENGINE ---
@st.cache_data(ttl=60) # Caches the price for 60 seconds to prevent API rate limits
def get_live_price(ticker):
    try:
        # Fetching a 1-day snapshot with 1-minute intervals
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not df.empty:
            # Handle yfinance multi-index columns if present
            if isinstance(df.columns, pd.MultiIndex):
                return df['Close'].iloc[-1].values[0]
            return df['Close'].iloc[-1]
    except Exception:
        pass
    return None

btc_price = get_live_price("BTC-USD")
bbca_price = get_live_price("BBCA.JK")

# ==========================================
# 🟢 CRYPTO ECOSYSTEM SECTION
# ==========================================
st.divider()

col1, col2, col3 = st.columns([1, 8, 3])
with col1:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=40)
with col2:
    st.subheader("Crypto Assets")
with col3:
    if btc_price:
        st.metric(label="Live BTC/USD", value=f"${btc_price:,.2f}")
    else:
        st.metric(label="Live BTC/USD", value="Loading...")

st.page_link("pages/btc_macro.py", label="Bitcoin (BTC) Macro Regime", icon="📈")


# ==========================================
# 🔵 IDX EQUITIES SECTION
# ==========================================
st.divider()

col4, col5, col6 = st.columns([1, 8, 3])
with col4:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=40)
with col5:
    st.subheader("IDX Equities")
with col6:
    if bbca_price:
        st.metric(label="Live BBCA", value=f"Rp{bbca_price:,.0f}")
    else:
        st.metric(label="Live BBCA", value="Loading...")

st.page_link("pages/bbca_matrix.py", label="Bank Central Asia (BBCA.JK) Equity Matrix", icon="🏦")
