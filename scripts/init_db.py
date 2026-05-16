#!/usr/bin/env python3
"""
One-time setup script. Run this before starting the dashboard:

    python scripts/init_db.py

What it does:
  1. Creates all database tables.
  2. Runs the Senate trade fetch.
  3. Runs the EDGAR 13F fetch.
  4. Computes quarter-over-quarter diffs.
  5. Computes conviction signals.
"""
import logging
import sys
import os

# Make project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("init_db")


def main() -> None:
    logger.info("=== Smart Money Tracker — DB initialisation ===")

    # 1. Create tables
    logger.info("Step 1/5 — Creating database tables…")
    from src.database.connection import init_db
    init_db()
    logger.info("Tables created (or already exist).")

    # 2. Senate trades
    logger.info("Step 2/5 — Fetching Senate PTR filings…")
    from src.collectors.senate import fetch_senate_trades
    n = fetch_senate_trades()
    logger.info("Senate: %d new trades inserted.", n)

    # 3. 13F filings
    logger.info("Step 3/5 — Fetching SEC 13F filings (this may take a few minutes)…")
    from src.collectors.edgar import fetch_all_13f_filings
    n = fetch_all_13f_filings()
    logger.info("EDGAR: %d holding rows inserted.", n)

    # 4. Diffs
    logger.info("Step 4/5 — Computing quarter-over-quarter diffs…")
    from src.processors.diff_13f import compute_all_diffs
    n = compute_all_diffs(rebuild=True)
    logger.info("Diffs: %d rows computed.", n)

    # 5. Signals
    logger.info("Step 5/5 — Computing conviction signals…")
    from src.processors.signals import compute_signals
    n = compute_signals(rebuild=True)
    logger.info("Signals: %d tickers scored.", n)

    logger.info("=== Initialisation complete. Run: streamlit run app/main.py ===")


if __name__ == "__main__":
    main()
