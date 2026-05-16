import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "tracker.db")

# Force using the absolute path to our populated tracker.db so Streamlit Cloud doesn't look elsewhere
DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"

SEC_USER_AGENT: str = os.getenv("SEC_USER_AGENT", "SmartMoneyTracker user@example.com")
STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

SMTP_HOST: str = os.getenv("SMTP_HOST", "")
SMTP_PORT: str = os.getenv("SMTP_PORT", "")
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")
ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
