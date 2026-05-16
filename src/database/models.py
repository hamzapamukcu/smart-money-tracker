from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Float, Integer, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class CongressTrade(Base):
    __tablename__ = "congress_trades"

    id               = Column(Integer, primary_key=True)
    member_name      = Column(Text, nullable=False)
    chamber          = Column(Text, nullable=False)          # 'senate' | 'house'
    party            = Column(Text)                          # 'R', 'D', 'I'
    state            = Column(Text)
    ticker           = Column(Text)                          # null for non-stock assets
    asset_name       = Column(Text, nullable=False)
    asset_type       = Column(Text)                          # 'Stock', 'ETF', etc.
    transaction_type = Column(Text, nullable=False)          # 'Purchase', 'Sale', 'Exchange'
    transaction_date = Column(Date, nullable=False)
    disclosure_date  = Column(Date, nullable=False)
    days_to_disclose = Column(Integer)                       # computed on insert
    amount_range     = Column(Text)
    amount_min       = Column(Integer)
    amount_max       = Column(Integer)
    filing_id        = Column(Text, unique=True)             # dedup key
    filing_url       = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)


class FundHolding(Base):
    __tablename__ = "fund_holdings"

    id               = Column(Integer, primary_key=True)
    fund_name        = Column(Text, nullable=False)
    fund_cik         = Column(Text, nullable=False)
    manager_name     = Column(Text, nullable=False)
    period_of_report = Column(Date, nullable=False)          # quarter-end date
    ticker           = Column(Text)
    cusip            = Column(Text, nullable=False)
    asset_name       = Column(Text, nullable=False)
    asset_class      = Column(Text)                          # 'COM', 'PRN', etc.
    shares           = Column(BigInteger)
    value_usd        = Column(BigInteger)                    # in thousands as reported
    filing_date      = Column(Date, nullable=False)
    accession_number = Column(Text, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("fund_cik", "period_of_report", "cusip", name="uq_fund_period_cusip"),
    )


class FundDiff(Base):
    __tablename__ = "fund_diffs"

    id             = Column(Integer, primary_key=True)
    fund_cik       = Column(Text, nullable=False)
    fund_name      = Column(Text, nullable=False)
    ticker         = Column(Text)
    cusip          = Column(Text, nullable=False)
    asset_name     = Column(Text, nullable=False)
    from_period    = Column(Date, nullable=False)
    to_period      = Column(Date, nullable=False)
    shares_prev    = Column(BigInteger)
    shares_curr    = Column(BigInteger)
    shares_delta   = Column(BigInteger)
    pct_change     = Column(Float)
    value_prev_usd = Column(BigInteger)
    value_curr_usd = Column(BigInteger)
    action         = Column(Text, nullable=False)  # 'new','increased','decreased','closed','unchanged'
    created_at     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("fund_cik", "cusip", "from_period", "to_period", name="uq_diff"),
    )


class Signal(Base):
    __tablename__ = "signals"

    id               = Column(Integer, primary_key=True)
    ticker           = Column(Text, nullable=False)
    signal_date      = Column(Date, nullable=False)
    period           = Column(Text, nullable=False)          # e.g. '2024-Q4'
    congress_buyers  = Column(Integer, default=0)
    congress_sellers = Column(Integer, default=0)
    fund_buyers      = Column(Text)                          # JSON array of CIKs
    fund_sellers     = Column(Text)                          # JSON array of CIKs
    new_positions    = Column(Integer, default=0)
    conviction_score = Column(Float)
    created_at       = Column(DateTime, default=datetime.utcnow)
