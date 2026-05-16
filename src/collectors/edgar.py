"""
Fetch SEC 13F-HR filings for all tracked funds via the EDGAR EDGAR API.

Flow:
  1. For each CIK in the watchlist, fetch the submissions JSON to find 13F filings.
  2. For each new 13F accession number not yet in the DB, fetch the filing index.
  3. Find the XML holdings file in the index, parse <informationTable>.
  4. Persist each holding row; duplicates are ignored (ON CONFLICT DO NOTHING).

Rate limit: 10 req/s max → we sleep 0.15 s between requests.
"""
import logging
import time
from datetime import date, datetime
from typing import Optional
from xml.etree import ElementTree as ET

import requests

from config.settings import SEC_USER_AGENT
from config.watchlists import FUND_WATCHLIST, FUND_BY_CIK
from src.database.connection import get_session
from src.database.crud import save_fund_holding, get_available_periods

logger = logging.getLogger(__name__)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FILING_INDEX_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/"
REQUEST_DELAY = 0.15  # respect 10 req/s EDGAR limit

# XML namespace used in 13F holding tables
_NS = {
    "ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable",
    # some filings use the alternate
    "ns2": "http://www.sec.gov/edgar/common",
}


def _headers() -> dict:
    return {
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }


def _get(url: str, base: str = "data.sec.gov") -> Optional[requests.Response]:
    """GET with EDGAR-required headers. Returns None on failure."""
    h = _headers()
    h["Host"] = base
    try:
        resp = requests.get(url, headers=h, timeout=30)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        logger.error("EDGAR request failed [%s]: %s", url, exc)
        return None


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _normalize_accession(accession: str) -> str:
    """Convert '0001234567-24-000123' → '0001234567-24-000123' (keep dashes for URL)."""
    return accession.replace("-", "")


def _get_13f_filings_for_cik(cik: str) -> list[dict]:
    """Return list of {accession, filing_date, period} dicts for all 13F-HR filings."""
    padded = cik.lstrip("0").zfill(10)
    url = SUBMISSIONS_URL.format(cik=padded)
    resp = _get(url, base="data.sec.gov")
    time.sleep(REQUEST_DELAY)
    if not resp:
        return []

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})
    forms        = recent.get("form", [])
    accessions   = recent.get("accessionNumber", [])
    filed_dates  = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])

    results = []
    for form, acc, filed, period in zip(forms, accessions, filed_dates, report_dates):
        if form.upper() in ("13F-HR", "13F-HR/A"):
            results.append({
                "accession":   acc,
                "filing_date": _parse_date(filed),
                "period":      _parse_date(period),
            })

    # Also check older filings in paginated files list (submissions may be paginated)
    for extra_file in data.get("filings", {}).get("files", []):
        extra_url = f"https://data.sec.gov/submissions/{extra_file['name']}"
        extra_resp = _get(extra_url, base="data.sec.gov")
        time.sleep(REQUEST_DELAY)
        if not extra_resp:
            continue
        extra_data = extra_resp.json()
        e_forms   = extra_data.get("form", [])
        e_accs    = extra_data.get("accessionNumber", [])
        e_filed   = extra_data.get("filingDate", [])
        e_periods = extra_data.get("reportDate", [])
        for form, acc, filed, period in zip(e_forms, e_accs, e_filed, e_periods):
            if form.upper() in ("13F-HR", "13F-HR/A"):
                results.append({
                    "accession":   acc,
                    "filing_date": _parse_date(filed),
                    "period":      _parse_date(period),
                })

    logger.info("CIK %s — found %d 13F filings", cik, len(results))
    return results


def _get_xml_url(cik: str, accession: str) -> Optional[str]:
    """Fetch filing index and return URL of the XML holdings file."""
    cik_int = str(int(cik))  # drop leading zeros for the URL path
    acc_nodash = accession.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/"

    resp = _get(index_url, base="www.sec.gov")
    time.sleep(REQUEST_DELAY)
    if not resp:
        return None

    import re
    matches = re.findall(r'href="([^"]+\.xml)"', resp.text, re.IGNORECASE)
    
    for path in matches:
        if "index" not in path.lower() and "primary_doc" not in path.lower():
            if path.startswith("/"):
                return f"https://www.sec.gov{path}"
            return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{path}"

    return None


def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix (e.g. '{http://...}tag' -> 'tag')."""
    return tag.split('}', 1)[1] if '}' in tag else tag

def _parse_holdings_xml(xml_text: str, fund_meta: dict, period: date, filing_date: date, accession: str) -> list[dict]:
    """Parse 13F XML informationTable and return list of holding dicts (namespace-agnostic)."""
    holdings = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.error("XML parse error: %s", exc)
        return holdings

    # Find all infoTable elements regardless of namespace
    info_tables = [el for el in root.iter() if strip_ns(el.tag) == "infoTable"]

    def _text(el, tag: str) -> Optional[str]:
        for child in el.iter():
            if strip_ns(child.tag) == tag:
                return child.text.strip() if child.text else None
        return None

    for entry in info_tables:
        cusip = _text(entry, "cusip")
        if not cusip:
            continue

        shares_raw = _text(entry, "sshPrnamt")
        shares = int(shares_raw) if shares_raw and shares_raw.isdigit() else None

        value_raw = _text(entry, "value")
        value = int(value_raw) if value_raw and value_raw.isdigit() else None

        holdings.append({
            "fund_name":        fund_meta["fund_name"],
            "fund_cik":         fund_meta["cik"],
            "manager_name":     fund_meta["manager_name"],
            "period_of_report": period,
            "ticker":           _text(entry, "ticker"),
            "cusip":            cusip,
            "asset_name":       _text(entry, "nameOfIssuer") or "Unknown",
            "asset_class":      _text(entry, "titleOfClass"),
            "shares":           shares,
            "value_usd":        value,
            "filing_date":      filing_date,
            "accession_number": accession,
        })

    return holdings


def fetch_13f_for_fund(fund_meta: dict, session) -> int:
    """Fetch and store all 13F holdings for one fund. Returns rows inserted."""
    cik = fund_meta["cik"]
    existing_periods = set(get_available_periods(session, cik))

    filings = _get_13f_filings_for_cik(cik)
    # VITAL SPEEDUP: Only process the 2 most recent quarters (to compute 1 diff)
    filings = sorted(filings, key=lambda x: x["period"], reverse=True)[:2]
    
    inserted = 0

    for filing in filings:
        period = filing["period"]
        if not period:
            continue
        # Skip quarters we already have
        if period in existing_periods:
            logger.debug("CIK %s — period %s already in DB, skipping", cik, period)
            continue

        accession = filing["accession"]
        xml_url = _get_xml_url(cik, accession)
        if not xml_url:
            logger.warning("CIK %s — could not find XML for accession %s", cik, accession)
            continue

        xml_resp = _get(xml_url, base="www.sec.gov")
        time.sleep(REQUEST_DELAY)
        if not xml_resp:
            continue

        holdings = _parse_holdings_xml(
            xml_resp.text,
            fund_meta,
            period,
            filing["filing_date"],
            accession,
        )

        for holding in holdings:
            if save_fund_holding(session, holding):
                inserted += 1

        logger.info(
            "CIK %s (%s) — period %s — %d holdings inserted",
            cik, fund_meta["fund_name"], period, inserted,
        )

    return inserted


def fetch_all_13f_filings() -> int:
    """Fetch 13F filings for every fund in the watchlist. Returns total rows inserted."""
    session = get_session()
    total = 0
    try:
        for fund_meta in FUND_WATCHLIST:
            logger.info("Processing fund: %s (CIK %s)", fund_meta["fund_name"], fund_meta["cik"])
            count = fetch_13f_for_fund(fund_meta, session)
            total += count
    finally:
        session.close()
    logger.info("EDGAR fetch complete — %d total holdings inserted.", total)
    return total
