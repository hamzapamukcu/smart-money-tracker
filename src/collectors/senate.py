"""
Fetch Senate STOCK Act Periodic Transaction Reports (PTRs) from the Senate
eFiling API and persist them to the database.

API docs: https://efts.senate.gov/PROD/api/filings
"""
import logging
import time
from datetime import date, datetime
from typing import Optional

import requests

from src.database.connection import get_session
from src.database.crud import save_congress_trade

logger = logging.getLogger(__name__)

SENATE_API_URL = "https://efts.senate.gov/PROD/api/filings"
PAGE_SIZE = 50
REQUEST_DELAY = 1.0  # seconds — be polite


# Amount range text → (min, max) in USD
_AMOUNT_MAP: dict[str, tuple[int, int]] = {
    "$1,001 - $15,000":       (1_001,       15_000),
    "$15,001 - $50,000":      (15_001,       50_000),
    "$50,001 - $100,000":     (50_001,      100_000),
    "$100,001 - $250,000":   (100_001,      250_000),
    "$250,001 - $500,000":   (250_001,      500_000),
    "$500,001 - $1,000,000": (500_001,    1_000_000),
    "$1,000,001 - $5,000,000":  (1_000_001,  5_000_000),
    "$5,000,001 - $25,000,000": (5_000_001, 25_000_000),
    "$25,000,001 +":          (25_000_001,  None),
}


def _parse_amount(raw: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    if not raw:
        return None, None
    for key, bounds in _AMOUNT_MAP.items():
        if key.lower() in raw.lower():
            return bounds
    return None, None


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _build_trade_record(filing: dict) -> Optional[dict]:
    """Map a raw filing dict to the congress_trades schema. Returns None if invalid."""
    filing_id = filing.get("filing_id") or filing.get("id") or filing.get("url")
    if not filing_id:
        return None

    tx_date_raw  = filing.get("transactionDate") or filing.get("transaction_date")
    disc_date_raw = filing.get("filedAt") or filing.get("filed_at") or filing.get("disclosure_date")

    tx_date   = _parse_date(tx_date_raw)
    disc_date = _parse_date(disc_date_raw)
    if not tx_date or not disc_date:
        return None

    amount_raw = filing.get("amount") or filing.get("amount_range")
    amt_min, amt_max = _parse_amount(amount_raw)

    days_late = (disc_date - tx_date).days if tx_date and disc_date else None

    senator_name = (
        filing.get("senator_name")
        or filing.get("first_name", "") + " " + filing.get("last_name", "")
    ).strip()

    return {
        "filing_id":        str(filing_id),
        "member_name":      senator_name or "Unknown",
        "chamber":          "senate",
        "party":            filing.get("party"),
        "state":            filing.get("state"),
        "ticker":           filing.get("ticker") or None,
        "asset_name":       filing.get("asset_name") or filing.get("assetName") or "Unknown",
        "asset_type":       filing.get("asset_type") or filing.get("assetType"),
        "transaction_type": filing.get("type") or filing.get("transaction_type") or "Unknown",
        "transaction_date": tx_date,
        "disclosure_date":  disc_date,
        "days_to_disclose": days_late,
        "amount_range":     amount_raw,
        "amount_min":       amt_min,
        "amount_max":       amt_max,
        "filing_url":       filing.get("url") or filing.get("filing_url"),
    }


def fetch_senate_trades(max_pages: int = 100) -> int:
    """
    Pull all PTR filings from the Senate API, page by page.
    Returns the number of new records inserted.
    """
    session = get_session()
    inserted = 0
    offset = 0

    headers = {"Accept": "application/json"}
    params = {
        "report_types": "PTR",
        "limit": PAGE_SIZE,
    }

    try:
        while offset // PAGE_SIZE < max_pages:
            params["offset"] = offset
            logger.info("Fetching Senate PTRs — offset %d", offset)

            try:
                resp = requests.get(SENATE_API_URL, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as exc:
                logger.error("Senate API request failed: %s", exc)
                break

            # The API returns either {"results": [...], "count": N} or a list directly
            if isinstance(data, list):
                filings = data
                total = len(data)
            else:
                filings = data.get("results", data.get("filings", []))
                total = data.get("count", len(filings))

            if not filings:
                logger.info("No more filings at offset %d — done.", offset)
                break

            for filing in filings:
                record = _build_trade_record(filing)
                if record and save_congress_trade(session, record):
                    inserted += 1

            offset += PAGE_SIZE
            if offset >= total:
                break

            time.sleep(REQUEST_DELAY)

    finally:
        session.close()

    logger.info("Senate fetch complete — %d new trades inserted.", inserted)
    return inserted
