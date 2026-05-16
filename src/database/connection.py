import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Allow imports from project root when running scripts directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.settings import DATABASE_URL
from src.database.models import Base

# SQLite needs check_same_thread=False; ignored for Postgres
_connect_args = {"check_same_thread": False, "timeout": 30.0} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    """Return a new database session. Caller is responsible for closing it."""
    return SessionLocal()


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)
