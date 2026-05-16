"""
Cross-reference congress trades and fund diffs to produce conviction scores.

signals table is fully derived — drop and recompute any time.
Formula: score = (congress_buyers * 1.0) + (new_positions * 2.0)
               + (fund_buyers_count * 1.5) - (congress_sellers * 0.5)
               - (fund_sellers_count * 0.5)
"""
import json
import logging
from datetime import date, timedelta
from collections import defaultdict

import pandas as pd

from src.database.connection import get_session
from src.database.crud import (
    get_congress_trades,
    get_fund_diffs,
    save_signal,
    clear_signals,
)

logger = logging.getLogger(__name__)

# How far back to look for congress buys when computing signals
CONGRESS_LOOKBACK_DAYS = 90


def _quarter_label(d: date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def compute_signals(rebuild: bool = True) -> int:
    session = get_session()
    inserted = 0

    try:
        if rebuild:
            clear_signals(session)

        # --- Congress side ---
        congress_df = get_congress_trades(session, days=CONGRESS_LOOKBACK_DAYS)

        congress_buys:  dict[str, list[str]] = defaultdict(list)
        congress_sells: dict[str, list[str]] = defaultdict(list)

        for _, row in congress_df.iterrows():
            ticker = row.get("ticker")
            if not ticker or pd.isna(ticker):
                continue
            ticker = ticker.upper()
            tx_type = (row.get("transaction_type") or "").lower()
            if "purchase" in tx_type or "buy" in tx_type:
                congress_buys[ticker].append(row["member_name"])
            elif "sale" in tx_type or "sell" in tx_type:
                congress_sells[ticker].append(row["member_name"])

        # --- Fund diffs side ---
        fund_diffs_df = get_fund_diffs(session)

        fund_buys:     dict[str, list[str]] = defaultdict(list)
        fund_sells:    dict[str, list[str]] = defaultdict(list)
        fund_new:      dict[str, list[str]] = defaultdict(list)
        ticker_period: dict[str, str]       = {}

        for _, row in fund_diffs_df.iterrows():
            ticker = row.get("ticker")
            if not ticker or pd.isna(ticker):
                continue
            ticker = ticker.upper()
            action = row.get("action", "")
            cik    = row.get("fund_cik", "")

            if action == "new":
                fund_new[ticker].append(cik)
                fund_buys[ticker].append(cik)
            elif action == "increased":
                fund_buys[ticker].append(cik)
            elif action in ("closed", "decreased"):
                fund_sells[ticker].append(cik)

            # Track which period this ticker belongs to
            if ticker not in ticker_period and row.get("to_period"):
                ticker_period[ticker] = _quarter_label(row["to_period"])

        # --- Union of all tickers ---
        all_tickers = (
            set(congress_buys) | set(congress_sells)
            | set(fund_buys) | set(fund_sells)
        )

        today = date.today()
        for ticker in all_tickers:
            cb = len(congress_buys.get(ticker, []))
            cs = len(congress_sells.get(ticker, []))
            fb = list(set(fund_buys.get(ticker, [])))
            fs = list(set(fund_sells.get(ticker, [])))
            np_ = len(fund_new.get(ticker, []))

            score = (cb * 1.0) + (np_ * 2.0) + (len(fb) * 1.5) - (cs * 0.5) - (len(fs) * 0.5)

            signal = {
                "ticker":           ticker,
                "signal_date":      today,
                "period":           ticker_period.get(ticker, _quarter_label(today)),
                "congress_buyers":  cb,
                "congress_sellers": cs,
                "fund_buyers":      json.dumps(fb),
                "fund_sellers":     json.dumps(fs),
                "new_positions":    np_,
                "conviction_score": round(score, 2),
            }
            save_signal(session, signal)
            inserted += 1

    finally:
        session.close()

    logger.info("Signals computed — %d tickers scored.", inserted)
    return inserted
