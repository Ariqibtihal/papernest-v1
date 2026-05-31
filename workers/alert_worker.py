from __future__ import annotations

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select

from app.db.session import SessionLocal
from models.search_alert import SearchAlert
from services.search_service import SearchService

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            run_alerts, "interval", minutes=60, id="alert_checker", replace_existing=True
        )
        scheduler.start()
        logger.info("Alert scheduler started")
    return scheduler


def stop_scheduler() -> None:
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Alert scheduler stopped")


async def run_alerts() -> None:
    logger.info("Running alert checks...")
    async with SessionLocal() as session:
        result = await session.execute(select(SearchAlert).where(SearchAlert.is_active.is_(True)))
        alerts = result.scalars().all()
        logger.info(f"Processing {len(alerts)} active alerts")
        for alert in alerts:
            try:
                await _check_alert(session, alert)
            except Exception:
                # Use logger.exception so the full traceback is captured in structured logs
                logger.exception(f"Alert {alert.id} check failed (query='{alert.query}')")


async def _check_alert(session, alert: SearchAlert) -> None:
    from schemas.search import SearchFilters

    filters = SearchFilters()
    if alert.filters_json:
        try:
            filters = SearchFilters.model_validate_json(alert.filters_json)
        except Exception:
            logger.warning(f"Alert {alert.id}: invalid filters_json, using defaults")

    papers, _latency, _total, _warnings = await SearchService().run(alert.query, filters, limit=10)

    # Always update last_run_at so we know the alert was processed
    alert.last_run_at = datetime.now(UTC).replace(tzinfo=None)  # naive UTC for SQLite
    await session.commit()

    if papers:
        logger.info(f"Alert {alert.id}: found {len(papers)} papers for query='{alert.query}'")
    else:
        logger.debug(f"Alert {alert.id}: no new papers for query='{alert.query}'")
