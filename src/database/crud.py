"""
CRUD helpers — thin wrappers around SQLAlchemy so collectors and processors
never touch the session directly.
"""
import json
import logging
from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from src.database.models import CongressTrade, FundDiff, FundHolding, Signal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Congress trades
# ---------------------------------------------------------------------------

def save_congress_trade(session: Session, trade: dict) -> bool:
    """Insert a congress trade, skip if filing_id already exists. Returns True if inserted."""
    dialect = session.bind.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert

    stmt = (
        insert(CongressTrade)
        .values(**trade)
        .on_conflict_do_nothing(index_elements=["filing_id"])
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


def get_congress_trades(
    session: Session,
    days: int = 60,
    chamber: Optional[str] = None,
    members: Optional[list[str]] = None,
    transaction_types: Optional[list[str]] = None,
    ticker: Optional[str] = None,
) -> pd.DataFrame:
    from sqlalchemy import select, and_, or_
    from datetime import timedelta

    cutoff = date.today() - timedelta(days=days)
    filters = [CongressTrade.disclosure_date >= cutoff]

    if chamber:
        filters.append(CongressTrade.chamber == chamber)
    if members:
        filters.append(CongressTrade.member_name.in_(members))
    if transaction_types:
        filters.append(CongressTrade.transaction_type.in_(transaction_types))
    if ticker:
        filters.append(CongressTrade.ticker.ilike(f"%{ticker}%"))

    stmt = select(CongressTrade).where(and_(*filters)).order_by(CongressTrade.disclosure_date.desc())
    rows = session.execute(stmt).scalars().all()
    return _to_df(rows, CongressTrade)


# ---------------------------------------------------------------------------
# Fund holdings
# ---------------------------------------------------------------------------

def save_fund_holding(session: Session, holding: dict) -> bool:
    dialect = session.bind.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert

    stmt = (
        insert(FundHolding)
        .values(**holding)
        .on_conflict_do_nothing(index_elements=["fund_cik", "period_of_report", "cusip"])
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


def get_fund_holdings(
    session: Session,
    fund_cik: Optional[str] = None,
    period: Optional[date] = None,
) -> pd.DataFrame:
    from sqlalchemy import select, and_

    filters = []
    if fund_cik:
        filters.append(FundHolding.fund_cik == fund_cik)
    if period:
        filters.append(FundHolding.period_of_report == period)

    stmt = select(FundHolding)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(FundHolding.value_usd.desc())
    rows = session.execute(stmt).scalars().all()
    return _to_df(rows, FundHolding)


def get_available_periods(session: Session, fund_cik: str) -> list[date]:
    from sqlalchemy import select, distinct
    stmt = (
        select(distinct(FundHolding.period_of_report))
        .where(FundHolding.fund_cik == fund_cik)
        .order_by(FundHolding.period_of_report.desc())
    )
    return [r for r in session.execute(stmt).scalars().all()]


# ---------------------------------------------------------------------------
# Fund diffs
# ---------------------------------------------------------------------------

def save_fund_diff(session: Session, diff: dict) -> bool:
    dialect = session.bind.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert

    stmt = (
        insert(FundDiff)
        .values(**diff)
        .on_conflict_do_nothing(index_elements=["fund_cik", "cusip", "from_period", "to_period"])
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


def get_fund_diffs(
    session: Session,
    fund_cik: Optional[str] = None,
    to_period: Optional[date] = None,
    action: Optional[str] = None,
) -> pd.DataFrame:
    from sqlalchemy import select, and_

    filters = []
    if fund_cik:
        filters.append(FundDiff.fund_cik == fund_cik)
    if to_period:
        filters.append(FundDiff.to_period == to_period)
    if action:
        filters.append(FundDiff.action == action)

    stmt = select(FundDiff)
    if filters:
        stmt = stmt.where(and_(*filters))
    rows = session.execute(stmt).scalars().all()
    return _to_df(rows, FundDiff)


def clear_fund_diffs(session: Session) -> None:
    session.query(FundDiff).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

def save_signal(session: Session, signal: dict) -> None:
    dialect = session.bind.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert

    # Signals don't have a unique constraint configured currently.
    # To use ON CONFLICT DO NOTHING in PostgreSQL, we must specify the unique index.
    # Let's just do a regular insert and handle IntegrityError.
    from sqlalchemy.exc import IntegrityError
    from src.database.models import Signal

    try:
        sig = Signal(**signal)
        session.add(sig)
        session.commit()
    except IntegrityError:
        session.rollback()


def get_signals(session: Session, min_score: float = 0.0) -> pd.DataFrame:
    from sqlalchemy import select
    stmt = (
        select(Signal)
        .where(Signal.conviction_score >= min_score)
        .order_by(Signal.conviction_score.desc())
    )
    rows = session.execute(stmt).scalars().all()
    return _to_df(rows, Signal)


def clear_signals(session: Session) -> None:
    session.query(Signal).delete()
    session.commit()


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _to_df(rows: list, model) -> pd.DataFrame:
    if not rows:
        cols = [c.key for c in model.__table__.columns]
        return pd.DataFrame(columns=cols)
    return pd.DataFrame([
        {c.key: getattr(r, c.key) for c in model.__table__.columns}
        for r in rows
    ])
