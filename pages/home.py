# ==========================================
# 🔵 IDX EQUITIES SECTION
# ==========================================
import streamlit as st
import yfinance as yf
import pandas as pd

# The rest of your code follows...
st.divider()

col4, col5, col6 = st.columns([1, 8, 3])
with col4:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830284.png", width=40)
with col5:
    st.subheader("IDX Equities")
with col6:
    # Stacking them vertically by removing the nested st.columns()
    if bbca_price:
        st.metric(label="BBCA", value=f"Rp{bbca_price:,.0f}")
    else:
        st.metric(label="BBCA", value="Loading...")
        
    if adro_price:
        st.metric(label="ADRO", value=f"Rp{adro_price:,.0f}")
    else:
        st.metric(label="ADRO", value="Loading...")

st.page_link("pages/bbca_matrix.py", label="Bank Central Asia (BBCA.JK) Equity Matrix", icon="🏦")
st.page_link("pages/adro_matrix.py", label="Adaro Energy (ADRO.JK) Cyclical Matrix", icon="⛏️")
