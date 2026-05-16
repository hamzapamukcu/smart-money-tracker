import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/tracker.db")
SEC_USER_AGENT: str = os.getenv("SEC_USER_AGENT", "SmartMoneyTracker user@example.com")
STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: str = os.getenv("SMTP_PORT", "")
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
