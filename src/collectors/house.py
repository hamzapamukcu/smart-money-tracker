"""
Phase 2 — House financial disclosures.

Uses the community-maintained S3 dataset (official site is PDF-only).
Endpoint: https://house-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json
"""
import logging
import time

import requests

from src.database.connection import get_session
from src.database.crud import save_congress_trade
from src.collectors.senate import _parse_date, _parse_amount

logger = logging.getLogger(__name__)

HOUSE_DATA_URL = (
    "https://house-stock-watcher-data.s3-us-east-2.amazonaws.com/data/all_transactions.json"
)


def fetch_house_trades() -> int:
    """Download all House transactions and persist new ones. Returns rows inserted."""
    logger.info("Fetching House trade data from community dataset…")
    try:
        resp = requests.get(HOUSE_DATA_URL, timeout=60)
        resp.raise_for_status()
        transactions = resp.json()
    except requests.RequestException as exc:
        logger.error("House data fetch failed: %s", exc)
        return 0

    session = get_session()
    inserted = 0
    try:
        for tx in transactions:
            filing_id = tx.get("ptr_link") or tx.get("disclosure_date", "") + tx.get("representative", "") + tx.get("ticker", "")
            if not filing_id:
                continue

            tx_date   = _parse_date(tx.get("transaction_date"))
            disc_date = _parse_date(tx.get("disclosure_date"))
            if not tx_date or not disc_date:
                continue

            amount_raw = tx.get("amount")
            amt_min, amt_max = _parse_amount(amount_raw)

            record = {
                "filing_id":        filing_id,
                "member_name":      tx.get("representative", "Unknown"),
                "chamber":          "house",
                "party":            tx.get("party"),
                "state":            tx.get("state"),
                "ticker":           tx.get("ticker") or None,
                "asset_name":       tx.get("asset_description") or "Unknown",
                "asset_type":       tx.get("asset_type"),
                "transaction_type": tx.get("type") or "Unknown",
                "transaction_date": tx_date,
                "disclosure_date":  disc_date,
                "days_to_disclose": (disc_date - tx_date).days,
                "amount_range":     amount_raw,
                "amount_min":       amt_min,
                "amount_max":       amt_max,
                "filing_url":       tx.get("ptr_link"),
            }
            if save_congress_trade(session, record):
                inserted += 1
    finally:
        session.close()

    logger.info("House fetch complete — %d new trades inserted.", inserted)
    return inserted
