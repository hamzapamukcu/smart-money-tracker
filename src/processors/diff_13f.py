"""
Compare consecutive 13F quarters for each fund and populate fund_diffs.

Run after any new holdings are ingested. fund_diffs is fully recomputable —
clear it and re-run at any time.
"""
import logging
from datetime import date
from typing import Optional

import pandas as pd

from src.database.connection import get_session
from src.database.crud import (
    get_fund_holdings,
    get_available_periods,
    save_fund_diff,
    clear_fund_diffs,
)
from config.watchlists import FUND_WATCHLIST

logger = logging.getLogger(__name__)


def _classify_action(prev: Optional[float], curr: Optional[float]) -> str:
    if prev is None or prev == 0:
        return "new"
    if curr is None or curr == 0:
        return "closed"
    delta = curr - prev
    if delta > 0:
        return "increased"
    if delta < 0:
        return "decreased"
    return "unchanged"


def compute_diffs_for_fund(session, fund_cik: str, fund_name: str) -> int:
    """Compute QoQ diffs for a single fund. Returns number of diff rows created."""
    periods = get_available_periods(session, fund_cik)
    if len(periods) < 2:
        logger.info("Fund %s — only %d period(s), skipping diff.", fund_name, len(periods))
        return 0

    # periods are sorted DESC; iterate consecutive pairs
    inserted = 0
    for i in range(len(periods) - 1):
        to_period   = periods[i]
        from_period = periods[i + 1]

        curr_df = get_fund_holdings(session, fund_cik=fund_cik, period=to_period)
        prev_df = get_fund_holdings(session, fund_cik=fund_cik, period=from_period)

        if curr_df.empty and prev_df.empty:
            continue

        # Merge on CUSIP
        merged = pd.merge(
            curr_df[["cusip", "ticker", "asset_name", "shares", "value_usd"]].rename(
                columns={"shares": "shares_curr", "value_usd": "value_curr"}
            ),
            prev_df[["cusip", "shares", "value_usd"]].rename(
                columns={"shares": "shares_prev", "value_usd": "value_prev"}
            ),
            on="cusip",
            how="outer",
        )

        for _, row in merged.iterrows():
            shares_prev = row.get("shares_prev")
            shares_curr = row.get("shares_curr")
            action = _classify_action(
                float(shares_prev) if pd.notna(shares_prev) else None,
                float(shares_curr) if pd.notna(shares_curr) else None,
            )

            delta = None
            pct   = None
            if pd.notna(shares_curr) and pd.notna(shares_prev):
                delta = int(shares_curr) - int(shares_prev)
                if shares_prev and shares_prev != 0:
                    pct = round(delta / float(shares_prev) * 100, 2)

            diff_record = {
                "fund_cik":       fund_cik,
                "fund_name":      fund_name,
                "ticker":         row.get("ticker") if pd.notna(row.get("ticker")) else None,
                "cusip":          row["cusip"],
                "asset_name":     row.get("asset_name") if pd.notna(row.get("asset_name")) else "Unknown",
                "from_period":    from_period,
                "to_period":      to_period,
                "shares_prev":    int(shares_prev) if pd.notna(shares_prev) else None,
                "shares_curr":    int(shares_curr) if pd.notna(shares_curr) else None,
                "shares_delta":   delta,
                "pct_change":     pct,
                "value_prev_usd": int(row["value_prev"]) if pd.notna(row.get("value_prev")) else None,
                "value_curr_usd": int(row["value_curr"]) if pd.notna(row.get("value_curr")) else None,
                "action":         action,
            }
            if save_fund_diff(session, diff_record):
                inserted += 1

    logger.info("Fund %s — %d diff rows created.", fund_name, inserted)
    return inserted


def compute_all_diffs(rebuild: bool = False) -> int:
    """
    Recompute diffs for all funds.
    If rebuild=True, wipe fund_diffs first for a clean slate.
    """
    session = get_session()
    total = 0
    try:
        if rebuild:
            clear_fund_diffs(session)
            logger.info("Cleared fund_diffs table for rebuild.")

        for fund in FUND_WATCHLIST:
            total += compute_diffs_for_fund(session, fund["cik"], fund["fund_name"])
    finally:
        session.close()
    logger.info("Diff computation complete — %d rows total.", total)
    return total
