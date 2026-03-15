"""
APScheduler setup for periodic tasks (weekly tournaments, etc.).
Registered in main.py lifespan.
"""
import logging

logger = logging.getLogger(__name__)

scheduler = None


def setup_scheduler():
    """Initialize and start the scheduler with tournament jobs."""
    global scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()

        # Generate tournaments: Friday 15:00 Astana (10:00 UTC)
        scheduler.add_job(
            _generate_tournaments_job,
            CronTrigger(day_of_week='fri', hour=10, minute=0),
            id='generate_weekly_tournaments',
            replace_existing=True,
        )

        # Finalize expired tournaments: Monday 00:00 Astana (Sunday 19:00 UTC)
        scheduler.add_job(
            _finalize_tournaments_job,
            CronTrigger(day_of_week='sun', hour=19, minute=0),
            id='finalize_tournaments',
            replace_existing=True,
        )

        scheduler.start()
        logger.info("Scheduler started with tournament jobs")
    except ImportError:
        logger.warning("APScheduler not installed — tournament cron jobs disabled")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


async def _generate_tournaments_job():
    """Cron job: generate weekly tournaments for all classes."""
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        from app.services.quiz_tournament_service import QuizTournamentService
        service = QuizTournamentService(db)
        count = await service.generate_weekly_tournaments()
        logger.info(f"Cron: generated {count} weekly tournaments")


async def _finalize_tournaments_job():
    """Cron job: finalize expired tournaments."""
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        from app.services.quiz_tournament_service import QuizTournamentService
        service = QuizTournamentService(db)
        count = await service.finalize_expired_tournaments()
        logger.info(f"Cron: finalized {count} tournaments")
