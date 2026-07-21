import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests  # <-- Added to handle custom sessions

st.title("Bank Central Asia (BBCA.JK) Equity Matrix")
st.caption("Quantitative regime matrix tailored specifically for BBCA.JK.")

TICKER = "BBCA.JK"

@st.cache_data(ttl=3600)
def get_bbca_data():
    # 1. Create a custom session to bypass Yahoo Finance cloud blocks
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    })
    
    # 2. Pass the session into yfinance
    df = yf.download(TICKER, period="3y", progress=False, session=session)
    
    if df.empty:
        return pd.DataFrame()
        
    # Flatten yfinance multi-index if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date", "Close": "close", "Volume": "volume"}, inplace=True)
    
    # 1. Moving Averages
    df["MA50"] = df["close"].rolling(50).mean()
    df["MA200"] = df["close"].rolling(200).mean()
    df["pct_vs_200ma"] = (df["close"] / df["MA200"] - 1) * 100
    
    # 2. RSI (14)
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["RSI14"] = 100 - (100 / (1 + rs))
    
    # 3. Bollinger Bands (%B)
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    upper_bb = ma20 + (2 * std20)
    lower_bb = ma20 - (2 * std20)
    df["BB_pctB"] = (df["close"] - lower_bb) / (upper_bb - lower_bb)
    
    return df.dropna().reset_index(drop=True)

df = get_bbca_data()

if df.empty:
    st.error("Failed to fetch BBCA.JK market data. Please check back shortly.")
else:
    latest = df.iloc[-1]
    
    def score_metric(val, buy_thresh, sell_thresh, invert=False):
        if pd.isna(val): return "N/A", "gray"
        if not invert:
            if val <= buy_thresh: return "BUY ZONE", "green"
            if val >= sell_thresh: return "SELL ZONE", "red"
            return "NEUTRAL", "gray"
        else:
            if val <= buy_thresh: return "SELL ZONE", "red"
            if val >= sell_thresh: return "BUY ZONE", "green"
            return "NEUTRAL", "gray"

    # Regime scoring tailored for blue-chip equity volatility (-5% to +10%)
    signals = {
        "Trend (50 vs 200)": ("BULLISH", "green") if latest["MA50"] > latest["MA200"] else ("BEARISH", "red"),
        "% vs 200 DMA": score_metric(latest["pct_vs_200ma"], -5, 10), 
        "RSI (14)": score_metric(latest["RSI14"], 35, 70),
        "Bollinger %B": score_metric(latest["BB_pctB"], 0, 1)
    }

    st.subheader("Current Read")
    cols = st.columns(len(signals))
    metric_values = {
        "Trend (50 vs 200)": f"50MA: Rp{latest['MA50']:,.0f} | 200MA: Rp{latest['MA200']:,.0f}",
        "% vs 200 DMA": f"{latest['pct_vs_200ma']:+.2f}%",
        "RSI (14)": f"{latest['RSI14']:.1f}",
        "Bollinger %B": f"{latest['BB_pctB']:.2f}"
    }
    
    for c, (name, (label, color)) in zip(cols, signals.items()):
        with c:
            st.markdown(f"**{name}**")
            st.markdown(f"<span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
            st.caption(metric_values[name])

    st.divider()

    # --- CHARTS ---
    st.subheader("Price & Moving Averages")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["date"], y=df["close"], name="BBCA Close", line=dict(color="#2962FF")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["MA50"], name="50 DMA", line=dict(color="#00E676", dash="dot")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["MA200"], name="200 DMA", line=dict(color="#FF6D00")))
    fig1.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI", line=dict(color="#FF6D00")))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=35, line_dash="dash", line_color="green")
        fig_rsi.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
        st.plotly_chart(fig_rsi, use_container_width=True)

    with c2:
        st.subheader("% vs 200 DMA")
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Scatter(x=df["date"], y=df["pct_vs_200ma"], name="% dist", line=dict(color="#00E676")))
        fig_dist.add_hline(y=10, line_dash="dash", line_color="red")
        fig_dist.add_hline(y=-5, line_dash="dash", line_color="green")
        fig_dist.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
        st.plotly_chart(fig_dist, use_container_width=True)
