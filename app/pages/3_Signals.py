import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import pandas as pd
import streamlit as st

from src.database.connection import get_session
from src.database.crud import get_signals, get_congress_trades, get_fund_diffs
from config.watchlists import FUND_BY_CIK
from app.components.charts import heatmap_sector_signals

st.set_page_config(page_title="Signals", page_icon="🎯", layout="wide")
st.title("🎯 Conviction Signals")
st.caption("Tickers where congress members AND institutional funds are moving in the same direction.")

# ── Filters ───────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([1, 3])
min_score = col_f1.slider("Minimum conviction score", 0.0, 20.0, 1.0, 0.5)

session = get_session()
signals_df = get_signals(session, min_score=min_score)
session.close()

if signals_df.empty:
    st.info("No signals yet. Run `python scripts/init_db.py` to generate conviction scores.")
    st.stop()

# Decode JSON arrays → readable names
def _cik_list_to_names(json_str) -> str:
    if not json_str:
        return ""
    try:
        ciks = json.loads(json_str)
        return ", ".join(FUND_BY_CIK.get(c, {}).get("fund_name", c) for c in ciks)
    except (json.JSONDecodeError, TypeError):
        return str(json_str)

signals_df = signals_df.copy()
signals_df["fund_buyers_names"]  = signals_df["fund_buyers"].apply(_cik_list_to_names)
signals_df["fund_sellers_names"] = signals_df["fund_sellers"].apply(_cik_list_to_names)

# ── Top signals table ─────────────────────────────────────────────────────────
st.subheader("Top Signals")
display_cols = ["ticker", "conviction_score", "congress_buyers", "congress_sellers",
                "new_positions", "fund_buyers_names", "period"]
display = signals_df[display_cols].rename(columns={
    "ticker":            "Ticker",
    "conviction_score":  "Score",
    "congress_buyers":   "Congress Buyers",
    "congress_sellers":  "Congress Sellers",
    "new_positions":     "New Fund Positions",
    "fund_buyers_names": "Funds Buying",
    "period":            "Period",
})
st.dataframe(display, use_container_width=True, height=400)

# ── Chart ─────────────────────────────────────────────────────────────────────
st.plotly_chart(heatmap_sector_signals(signals_df), use_container_width=True)

# ── Ticker drill-down ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Ticker Detail")
ticker_pick = st.selectbox("Select a ticker to inspect", [""] + sorted(signals_df["ticker"].tolist()))

if ticker_pick:
    row = signals_df[signals_df["ticker"] == ticker_pick].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Conviction Score", row["conviction_score"])
    c2.metric("Congress Buyers",  row["congress_buyers"])
    c3.metric("New Fund Positions", row["new_positions"])

    st.markdown(f"**Funds buying:** {row['fund_buyers_names'] or 'none'}")
    st.markdown(f"**Funds selling:** {row['fund_sellers_names'] or 'none'}")

    # Congress activity for this ticker
    session = get_session()
    ctrades = get_congress_trades(session, days=90, ticker=ticker_pick)
    diffs   = get_fund_diffs(session)
    session.close()

    if not ctrades.empty:
        st.subheader("Congress Activity (last 90 days)")
        cols = ["member_name", "party", "state", "transaction_type", "amount_range", "transaction_date"]
        cols = [c for c in cols if c in ctrades.columns]
        st.dataframe(ctrades[cols], use_container_width=True)

    fund_activity = diffs[diffs["ticker"].str.upper() == ticker_pick.upper()] if not diffs.empty else pd.DataFrame()
    if not fund_activity.empty:
        st.subheader("Fund Activity")
        fa_cols = ["fund_name", "from_period", "to_period", "shares_prev", "shares_curr", "pct_change", "action"]
        fa_cols = [c for c in fa_cols if c in fund_activity.columns]
        st.dataframe(fund_activity[fa_cols], use_container_width=True)
