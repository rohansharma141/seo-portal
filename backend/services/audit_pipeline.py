"""Audit pipeline — Step 5 / Section 11.

`run_audit()` wires crawler → seo_rules → scorer → analyser into one
background task, walking the audit through its status states and persisting
results. Persistence is behind the `AuditRepository` protocol so the
orchestration is testable with an in-memory fake (no DB / no Supabase needed),
while production uses `SqlAlchemyAuditRepository`.

NOTE: not in Section 3's file list — added because both the audits router
(Step 6) and the scheduler (Step 7) need this shared orchestration, and
coupling it into scheduler.py would make the API import the scheduler.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from services.analyser import analyse_audit
from services.backlinks import get_backlink_data
from services.crawler import crawl_site
from services.gsc import get_gsc_performance
from services.scorer import calculate_score, count_by_severity
from services.webhook_dispatcher import Sender, deliver
from utils.seo_rules import evaluate_pages

logger = logging.getLogger("seo_portal.pipeline")


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Lightweight transfer objects (decouple orchestration from the ORM) ──
@dataclass
class SiteInfo:
    id: uuid.UUID
    url: str
    max_pages: int
    domain: str = ""  # Addendum v1.1 — needed for backlink lookup


@dataclass
class AuditInfo:
    id: uuid.UUID
    site_id: uuid.UUID
    status: str


@dataclass
class WebhookInfo:
    id: uuid.UUID
    url: str
    secret: str | None
    events: list


class AuditRepository(Protocol):
    """Persistence seam used by the pipeline."""

    async def create_audit(
        self, site_id: uuid.UUID, triggered_by: str
    ) -> uuid.UUID: ...

    async def get_audit(self, audit_id: uuid.UUID) -> AuditInfo | None: ...

    async def get_site(self, site_id: uuid.UUID) -> SiteInfo | None: ...

    async def update_audit(self, audit_id: uuid.UUID, **fields) -> None: ...

    async def add_issues(
        self, audit_id: uuid.UUID, issues: list[dict]
    ) -> None: ...

    async def touch_site_last_audit(
        self, site_id: uuid.UUID, when: datetime
    ) -> None: ...

    async def list_active_webhooks(
        self, event: str
    ) -> list[WebhookInfo]: ...

    async def touch_webhook(
        self, webhook_id: uuid.UUID, when: datetime
    ) -> None: ...


_SCORE_KEYS = (
    "overall",
    "technical",
    "content",
    "eeeat",
    "performance",
    "structure",
)


async def run_audit(
    audit_id: uuid.UUID,
    repo: AuditRepository,
    *,
    webhook_sender: Sender | None = None,
) -> None:
    """Execute one audit end to end. Designed to run as a FastAPI
    BackgroundTask; never raises (failures are recorded on the audit row and
    dispatched as `audit.failed`)."""
    audit = await repo.get_audit(audit_id)
    if audit is None:
        logger.error("run_audit: audit %s not found", audit_id)
        return

    site = await repo.get_site(audit.site_id)
    event = "audit.failed"
    score_overall = None
    counts = {"critical": 0, "warning": 0, "info": 0}

    try:
        if site is None:
            raise RuntimeError(f"site {audit.site_id} not found")

        await repo.update_audit(
            audit_id, status="crawling", started_at=_now()
        )
        pages = await crawl_site(site.url, site.max_pages)

        await repo.update_audit(
            audit_id,
            status="analysing",
            pages_crawled=len(pages),
            crawl_data=pages,
        )
        issues = evaluate_pages(pages)

        await repo.update_audit(audit_id, status="scoring")
        scores = calculate_score(issues)
        counts = count_by_severity(issues)
        gsc = await get_gsc_performance(site.url)
        analysis = await analyse_audit(site.url, pages, issues, scores, gsc)
        # Addendum v1.1 — backlink data (mock unless DataForSEO configured)
        backlinks = await get_backlink_data(site.domain)

        await repo.add_issues(audit_id, issues)
        completed = _now()
        await repo.update_audit(
            audit_id,
            status="complete",
            completed_at=completed,
            score_overall=scores["overall"],
            score_technical=scores["technical"],
            score_content=scores["content"],
            score_eeeat=scores["eeeat"],
            score_performance=scores["performance"],
            score_structure=scores["structure"],
            issues_critical=counts["critical"],
            issues_warning=counts["warning"],
            issues_info=counts["info"],
            gsc_data=gsc,
            analysis_summary=analysis["summary"],
            quick_wins=analysis["quick_wins"],
            audit_metadata={"backlinks": backlinks},
        )
        await repo.touch_site_last_audit(site.id, completed)
        score_overall = scores["overall"]
        event = "audit.complete"
        logger.info("Audit %s complete (score=%s)", audit_id, score_overall)

    except Exception as exc:  # noqa: BLE001 — record failure, never crash the task
        logger.exception("Audit %s failed", audit_id)
        await repo.update_audit(
            audit_id,
            status="failed",
            error_message=str(exc),
            completed_at=_now(),
        )
        event = "audit.failed"

    await _fire_webhooks(
        repo,
        event,
        {
            "audit_id": str(audit_id),
            "site_id": str(audit.site_id),
            "site_url": site.url if site else None,
            "score_overall": score_overall,
            "issues_critical": counts["critical"],
            "issues_warning": counts["warning"],
            "status": "complete" if event == "audit.complete" else "failed",
        },
        sender=webhook_sender,
    )


async def _fire_webhooks(
    repo: AuditRepository,
    event: str,
    data: dict,
    *,
    sender: Sender | None,
) -> None:
    try:
        subs = await repo.list_active_webhooks(event)
        if not subs:
            return
        results = await deliver(subs, event, data, sender=sender)
        when = _now()
        for webhook_id, delivered in results:
            if delivered:
                await repo.touch_webhook(webhook_id, when)
    except Exception:  # noqa: BLE001 — webhook problems must not affect the audit
        logger.warning("Webhook dispatch errored for %s", event, exc_info=True)


# The production implementation of AuditRepository lives in
# services/repository.py (SqlAlchemyRepository), which also serves the
# routers. It structurally satisfies the AuditRepository protocol above.
