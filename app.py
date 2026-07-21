import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="BTC Analytics", layout="wide")
st.title("Bitcoin Unified Analytics (5-Year Macro View)")

# 1. Price & MA200 (Expanded to 5-Year Macro View)
@st.cache_data(ttl=3600)
def get_price():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
    # Coinbase max candle limit per request is 300 gran-slots unless paginated, 
    # but we can request historical chunks or use alternative public aggregators.
    # To keep it lightweight and free, we pull the maximum available daily candles (~300 days standard per call) 
    # OR we use CoinMetrics for the 5-year price history alongside MVRV to ensure a seamless multi-year alignment.
    url_cm = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {
        "assets": "btc",
        "metrics": "PriceUSD,CapMVRVCur",
        "frequency": "1d",
        "limit_per_asset": 1825  # 5 Years
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url_cm, params=params, headers=headers).json()
    
    df = pd.DataFrame(res['data'])
    df['date'] = pd.to_datetime(df['time'])
    df['close'] = df['PriceUSD'].astype(float)
    df['mvrv'] = df['CapMVRVCur'].astype(float)
    
    # Calculate the 200 Simple Moving Average over the 5-year dataset
    df['MA200'] = df['close'].rolling(200).mean()
    return df.dropna()

# 2. Fear & Greed (Alternative.me - Historical sentiment is limited by API, shows current state)
@st.cache_data(ttl=3600)
def get_fng():
    res = requests.get("https://api.alternative.me/fng/?limit=1").json()['data'][0]
    return res['value'], res['value_classification']

# Execute Fetchers
df_data = get_price()
fng_val, fng_class = get_fng()

# Build the UI Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("5-Year Price & 200 MA Macro View")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_data['date'], y=df_data['close'], name='BTC Price', line=dict(color='#2962FF')))
    fig1.add_trace(go.Scatter(x=df_data['date'], y=df_data['MA200'], name='MA200', line=dict(color='#FF6D00')))
    fig1.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("5-Year MVRV Ratio (Valuation Bands)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_data['date'], y=df_data['mvrv'], name='MVRV', line=dict(color='#00E676')))
    # Adding macro reference lines for investment management (e.g., historical undervaluation / overvaluation zones)
    fig2.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Realized Value Baseline (1.0)")
    fig2.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.subheader("Sentiment")
    st.metric(label="Fear & Greed Index", value=fng_val, delta=fng_class, delta_color="off")
