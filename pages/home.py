import streamlit as st

st.set_page_config(page_title="Market Dashboard", layout="wide")

st.title("Market Intelligence Dashboard")
st.caption("Quantitative regime monitoring.")

# --- PORTFOLIO ALLOCATOR REMOVED ---
# (The code block that used to be here is now deleted)

# ==========================================
# 🟢 CRYPTO ECOSYSTEM SECTION
# ==========================================
st.divider()

# Adding Logo and Header side-by-side
col1, col2 = st.columns([1, 20])
with col1:
    # Standard transparent BTC logo URL
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=40)
with col2:
    st.subheader("Crypto Assets")

# Your BTC Macro navigation link or content goes here
st.page_link("pages/btc_macro.py", label="Bitcoin (BTC) Macro Regime", icon="📈")

# Adding Crypto Sentiment Logo and Header
col3, col4 = st.columns([1, 20])
with col3:
    # Standard sentiment/gauge icon URL
    st.image("https://cdn-icons-png.flaticon.com/512/3563/3563391.png", width=40)
with col4:
    st.subheader("Crypto Sentiment")

# Your Sentiment navigation link or content goes here
st.write("Fear & Greed Index Dashboard")


# ==========================================
# 🔵 IDX EQUITIES SECTION
# ==========================================
st.divider()

col5, col6 = st.columns([1, 20])
with col5:
    # Standard banking/IDX logo placeholder
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=40)
with col6:
    st.subheader("IDX Equities")

# Your BBCA Matrix navigation link or content goes here
st.page_link("pages/bbca_matrix.py", label="Bank Central Asia (BBCA.JK) Equity Matrix", icon="🏦")
