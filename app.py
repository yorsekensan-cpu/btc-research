import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="BTC Analytics", layout="wide")
st.title("Bitcoin Investment Dashboard")
st.caption("On-chain valuation + technical regime dashboard. Not financial advice — use as one input among many.")

# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_data():
    """
    All fields pulled here are on CoinMetrics' free Community API tier
    (no key required): PriceUSD, CapMVRVCur, CapMrktCurUSD, CapRealUSD, IssContUSD.
    Pulling full history since 2013 because Z-scores / percentiles are meaningless
    on a 365-day window.
    """
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {
        "assets": "btc",
        "metrics": "PriceUSD,CapMVRVCur,CapMrktCurUSD,CapRealUSD,IssContUSD",
        "frequency": "1d",
        "start_time": "2013-01-01",
        "page_size": 10000,
    }
    res = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}).json()
    df = pd.DataFrame(res["data"])
    df["date"] = pd.to_datetime(df["time"])

    for col in ["PriceUSD", "CapMVRVCur", "CapMrktCurUSD", "CapRealUSD", "IssContUSD"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.rename(columns={"PriceUSD": "close"}).sort_values("date").reset_index(drop=True)

    # --- Technicals (computed locally, no extra API calls) ---
    df["MA200"] = df["close"].rolling(200).mean()
    df["MA111"] = df["close"].rolling(111).mean()
    df["MA350x2"] = df["close"].rolling(350).mean() * 2  # Pi Cycle Top upper leg

    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["RSI14"] = 100 - (100 / (1 + rs))

    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    upper_bb = ma20 + 2 * std20
    lower_bb = ma20 - 2 * std20
    df["BB_pctB"] = (df["close"] - lower_bb) / (upper_bb - lower_bb)

    # --- On-chain valuation metrics ---
    df["mvrv"] = df["CapMVRVCur"]

    diff = df["CapMrktCurUSD"] - df["CapRealUSD"]
    exp_mean = diff.expanding(min_periods=365).mean()
    exp_std = diff.expanding(min_periods=365).std()
    df["mvrv_z"] = (diff - exp_mean) / exp_std

    df["nupl"] = (df["CapMrktCurUSD"] - df["CapRealUSD"]) / df["CapMrktCurUSD"]

    df["puell"] = df["IssContUSD"] / df["IssContUSD"].rolling(365).mean()

    return df


@st.cache_data(ttl=3600)
def get_fng():
    res = requests.get("https://api.alternative.me/fng/?limit=1").json()["data"][0]
    return int(res["value"]), res["value_classification"]


df = get_data()
fng_val, fng_class = get_fng()
latest = df.iloc[-1]

# ---------------------------------------------------------------------------
# SIGNAL LOGIC — thresholds are the commonly cited historical zones for each
# metric. They describe past cycle behavior, not guarantees of future behavior.
# ---------------------------------------------------------------------------

def zone(value, low, high, invert=False):
    """Return (label, color) — green=buy zone, red=sell zone, gray=neutral."""
    if pd.isna(value):
        return "N/A", "gray"
    if not invert:
        if value <= low:
            return "BUY ZONE", "green"
        if value >= high:
            return "SELL ZONE", "red"
        return "NEUTRAL", "gray"
    else:
        if value <= low:
            return "SELL ZONE", "red"
        if value >= high:
            return "BUY ZONE", "green"
        return "NEUTRAL", "gray"


signals = {
    "MVRV Z-Score": zone(latest["mvrv_z"], 0, 7),
    "NUPL": zone(latest["nupl"], 0, 0.75),
    "Puell Multiple": zone(latest["puell"], 0.5, 4),
    "RSI (14)": zone(latest["RSI14"], 30, 70),
    "Bollinger %B": zone(latest["BB_pctB"], 0, 1),
    "Fear & Greed": zone(fng_val, 25, 75),
    "Pi Cycle Top": ("SELL ZONE", "red") if latest["MA111"] > latest["MA350x2"] else ("NEUTRAL", "gray"),
}

descriptions = {
    "MVRV Z-Score": (
        "(Market Cap − Realized Cap) scaled by historical volatility. Realized cap "
        "values every coin at the price it last moved, so this compares 'what the "
        "market says it's worth' to 'what holders actually paid.' Z above ~7 has "
        "coincided with every major cycle top since 2013; Z below 0 has coincided "
        "with every major cycle bottom. Best for macro positioning, not entries/exits."
    ),
    "NUPL": (
        "Net Unrealized Profit/Loss — the % of market cap currently sitting in profit "
        "across all coins. Above 0.75 = euphoria, most holders sitting on large gains "
        "and prone to sell into strength. Below 0 = capitulation, majority underwater, "
        "historically a bottoming signal. 0–0.25 is the 'hope/fear' accumulation range."
    ),
    "Puell Multiple": (
        "Daily miner revenue (USD) divided by its 365-day average. Miners are "
        "structurally forced sellers to cover costs. Below 0.5 = miners under-earning, "
        "selling less/at a loss — historically a strong accumulation zone. Above 4 = "
        "miners in abnormal profit, often coincides with blow-off tops."
    ),
    "RSI (14)": (
        "Standard 14-day momentum oscillator on price. Above 70 = short-term "
        "overbought/exhausted. Below 30 = short-term oversold. Good for timing "
        "entries/exits inside a trend already confirmed by the metrics above — weak "
        "as a standalone macro signal since it can stay overbought for months in a bull run."
    ),
    "Bollinger %B": (
        "Where price sits relative to its 20-day volatility bands. Above 1 = price has "
        "broken above the upper band (statistically stretched, mean-reversion risk). "
        "Below 0 = broken below the lower band (statistically stretched down, bounce risk)."
    ),
    "Fear & Greed": (
        "Aggregate sentiment index (volatility, momentum, social media, surveys, "
        "dominance). Extreme Greed (75+) tends to precede pullbacks. Extreme Fear "
        "(25 or below) has historically been a contrarian buy signal."
    ),
    "Pi Cycle Top": (
        "Fires when the 111-day MA crosses above 2x the 350-day MA. A purely "
        "price-based signal that has flagged every major cycle top since 2013 within "
        "days, with no historical false positives on the top side. It only calls tops, "
        "never bottoms."
    ),
}

# ---------------------------------------------------------------------------
# LAYOUT — summary matrix first
# ---------------------------------------------------------------------------

buy_count = sum(1 for label, _ in signals.values() if label == "BUY ZONE")
sell_count = sum(1 for label, _ in signals.values() if label == "SELL ZONE")

if sell_count >= 4:
    verdict, verdict_color = "MAJORITY OF SIGNALS IN SELL ZONE", "red"
elif buy_count >= 4:
    verdict, verdict_color = "MAJORITY OF SIGNALS IN BUY ZONE", "green"
else:
    verdict, verdict_color = "MIXED / NEUTRAL REGIME", "gray"

st.markdown(
    f"<h4 style='color:{verdict_color}'>Composite read: {verdict} "
    f"({buy_count} buy-zone / {sell_count} sell-zone / {7 - buy_count - sell_count} neutral)</h4>",
    unsafe_allow_html=True,
)

cols = st.columns(7)
metric_values = {
    "MVRV Z-Score": f"{latest['mvrv_z']:.2f}",
    "NUPL": f"{latest['nupl']:.2f}",
    "Puell Multiple": f"{latest['puell']:.2f}",
    "RSI (14)": f"{latest['RSI14']:.1f}",
    "Bollinger %B": f"{latest['BB_pctB']:.2f}",
    "Fear & Greed": f"{fng_val} ({fng_class})",
    "Pi Cycle Top": "TRIGGERED" if latest["MA111"] > latest["MA350x2"] else "not triggered",
}
for c, (name, (label, color)) in zip(cols, signals.items()):
    with c:
        st.markdown(f"**{name}**")
        st.markdown(f"<span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
        st.caption(metric_values[name])

st.divider()

# ---------------------------------------------------------------------------
# PRICE + PI CYCLE TOP
# ---------------------------------------------------------------------------

st.subheader("Price, 200MA & Pi Cycle Top")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df["date"], y=df["close"], name="BTC Price", line=dict(color="#2962FF")))
fig1.add_trace(go.Scatter(x=df["date"], y=df["MA200"], name="200 DMA", line=dict(color="#FF6D00")))
fig1.add_trace(go.Scatter(x=df["date"], y=df["MA111"], name="111 DMA", line=dict(color="#AA00FF", dash="dot")))
fig1.add_trace(go.Scatter(x=df["date"], y=df["MA350x2"], name="350 DMA x2", line=dict(color="#D50000", dash="dot")))
fig1.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark", yaxis_type="log")
st.plotly_chart(fig1, use_container_width=True)
with st.expander("What is Pi Cycle Top / how to read this chart"):
    st.write(descriptions["Pi Cycle Top"])

st.divider()

# ---------------------------------------------------------------------------
# ON-CHAIN VALUATION ROW
# ---------------------------------------------------------------------------

c1, c2 = st.columns(2)

with c1:
    st.subheader("MVRV Z-Score")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["mvrv_z"], name="MVRV Z-Score", line=dict(color="#00E676")))
    fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="Sell zone (7)")
    fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Buy zone (0)")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read MVRV Z-Score"):
        st.write(descriptions["MVRV Z-Score"])

with c2:
    st.subheader("NUPL")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["nupl"], name="NUPL", line=dict(color="#00B8D4")))
    fig.add_hline(y=0.75, line_dash="dash", line_color="red", annotation_text="Euphoria (0.75)")
    fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Capitulation (0)")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read NUPL"):
        st.write(descriptions["NUPL"])

c3, c4 = st.columns(2)

with c3:
    st.subheader("Puell Multiple")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["puell"], name="Puell Multiple", line=dict(color="#FFD600")))
    fig.add_hline(y=4, line_dash="dash", line_color="red", annotation_text="Miner euphoria (4)")
    fig.add_hline(y=0.5, line_dash="dash", line_color="green", annotation_text="Miner capitulation (0.5)")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read Puell Multiple"):
        st.write(descriptions["Puell Multiple"])

with c4:
    st.subheader("MVRV (raw ratio)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["mvrv"], name="MVRV", line=dict(color="#00E676")))
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Fair value (1.0)")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read raw MVRV"):
        st.write(
            "Market Cap / Realized Cap. Above 1 = average holder in profit, below 1 = "
            "average holder underwater. Simpler but noisier version of the Z-score above; "
            "kept here mainly for direct comparison against the Z-score."
        )

st.divider()

# ---------------------------------------------------------------------------
# TECHNICAL / SENTIMENT ROW
# ---------------------------------------------------------------------------

c5, c6 = st.columns(2)

with c5:
    st.subheader("RSI (14)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14", line=dict(color="#FF6D00")))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read RSI(14)"):
        st.write(descriptions["RSI (14)"])

with c6:
    st.subheader("Bollinger %B")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["BB_pctB"], name="%B", line=dict(color="#AA00FF")))
    fig.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Upper band (1)")
    fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="Lower band (0)")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("How to read Bollinger %B"):
        st.write(descriptions["Bollinger %B"])

st.subheader("Market Sentiment")
sc1, sc2 = st.columns([1, 3])
with sc1:
    st.metric(label="Fear & Greed Index", value=fng_val, delta=fng_class, delta_color="off")
with sc2:
    st.write(descriptions["Fear & Greed"])
