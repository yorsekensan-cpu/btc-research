import streamlit as st

st.set_page_config(page_title="Investment Dashboard", layout="wide")

btc_macro_page = st.Page("pages/btc_macro.py", title="BTC Macro Dashboard", icon="📊", default=True)
bbca_matrix_page = st.Page("pages/bbca_matrix.py", title="BBCA Equity Matrix", icon="🏦")

pg = st.navigation([btc_macro_page, bbca_matrix_page])
pg.run()
