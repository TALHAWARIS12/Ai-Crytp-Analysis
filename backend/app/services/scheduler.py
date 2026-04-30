from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.alert_engine import alert_engine
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def setup_scheduler():
    """Configure and start the background scheduler"""
    logger.info("Initializing Scheduler...")
    
    # Run market checks every 5 minutes
    scheduler.add_job(
        alert_engine.run_check,
        'interval',
        minutes=5,
        id='market_check',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started. Market checks scheduled every 5 minutes.")

def shutdown_scheduler():
    """Gracefully shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
