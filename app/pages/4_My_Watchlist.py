import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.database.connection import get_session
from src.database.crud import get_congress_trades, get_fund_diffs, get_signals
from config.watchlists import FUND_BY_CIK

st.set_page_config(page_title="My Watchlist", page_icon="⭐", layout="wide")
st.title("⭐ My Watchlist")

WATCHLIST_PATH = Path(__file__).parent.parent.parent / "data" / "user_watchlist.json"


def _load_watchlist() -> list[str]:
    if WATCHLIST_PATH.exists():
        try:
            return json.loads(WATCHLIST_PATH.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_watchlist(tickers: list[str]) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_PATH.write_text(json.dumps(sorted(set(t.upper() for t in tickers))))


# ── Add / remove tickers ──────────────────────────────────────────────────────
watchlist = _load_watchlist()

col_add, col_remove = st.columns(2)
with col_add:
    new_ticker = st.text_input("Add ticker", placeholder="e.g. NVDA").strip().upper()
    if st.button("➕ Add") and new_ticker:
        if new_ticker not in watchlist:
            watchlist.append(new_ticker)
            _save_watchlist(watchlist)
            st.success(f"{new_ticker} added.")
            st.rerun()
        else:
            st.info(f"{new_ticker} is already in your watchlist.")

with col_remove:
    if watchlist:
        to_remove = st.selectbox("Remove ticker", [""] + watchlist)
        if st.button("❌ Remove") and to_remove:
            watchlist = [t for t in watchlist if t != to_remove]
            _save_watchlist(watchlist)
            st.success(f"{to_remove} removed.")
            st.rerun()

if not watchlist:
    st.info("Your watchlist is empty. Add a ticker above.")
    st.stop()

st.markdown(f"**Tracking:** {', '.join(watchlist)}")
st.markdown("---")

# ── Pull data ─────────────────────────────────────────────────────────────────
session = get_session()
congress_df = get_congress_trades(session, days=90)
diffs_df    = get_fund_diffs(session)
signals_df  = get_signals(session, min_score=0.0)
session.close()

# ── Per-ticker summary ────────────────────────────────────────────────────────
for ticker in watchlist:
    with st.expander(f"**{ticker}**", expanded=True):
        # Congress activity
        ct = congress_df[congress_df["ticker"].str.upper() == ticker] if not congress_df.empty else pd.DataFrame()
        buys  = ct[ct["transaction_type"].str.lower().str.contains("purchase|buy", na=False)] if not ct.empty else pd.DataFrame()
        sells = ct[ct["transaction_type"].str.lower().str.contains("sale|sell", na=False)] if not ct.empty else pd.DataFrame()

        c1, c2 = st.columns(2)
        c1.metric("Congress buys (90d)",  len(buys))
        c2.metric("Congress sells (90d)", len(sells))

        if not ct.empty:
            st.markdown("**Congress trades:**")
            ct_cols = ["member_name", "party", "transaction_type", "amount_range", "transaction_date"]
            ct_cols = [c for c in ct_cols if c in ct.columns]
            st.dataframe(ct[ct_cols], use_container_width=True)

        # Fund activity
        fd = diffs_df[diffs_df["ticker"].str.upper() == ticker] if not diffs_df.empty else pd.DataFrame()
        if not fd.empty:
            st.markdown("**Fund activity (latest quarter):**")
            fd_cols = ["fund_name", "to_period", "shares_prev", "shares_curr", "pct_change", "action"]
            fd_cols = [c for c in fd_cols if c in fd.columns]
            st.dataframe(fd[fd_cols], use_container_width=True)
        else:
            st.caption("No fund activity found for this ticker.")

        # Conviction score
        sig = signals_df[signals_df["ticker"] == ticker] if not signals_df.empty else pd.DataFrame()
        if not sig.empty:
            score = sig.iloc[0]["conviction_score"]
            st.metric("Conviction Score", score)
        else:
            st.caption("No conviction score — ticker not yet in signals data.")

# ── Alert summary ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Alert Summary")
if not congress_df.empty:
    activity = congress_df[congress_df["ticker"].isin(watchlist)]
    if not activity.empty:
        counts = activity.groupby("ticker").size().reset_index(name="trades")
        for _, row in counts.iterrows():
            st.info(f"📢 {row['trades']} tracked entity trade(s) for **{row['ticker']}** in the last 90 days.")
    else:
        st.success("No recent congress activity on your watchlist tickers.")
