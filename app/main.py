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
st.title("🏦 Smart Money Tracker")
st.markdown("### Professional Dashboard for Institutional & Congress Trades")

# Dynamic Metrics Calculation
import os
import datetime

def get_next_13f_deadline():
    today = datetime.date.today()
    year = today.year
    deadlines = [
        datetime.date(year, 2, 14),
        datetime.date(year, 5, 15),
        datetime.date(year, 8, 14),
        datetime.date(year, 11, 14)
    ]
    for d in deadlines:
        if d >= today:
            return d.strftime("%B %d, %Y")
    return datetime.date(year + 1, 2, 14).strftime("%B %d, %Y")

db_path = os.path.join(os.path.dirname(__file__), "..", "data", "tracker.db")
last_updated = "Never (Empty DB)"
if os.path.exists(db_path):
    size_kb = os.path.getsize(db_path) / 1024
    if size_kb > 100: # Ensure it's not just an empty table schema
        mtime = os.path.getmtime(db_path)
        last_updated = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

col1, col2, col3 = st.columns(3)
col1.metric("Last Database Update", last_updated)
col2.metric("Next SEC 13F Deadline", get_next_13f_deadline())
col3.metric("Tracked Institutions", "18 Top Tier")

st.markdown("---")

st.markdown(
    """
Track investment patterns from **US Congress members** (STOCK Act disclosures)
and **institutional fund managers** (SEC 13F filings).

Use the sidebar to navigate between pages.

| Page | What you'll find |
|---|---|
| 🏛️ **Senate Trades** | Real-time STOCK Act purchase/sale feed |
| 🐋 **Fund Tracker** | 13F holdings and quarter-over-quarter changes |
| 🎯 **Signals** | Cross-referenced conviction scores |
| 👀 **My Watchlist** | Activity alerts for your personal tickers |
    """
)
