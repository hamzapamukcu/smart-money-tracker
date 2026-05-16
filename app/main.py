"""
Smart Money Tracker — Streamlit entry point.

Run with:  streamlit run app/main.py
"""
import sys
import os
import atexit

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from src.database.connection import init_db

# Ensure database tables exist before rendering pages
init_db()

st.set_page_config(
    page_title="Smart Money Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)



# Sidebar
with st.sidebar:
    st.title("💰 Smart Money Tracker")
    st.caption("Track congress & fund positions in real time.")
    st.markdown("---")
    st.markdown(
        """
**Pages**
- Senate Trades
- Fund Tracker
- Signals
- My Watchlist
        """
    )
    st.markdown("---")
    if st.button("🔄 Refresh Data Now"):
        with st.spinner("Running data pipeline…"):
            from src.collectors.senate import fetch_senate_trades
            from src.collectors.edgar import fetch_all_13f_filings
            from src.processors.diff_13f import compute_all_diffs
            from src.processors.signals import compute_signals
            fetch_senate_trades()
            fetch_all_13f_filings()
            compute_all_diffs(rebuild=True)
            compute_signals(rebuild=True)
        st.success("Data refreshed!")

# Landing page content
st.title("Smart Money Tracker")
st.markdown(
    """
Track investment patterns from **US Congress members** (STOCK Act disclosures)
and **institutional fund managers** (SEC 13F filings).

Use the sidebar to navigate between pages.

| Page | What you'll find |
|---|---|
| **Senate Trades** | Real-time STOCK Act purchase/sale feed |
| **Fund Tracker** | 13F holdings and quarter-over-quarter changes |
| **Signals** | Cross-referenced conviction scores |
| **My Watchlist** | Activity alerts for your personal tickers |
    """
)
