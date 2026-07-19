"""
Scheduler Module - In-process APScheduler for weekly batch jobs.

Provides a singleton AsyncIOScheduler that starts with the FastAPI app
and registers weekly jobs (Error DNA, Trajectory, Study Plan generation).
"""
import logging
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Singleton scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown complete")


def register_weekly_job(
    func: Callable,
    job_id: str,
    day_of_week: str = "mon",
    hour: int = 6,
    minute: int = 0,
    replace: bool = True,
) -> None:
    """
    Register a function to run weekly.

    Args:
        func: Async callable to execute
        job_id: Unique identifier for the job
        day_of_week: Day to run (mon, tue, wed, thu, fri, sat, sun)
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        replace: Whether to replace existing job with same ID
    """
    scheduler = get_scheduler()
    trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)

    if replace:
        # Remove existing job with same ID if present
        existing = scheduler.get_job(job_id)
        if existing:
            scheduler.remove_job(job_id)
            logger.debug("Removed existing job: %s", job_id)

    scheduler.add_job(func, trigger=trigger, id=job_id, replace_existing=replace)
    logger.info("Registered weekly job '%s' for %s at %02d:%02d", job_id, day_of_week, hour, minute)


def register_interval_job(
    func: Callable,
    job_id: str,
    seconds: int = 60,
    replace: bool = True,
) -> None:
    """
    Register a function to run at a fixed interval.

    Args:
        func: Async callable to execute
        job_id: Unique identifier for the job
        seconds: Interval in seconds
        replace: Whether to replace existing job with same ID
    """
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = get_scheduler()
    trigger = IntervalTrigger(seconds=seconds)

    if replace:
        existing = scheduler.get_job(job_id)
        if existing:
            scheduler.remove_job(job_id)

    scheduler.add_job(func, trigger=trigger, id=job_id, replace_existing=replace)
    logger.info("Registered interval job '%s' every %d seconds", job_id, seconds)


def list_scheduled_jobs() -> list[dict]:
    """List all scheduled jobs with their next run times."""
    scheduler = get_scheduler()
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs
