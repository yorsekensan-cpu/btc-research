import streamlit as st

st.set_page_config(page_title="Investment Dashboard", layout="wide")

# Register your pages cleanly
home_page = st.Page("pages/home.py", title="Command Center", icon="🏠")
btc_page = st.Page("pages/btc_macro.py", title="BTC", icon="📊")
bbca_page = st.Page("pages/bbca_matrix.py", title="BBCA", icon="🏦")
adro_page = st.Page("pages/adro_matrix.py", title="ADRO", icon="⛏️")
allocator_page = st.Page("pages/portofolio_allocator.py", title="Portfolio Allocator", icon="⚖️")

# Pass only the modular pages into the router
pg = st.navigation([home_page, btc_page, bbca_page, adro_page, allocator_page])
pg.run()
