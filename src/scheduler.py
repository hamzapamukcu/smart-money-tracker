"""
Background scheduler — runs inside the Python process (no separate service needed).

Jobs:
  - fetch_senate_trades   daily at 08:00
  - fetch_13f_filings     weekly Monday 09:00
  - compute_diffs         after each 13F fetch
  - compute_signals       after diffs or senate fetch
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def _run_senate_pipeline() -> None:
    from src.collectors.senate import fetch_senate_trades
    from src.processors.signals import compute_signals
    logger.info("[scheduler] Senate pipeline starting…")
    fetch_senate_trades()
    compute_signals(rebuild=True)
    logger.info("[scheduler] Senate pipeline done.")


def _run_edgar_pipeline() -> None:
    from src.collectors.edgar import fetch_all_13f_filings
    from src.processors.diff_13f import compute_all_diffs
    from src.processors.signals import compute_signals
    logger.info("[scheduler] EDGAR pipeline starting…")
    fetch_all_13f_filings()
    compute_all_diffs(rebuild=True)
    compute_signals(rebuild=True)
    logger.info("[scheduler] EDGAR pipeline done.")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        _run_senate_pipeline,
        CronTrigger(hour=8, minute=0),
        id="senate_daily",
        name="Daily Senate trade fetch",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_edgar_pipeline,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="edgar_weekly",
        name="Weekly 13F fetch + diff + signals",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — senate daily 08:00, EDGAR weekly Monday 09:00.")
    return scheduler
