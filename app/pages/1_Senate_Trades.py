import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.database.connection import get_session
from src.database.crud import get_congress_trades
from app.components.charts import bar_senator_activity
from app.components.tables import style_congress_trades

st.set_page_config(page_title="Senate Trades", page_icon="🏛️", layout="wide")
st.title("🏛️ Senate & Congress Trades")

# ── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    days = st.slider("Show last N days", 7, 365, 60)
    tx_types = st.multiselect(
        "Transaction type",
        ["Purchase", "Sale", "Exchange"],
        default=["Purchase", "Sale"],
    )
    ticker_search = st.text_input("Ticker search", placeholder="e.g. NVDA")

session = get_session()
df = get_congress_trades(
    session,
    days=days,
    transaction_types=tx_types if tx_types else None,
    ticker=ticker_search or None,
)
session.close()

# ── Member filter (dynamic based on query result) ────────────────────────────
if not df.empty:
    all_members = sorted(df["member_name"].dropna().unique().tolist())
    selected_members = st.sidebar.multiselect("Members", all_members)
    if selected_members:
        df = df[df["member_name"].isin(selected_members)]

    party_filter = st.sidebar.multiselect("Party", ["R", "D", "I"])
    if party_filter:
        df = df[df["party"].isin(party_filter)]

# ── Metrics row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
if not df.empty:
    month_ago = date.today() - timedelta(days=30)
    this_month = df[pd.to_datetime(df["disclosure_date"]).dt.date >= month_ago]

    col1.metric("Trades this month", len(this_month))
    col2.metric("Unique tickers", df["ticker"].dropna().nunique())
    col3.metric(
        "Most active",
        df["member_name"].value_counts().idxmax() if len(df) else "—",
    )
    avg_days = df["days_to_disclose"].dropna().mean()
    col4.metric("Avg days to disclose", f"{avg_days:.0f}" if pd.notna(avg_days) else "—")
else:
    col1.metric("Trades this month", 0)
    col2.metric("Unique tickers", 0)
    col3.metric("Most active", "—")
    col4.metric("Avg days to disclose", "—")

st.markdown("---")

# ── Chart ─────────────────────────────────────────────────────────────────────
if not df.empty:
    st.plotly_chart(bar_senator_activity(df), use_container_width=True)
else:
    st.info("No data yet. Run `python scripts/init_db.py` to fetch trades.")

# ── Trade table ────────────────────────────────────────────────────────────────
st.subheader("Trade Feed")
if df.empty:
    st.warning("No trades match the current filters.")
else:
    # Friendly column names for display
    display = df.rename(columns={
        "member_name":      "Member",
        "party":            "Party",
        "state":            "State",
        "ticker":           "Ticker",
        "asset_name":       "Asset",
        "transaction_type": "Action",
        "amount_range":     "Amount Range",
        "transaction_date": "Trade Date",
        "disclosure_date":  "Disclosed",
        "days_to_disclose": "Days Late",
    })
    cols = ["Member","Party","State","Ticker","Asset","Action","Amount Range","Trade Date","Disclosed","Days Late"]
    cols = [c for c in cols if c in display.columns]
    st.dataframe(display[cols], use_container_width=True, height=500)

    late = df[df["days_to_disclose"].fillna(0) > 45]
    if not late.empty:
        st.warning(f"⚠️ {len(late)} trade(s) disclosed more than 45 days after the transaction date.")
