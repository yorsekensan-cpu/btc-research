import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio Allocator", layout="wide")

st.title("⚖️ Dynamic Portfolio Allocator")
st.caption("Live valuation and algorithmic risk profiling.")

# --- 1. THE MASTER REGISTRY ---
# To add future assets, simply add a new line here!
ASSET_REGISTRY = {
    "BTC-USD": {"name": "Bitcoin", "class": "Crypto", "currency": "USD"},
    "BBCA.JK": {"name": "Bank Central Asia", "class": "Equity", "currency": "IDR"},
    "ADRO.JK": {"name": "Adaro Energy", "class": "Equity", "currency": "IDR"}
}

# --- 2. LIVE DATA ENGINE ---
@st.cache_data(ttl=120)
def fetch_live_valuations():
    try:
        # Fetch all registered assets PLUS the USD/IDR exchange rate
        tickers = list(ASSET_REGISTRY.keys()) + ["IDR=X"]
        df = yf.download(tickers, period="1d", progress=False)['Close']
        
        # Handle single vs multi-index returns safely
        if isinstance(df.columns, pd.MultiIndex):
            df = df.iloc[-1].droplevel(1)
        else:
            df = df.iloc[-1]
            
        return df.to_dict()
    except Exception:
        return {}

live_prices = fetch_live_valuations()

if not live_prices:
    st.error("⚠️ Failed to fetch market data. Please check your connection or Yahoo Finance status.")
    st.stop()

# Ensure we have the FX rate for USD conversion
usd_idr_rate = live_prices.get("IDR=X", 15500.0) # Fallback rate if FX fails

# --- 3. DYNAMIC INPUT UI ---
st.subheader("Asset Holdings")
st.markdown("Enter your current unit holdings for each asset:")

user_holdings = {}
cols = st.columns(len(ASSET_REGISTRY))

# Dynamically generate input fields based on the registry
for idx, (ticker, details) in enumerate(ASSET_REGISTRY.items()):
    with cols[idx]:
        # Using min_value=0.0 and value=0.0 forces floats, preventing the MixedNumericTypesError
        units = st.number_input(f"{details['name']} ({ticker})", min_value=0.0, value=0.0, step=0.01, format="%.4f")
        user_holdings[ticker] = units

st.divider()

# --- 4. VALUATION ALGORITHM ---
total_value_idr = 0.0
class_totals = {"Crypto": 0.0, "Equity": 0.0}
portfolio_breakdown = []

for ticker, details in ASSET_REGISTRY.items():
    units = user_holdings[ticker]
    price = live_prices.get(ticker, 0.0)
    
    # Convert USD assets to Base Currency (IDR)
    if details["currency"] == "USD":
        value_idr = units * price * usd_idr_rate
    else:
        value_idr = units * price
        
    total_value_idr += value_idr
    class_totals[details["class"]] += value_idr
    
    if value_idr > 0:
        portfolio_breakdown.append({
            "Asset": details['name'],
            "Class": details['class'],
            "Value (IDR)": value_idr
        })

# --- 5. RISK PROFILING ---
if total_value_idr > 0:
    crypto_weight = (class_totals["Crypto"] / total_value_idr) * 100
    equity_weight = (class_totals["Equity"] / total_value_idr) * 100
    
    if crypto_weight <= 15:
        profile = "CONSERVATIVE 🛡️"
        desc = "Your portfolio is heavily anchored in traditional cash-flow equities. Low risk of systemic ruin."
        p_color = "normal"
    elif crypto_weight <= 40:
        profile = "BALANCED ⚖️"
        desc = "Standard institutional risk curve. Healthy mix of aggressive upside (Web3/Macro) and domestic stability."
        p_color = "off"
    else:
        profile = "AGGRESSIVE 🚀"
        desc = "High volatility exposure. Portfolio valuation will swing violently based on global macro liquidity."
        p_color = "inverse"

    # --- 6. RENDER DASHBOARD ---
    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    col_metrics1.metric("Total Net Worth (IDR)", f"Rp{total_value_idr:,.0f}")
    col_metrics2.metric("Crypto Exposure", f"{crypto_weight:.1f}%")
    col_metrics3.metric("Assigned Risk Profile", profile, delta_color=p_color)
    
    st.info(f"**Manager's Note:** {desc}")
    
    st.divider()
    
    # Visual Breakdown
    st.subheader("Capital Allocation")
    
    col_chart, col_table = st.columns([1.5, 1])
    
    with col_chart:
        df_viz = pd.DataFrame(portfolio_breakdown)
        fig = go.Figure(data=[go.Pie(labels=df_viz['Asset'], values=df_viz['Value (IDR)'], hole=.4, textinfo='label+percent')])
        fig.update_layout(template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0), height=350)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_table:
        st.dataframe(df_viz.style.format({"Value (IDR)": "Rp{:,.0f}"}), hide_index=True, use_container_width=True)
        
else:
    st.warning("Enter your asset units above to generate your quantitative risk profile.")
