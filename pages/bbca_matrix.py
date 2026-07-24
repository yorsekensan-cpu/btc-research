import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="BBCA Matrix", layout="wide")

st.title("🏦 Bank Central Asia (BBCA.JK) Equity Matrix")
st.caption("Quantitative Regime and Momentum Tracking")

# --- 1. SAFE DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_bbca_data():
    try:
        # Fetch 2 years to ensure the 200 DMA calculates correctly
        df = yf.download("BBCA.JK", period="2y", progress=False)
        
        if not df.empty and isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        return df
    except Exception:
        return pd.DataFrame()

df = fetch_bbca_data()

if df.empty or len(df) < 200:
    st.warning("⚠️ Market data provider (yfinance) is temporarily busy or returning incomplete data. Please refresh in a few moments.")
    st.stop()

# --- 2. CALCULATE INDICATORS ---
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
df["Upper_BB"] = ma20 + (2 * std20)
df["Lower_BB"] = ma20 - (2 * std20)
df["BB_pctB"] = (df["Close"] - df["Lower_BB"]) / (df["Upper_BB"] - df["Lower_BB"])

clean_df = df.dropna()

if clean_df.empty:
    st.warning("⚠️ Calculating technicals... Waiting for complete data history.")
    st.stop()

latest = clean_df.iloc[-1]

# --- 3. SCORING REGIME LOGIC ---
buy_count, sell_count = 0, 0

if latest["MA50"] > latest["MA200"]:
    trend_status, trend_signal = "BULLISH", "🟢 BUY"
    buy_count += 1 
else: 
    trend_status, trend_signal = "BEARISH", "🔴 SELL"
    sell_count += 1

# Standard compounding bank threshold (tighter than cyclical assets)
if latest["pct_vs_200ma"] <= -5:
    pct_status, pct_signal = "DEEP DISCOUNT", "🟢 BUY"
    buy_count += 1
elif latest["pct_vs_200ma"] >= 10:
    pct_status, pct_signal = "OVEREXTENDED", "🔴 SELL"
    sell_count += 1
else:
    pct_status, pct_signal = "NEUTRAL", "⚪ HOLD"

if latest["RSI14"] <= 35:
    rsi_status, rsi_signal = "OVERSOLD", "🟢 BUY"
    buy_count += 1
elif latest["RSI14"] >= 70:
    rsi_status, rsi_signal = "OVERBOUGHT", "🔴 SELL"
    sell_count += 1
else:
    rsi_status, rsi_signal = "NEUTRAL", "⚪ HOLD"

if latest["BB_pctB"] <= 0:
    bb_status, bb_signal = "BELOW LOWER BAND", "🟢 BUY"
    buy_count += 1
elif latest["BB_pctB"] >= 1:
    bb_status, bb_signal = "ABOVE UPPER BAND", "🔴 SELL"
    sell_count += 1
else:
    bb_status, bb_signal = "WITHIN BANDS", "⚪ HOLD"

# Requires 3 out of 4 indicators to trigger a strong regime shift
if buy_count >= 3:
    verdict = "ACCUMULATION ZONE"
    color = "normal"
elif sell_count >= 3:
    verdict = "DISTRIBUTION ZONE"
    color = "inverse"
else:
    verdict = "NEUTRAL REGIME"
    color = "off"

# --- 4. DASHBOARD UI & RECOMMENDATION ---
st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Live Price", f"Rp{latest['Close']:,.0f}")
col2.metric("Trend (50 vs 200)", trend_status)
col3.metric("% vs 200 DMA", f"{latest['pct_vs_200ma']:+.2f}%")
col4.metric("RSI (14)", f"{latest['RSI14']:.1f}")

st.divider()

st.subheader("Algorithmic Recommendation")
if verdict == "ACCUMULATION ZONE":
    st.success(f"**🟢 {verdict}:** BBCA is exhibiting rare structural weakness. This presents a high-probability entry point for long-term compounding.")
elif verdict == "DISTRIBUTION ZONE":
    st.error(f"**🔴 {verdict}:** BBCA is technically overextended compared to its historical mean. Consider holding off on new capital deployment until a pullback occurs.")
else:
    st.info(f"**⚪ {verdict}:** BBCA is compounding steadily within normal structural bounds. Maintain current holdings and collect dividends.")

with st.expander("📊 View Detailed Indicator Breakdown", expanded=False):
    matrix_data = {
        "Indicator": ["Trend (50 vs 200 DMA)", "Deviation from 200 DMA", "RSI (14)", "Bollinger %B"],
        "Current Value": [f"50DMA: Rp{latest['MA50']:,.0f}", f"{latest['pct_vs_200ma']:+.2f}%", f"{latest['RSI14']:.1f}", f"{latest['BB_pctB']:.2f}"],
        "Condition": [trend_status, pct_status, rsi_status, bb_status],
        "Signal": [trend_signal, pct_signal, rsi_signal, bb_signal]
    }
    st.table(pd.DataFrame(matrix_data))

st.divider()

# --- 5. TIMEFRAME SELECTOR & INTERACTIVE CHARTS ---
st.subheader("Price Action & Moving Averages")

timeframe = st.radio(
    "Select Chart Timeframe:",
    ["3 Months", "6 Months", "1 Year", "2 Years"],
    horizontal=True,
    index=3
)

end_date = clean_df.index.max()
if timeframe == "3 Months":
    start_date = end_date - pd.DateOffset(months=3)
elif timeframe == "6 Months":
    start_date = end_date - pd.DateOffset(months=6)
elif timeframe == "1 Year":
    start_date = end_date - pd.DateOffset(years=1)
else:
    start_date = clean_df.index.min()

plot_df = clean_df[clean_df.index >= start_date]

# Main Price Chart
fig_price = go.Figure()
fig_price.add_trace(go.Candlestick(x=plot_df.index, open=plot_df['Open'], high=plot_df['High'], low=plot_df['Low'], close=plot_df['Close'], name='BBCA Price'))
fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA50'], line=dict(color='orange', width=1.5), name='50-Day MA'))
fig_price.add_trace(go.Scatter(x=plot_df.index, y=plot_df['MA200'], line=dict(color='blue', width=2), name='200-Day MA'))
fig_price.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500, margin=dict(l=10, r=10, t=30, b=10))
fig_price.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
st.plotly_chart(fig_price, use_container_width=True)

# Sub-Charts
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Relative Strength Index (RSI)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=plot_df.index, y=plot_df['RSI14'], line=dict(color='purple', width=2), name='RSI (14)'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=35, line_dash="dash", line_color="green", annotation_text="Oversold (35)")
    fig_rsi.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=30, b=10))
    fig_rsi.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    st.plotly_chart(fig_rsi, use_container_width=True)

with col_chart2:
    st.subheader("Bollinger Bands")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Upper_BB'], line=dict(color='gray', dash='dot'), name='Upper Band'))
    fig_bb.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Lower_BB'], line=dict(color='gray', dash='dot'), fill='tonexty', fillcolor='rgba(128, 128, 128, 0.2)', name='Lower Band'))
    fig_bb.add_trace(go.Scatter(x=plot_df.index, y=plot_df['Close'], line=dict(color='white', width=1.5), name='Price'))
    fig_bb.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=30, b=10))
    fig_bb.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    st.plotly_chart(fig_bb, use_container_width=True)

# --- 6. MACRO RESEARCH EXPANDER ---
with st.expander("View Manager's Research Thesis"):
    st.markdown("""
    **The Compounding Nature of BBCA:**
    Unlike highly cyclical assets, Bank Central Asia (BBCA) is evaluated as a structural compounder driven by credit growth and net interest margins (NIM). 
    *   **The 200 DMA Rule:** BBCA rarely breaks below its 200-day moving average during normal economic conditions. A deviation of -5% or more signals a rare systemic discount and a high-conviction accumulation zone.
    *   **Low Volatility Profile:** Momentum metrics (like RSI and Bollinger Bands) act as short-term timing tools for capital deployment, rather than structural exit signals.
    """)
