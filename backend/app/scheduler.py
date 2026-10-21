import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")
