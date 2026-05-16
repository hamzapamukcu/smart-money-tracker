import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
import streamlit as st

from src.database.connection import get_session
from src.database.crud import get_fund_holdings, get_available_periods, get_fund_diffs
from config.watchlists import FUND_WATCHLIST
from app.components.charts import treemap_portfolio, line_position_history
from app.components.tables import format_value

st.set_page_config(page_title="Fund Tracker", page_icon="📊", layout="wide")
st.title("📊 Fund Tracker — 13F Holdings")

# ── Fund selector ─────────────────────────────────────────────────────────────
fund_options = {f"{f['manager_name']} — {f['fund_name']}": f for f in FUND_WATCHLIST}
selected_label = st.selectbox("Select fund", list(fund_options.keys()))
fund_meta = fund_options[selected_label]
cik = fund_meta["cik"]

session = get_session()
periods = get_available_periods(session, cik)
session.close()

if not periods:
    st.info(f"No 13F data yet for {fund_meta['fund_name']}. Run `python scripts/init_db.py`.")
    st.stop()

# ── Quarter selector ──────────────────────────────────────────────────────────
period_labels = {str(p): p for p in periods}
selected_period_str = st.selectbox("Quarter", list(period_labels.keys()))
selected_period = period_labels[selected_period_str]

session = get_session()
holdings_df = get_fund_holdings(session, fund_cik=cik, period=selected_period)
diffs_df    = get_fund_diffs(session, fund_cik=cik, to_period=selected_period)
all_holdings = get_fund_holdings(session, fund_cik=cik)
session.close()

# ── Portfolio summary ─────────────────────────────────────────────────────────
if not holdings_df.empty:
    total_value = holdings_df["value_usd"].sum() * 1000  # stored in thousands
    st.metric("Total portfolio value", format_value(total_value))

    # Add % of portfolio column
    holdings_df = holdings_df.copy()
    total_k = holdings_df["value_usd"].sum()
    holdings_df["pct_portfolio"] = (holdings_df["value_usd"] / total_k * 100).round(2)

    st.subheader("Current Holdings")
    display = holdings_df[["ticker", "asset_name", "shares", "value_usd", "pct_portfolio"]].rename(columns={
        "ticker":        "Ticker",
        "asset_name":    "Company",
        "shares":        "Shares",
        "value_usd":     "Value ($K)",
        "pct_portfolio": "% Portfolio",
    })
    st.dataframe(display, use_container_width=True, height=400)

    # Treemap
    st.plotly_chart(treemap_portfolio(holdings_df, fund_meta["fund_name"]), use_container_width=True)
else:
    st.warning("No holdings data for this quarter.")

# ── Quarter-over-quarter changes ──────────────────────────────────────────────
if not diffs_df.empty:
    st.markdown("---")
    st.subheader("Quarter-over-Quarter Changes")

    tab_new, tab_inc, tab_dec, tab_closed, tab_unchanged = st.tabs(
        ["🆕 New", "⬆️ Increased", "⬇️ Decreased", "❌ Closed", "➡️ Unchanged"]
    )

    diff_cols = ["ticker", "asset_name", "shares_prev", "shares_curr", "shares_delta", "pct_change"]
    diff_cols = [c for c in diff_cols if c in diffs_df.columns]

    def show_diff_tab(action: str):
        sub = diffs_df[diffs_df["action"] == action][diff_cols]
        if sub.empty:
            st.info(f"No {action} positions this quarter.")
        else:
            st.dataframe(sub.rename(columns={
                "ticker": "Ticker", "asset_name": "Company",
                "shares_prev": "Prev Shares", "shares_curr": "Curr Shares",
                "shares_delta": "Δ Shares", "pct_change": "% Change",
            }), use_container_width=True)

    with tab_new:      show_diff_tab("new")
    with tab_inc:      show_diff_tab("increased")
    with tab_dec:      show_diff_tab("decreased")
    with tab_closed:   show_diff_tab("closed")
    with tab_unchanged: show_diff_tab("unchanged")

# ── Historical position for a ticker ─────────────────────────────────────────
st.markdown("---")
st.subheader("Historical Position for a Ticker")
hist_ticker = st.text_input("Enter ticker to view history", placeholder="e.g. NVDA")
if hist_ticker and not all_holdings.empty:
    fig = line_position_history(all_holdings, hist_ticker, fund_meta["fund_name"])
    st.plotly_chart(fig, use_container_width=True)
