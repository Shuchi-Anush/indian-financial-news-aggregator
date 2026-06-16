from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from datetime import datetime, timedelta

from app.orchestration.ingestion_jobs import run_ingestion_cycle

log = structlog.get_logger()
IST = ZoneInfo("Asia/Kolkata")

scheduler = AsyncIOScheduler(timezone=IST)


def start_scheduler():
    """Initializes and starts the APScheduler with market-aware intervals."""
    if scheduler.running:
        return

    # Market hours: Mon-Fri 09:00 - 15:59 IST -> every 5 minutes
    scheduler.add_job(
        run_ingestion_cycle,
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5", timezone=IST),
        id="market_hours_ingestion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Off-market hours (Mon-Fri 00:00 - 08:59 and 16:00 - 23:59) -> every 30 minutes
    scheduler.add_job(
        run_ingestion_cycle,
        CronTrigger(day_of_week="mon-fri", hour="0-8,16-23", minute="*/30", timezone=IST),
        id="off_market_hours_ingestion_weekdays",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Weekends -> every 30 minutes
    scheduler.add_job(
        run_ingestion_cycle,
        CronTrigger(day_of_week="sat,sun", minute="*/30", timezone=IST),
        id="off_market_hours_ingestion_weekends",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Run once 10 seconds after startup for out-of-the-box ingestion
    scheduler.add_job(
        run_ingestion_cycle,
        "date",
        run_date=datetime.now(IST) + timedelta(seconds=10),
        id="startup_ingestion",
        replace_existing=True,
    )

    scheduler.start()
    log.info("scheduler_started", timezone="Asia/Kolkata")


def stop_scheduler():
    """Gracefully shuts down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("scheduler_stopped")
