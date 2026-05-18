"""APScheduler setup + scheduled audit jobs — Section 9.

Two cron jobs (UTC):
  * weekly  — every Monday 06:00
  * monthly — 1st of the month 07:00

Each job calls `run_scheduled_audits`, which audits every active site whose
`schedule` matches by running the shared `run_audit` pipeline (Step 5) — so
status transitions, issue persistence and webhook firing are all reused.

`configure_jobs` is split out from `setup_scheduler` so the job wiring is
unit-testable without starting an event-loop scheduler.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_sessionmaker
from services.audit_pipeline import run_audit
from services.repository import SqlAlchemyRepository

logger = logging.getLogger("seo_portal.scheduler")

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_scheduled_audits(schedule: str, repo=None) -> None:
    """Audit every active site with the given schedule. `repo` is injectable
    for tests; production builds a SQLAlchemy repo per run."""
    repo = repo or SqlAlchemyRepository(get_sessionmaker())
    site_ids = await repo.list_due_sites(schedule)
    logger.info(
        "Scheduled run '%s': %d site(s) due", schedule, len(site_ids)
    )
    for site_id in site_ids:
        try:
            audit_id = await repo.create_audit(site_id, "scheduled")
            await run_audit(audit_id, repo)  # fires webhooks itself
        except Exception:  # noqa: BLE001 — one site must not stop the rest
            logger.exception(
                "Scheduled audit failed for site %s", site_id
            )


def configure_jobs(sched: AsyncIOScheduler) -> None:
    """Register the weekly + monthly cron jobs (idempotent)."""
    sched.add_job(
        run_scheduled_audits,
        trigger="cron",
        day_of_week="mon",
        hour=6,
        minute=0,
        id="weekly_audits",
        replace_existing=True,
        kwargs={"schedule": "weekly"},
    )
    sched.add_job(
        run_scheduled_audits,
        trigger="cron",
        day=1,
        hour=7,
        minute=0,
        id="monthly_audits",
        replace_existing=True,
        kwargs={"schedule": "monthly"},
    )


def setup_scheduler(app=None) -> AsyncIOScheduler:
    """Wire jobs and start the scheduler. Safe to call once per process."""
    configure_jobs(scheduler)
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started (weekly + monthly audit jobs, UTC)")
    return scheduler


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
