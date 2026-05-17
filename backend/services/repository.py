"""Production persistence — SQLAlchemy implementation of every data
operation the routers, auth and pipeline need.

Per the agreed test strategy, routers/auth depend on ``get_repository`` and
tests override it with an in-memory fake (no DB / no Supabase). This concrete
class is the real Postgres path; it also structurally satisfies the
pipeline's ``AuditRepository`` protocol.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update

from database import get_sessionmaker
from services.audit_pipeline import AuditInfo, SiteInfo, WebhookInfo


def _date(dt: datetime | None) -> str | None:
    return dt.date().isoformat() if dt else None


def _status_message(status: str, pages: int) -> str:
    return {
        "pending": "Audit queued.",
        "crawling": f"Crawling… ({pages} pages so far)",
        "analysing": "Running SEO rules…",
        "scoring": "Scoring categories…",
        "complete": "Audit complete.",
        "failed": "Audit failed.",
    }.get(status, status)


def health_status(score: int | None) -> str:
    """Section 8 colour bands: Emerald 80+, Amber 50–79, Red <50."""
    if score is None:
        return "unknown"
    if score >= 80:
        return "healthy"
    if score >= 50:
        return "warning"
    return "critical"


class SqlAlchemyRepository:
    def __init__(self, sessionmaker):
        self._sm = sessionmaker

    # ── helpers ────────────────────────────────────────────────────────
    async def _latest_complete_audit(self, s, site_id):
        from models import Audit

        return (
            await s.execute(
                select(Audit)
                .where(Audit.site_id == site_id, Audit.status == "complete")
                .order_by(Audit.completed_at.desc().nullslast())
                .limit(1)
            )
        ).scalar_one_or_none()

    def _site_out(self, site, last_audit) -> dict:
        return {
            "id": site.id,
            "name": site.name,
            "domain": site.domain,
            "url": site.url,
            "site_type": site.site_type,
            "schedule": site.schedule,
            "is_active": site.is_active,
            "last_audit_at": site.last_audit_at,
            "last_score": last_audit.score_overall if last_audit else None,
            "created_at": site.created_at,
        }

    # ── sites (Section 7.2) ────────────────────────────────────────────
    async def list_sites(self) -> list[dict]:
        from models import Site

        async with self._sm() as s:
            sites = (
                await s.execute(select(Site).order_by(Site.created_at.desc()))
            ).scalars().all()
            out = []
            for site in sites:
                la = await self._latest_complete_audit(s, site.id)
                out.append(self._site_out(site, la))
            return out

    async def create_site(self, data: dict) -> dict:
        from models import Site

        async with self._sm() as s:
            site = Site(**data)
            s.add(site)
            await s.commit()
            await s.refresh(site)
            return self._site_out(site, None)

    async def get_site_detail(self, site_id: uuid.UUID) -> dict | None:
        from models import Site

        async with self._sm() as s:
            site = await s.get(Site, site_id)
            if site is None:
                return None
            la = await self._latest_complete_audit(s, site.id)
            out = self._site_out(site, la)
            out["last_audit"] = (
                {
                    "audit_id": la.id,
                    "status": la.status,
                    "score_overall": la.score_overall,
                    "completed_at": la.completed_at,
                }
                if la
                else None
            )
            return out

    async def update_site(
        self, site_id: uuid.UUID, fields: dict
    ) -> dict | None:
        from models import Site

        if not fields:
            return await self.get_site_detail(site_id)
        async with self._sm() as s:
            site = await s.get(Site, site_id)
            if site is None:
                return None
            for k, v in fields.items():
                setattr(site, k, v)
            await s.commit()
        return await self.get_site_detail(site_id)

    async def soft_delete_site(self, site_id: uuid.UUID) -> bool:
        from models import Site

        async with self._sm() as s:
            site = await s.get(Site, site_id)
            if site is None:
                return False
            site.is_active = False
            await s.commit()
            return True

    # ── pipeline seam (AuditRepository protocol) ───────────────────────
    async def get_site(self, site_id) -> SiteInfo | None:
        from models import Site

        async with self._sm() as s:
            site = await s.get(Site, site_id)
            return (
                SiteInfo(id=site.id, url=site.url, max_pages=site.max_pages)
                if site
                else None
            )

    async def touch_site_last_audit(self, site_id, when) -> None:
        from models import Site

        async with self._sm() as s:
            await s.execute(
                update(Site).where(Site.id == site_id).values(
                    last_audit_at=when
                )
            )
            await s.commit()

    async def create_audit(self, site_id, triggered_by) -> uuid.UUID:
        from models import Audit

        async with self._sm() as s:
            audit = Audit(
                site_id=site_id, triggered_by=triggered_by, status="pending"
            )
            s.add(audit)
            await s.commit()
            await s.refresh(audit)
            return audit.id

    async def get_audit(self, audit_id) -> AuditInfo | None:
        from models import Audit

        async with self._sm() as s:
            a = await s.get(Audit, audit_id)
            return (
                AuditInfo(id=a.id, site_id=a.site_id, status=a.status)
                if a
                else None
            )

    async def update_audit(self, audit_id, **fields) -> None:
        from models import Audit

        async with self._sm() as s:
            await s.execute(
                update(Audit).where(Audit.id == audit_id).values(**fields)
            )
            await s.commit()

    async def add_issues(self, audit_id, issues) -> None:
        from models import AuditIssue

        if not issues:
            return
        async with self._sm() as s:
            s.add_all(
                AuditIssue(
                    audit_id=audit_id,
                    page_url=i.get("page_url"),
                    category=i["category"],
                    severity=i["severity"],
                    rule_id=i["rule_id"],
                    rule_name=i["rule_name"],
                    description=i["description"],
                    fix_suggestion=i["fix_suggestion"],
                    affected_value=i.get("affected_value"),
                    expected_value=i.get("expected_value"),
                )
                for i in issues
            )
            await s.commit()

    # ── audits (Section 7.3) ───────────────────────────────────────────
    @staticmethod
    def _audit_out(a) -> dict:
        return {
            "id": a.id,
            "site_id": a.site_id,
            "status": a.status,
            "scores": {
                "overall": a.score_overall,
                "technical": a.score_technical,
                "content": a.score_content,
                "eeeat": a.score_eeeat,
                "performance": a.score_performance,
                "structure": a.score_structure,
            },
            "pages_crawled": a.pages_crawled or 0,
            "issues": {
                "critical": a.issues_critical or 0,
                "warning": a.issues_warning or 0,
                "info": a.issues_info or 0,
            },
            "analysis": {
                "summary": a.analysis_summary,
                "quick_wins": a.quick_wins or [],
                # Section 4.2 only persists summary + quick_wins.
                "priority_actions": [],
                "positive_signals": [],
            },
            "gsc_snapshot": a.gsc_data or {},
            "started_at": a.started_at,
            "completed_at": a.completed_at,
        }

    async def get_audit_out(self, audit_id) -> dict | None:
        from models import Audit

        async with self._sm() as s:
            a = await s.get(Audit, audit_id)
            return self._audit_out(a) if a else None

    async def list_audits(
        self, site_id: uuid.UUID | None, limit: int, offset: int
    ) -> tuple[list[dict], int]:
        from models import Audit

        async with self._sm() as s:
            base = select(Audit)
            count_q = select(func.count()).select_from(Audit)
            if site_id is not None:
                base = base.where(Audit.site_id == site_id)
                count_q = count_q.where(Audit.site_id == site_id)
            total = (await s.execute(count_q)).scalar_one()
            rows = (
                await s.execute(
                    base.order_by(Audit.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).scalars().all()
            items = [
                {
                    "id": a.id,
                    "site_id": a.site_id,
                    "status": a.status,
                    "score_overall": a.score_overall,
                    "triggered_by": a.triggered_by,
                    "created_at": a.created_at,
                    "completed_at": a.completed_at,
                }
                for a in rows
            ]
            return items, total

    async def get_audit_status(self, audit_id) -> dict | None:
        from models import Audit

        async with self._sm() as s:
            a = await s.get(Audit, audit_id)
            if a is None:
                return None
            return {
                "audit_id": a.id,
                "status": a.status,
                "progress_message": _status_message(
                    a.status, a.pages_crawled or 0
                ),
                "pages_crawled": a.pages_crawled or 0,
                "started_at": a.started_at,
            }

    async def get_issues(
        self,
        audit_id: uuid.UUID,
        severity: str | None,
        category: str | None,
    ) -> tuple[list[dict], int] | None:
        from models import Audit, AuditIssue

        async with self._sm() as s:
            if await s.get(Audit, audit_id) is None:
                return None
            q = select(AuditIssue).where(AuditIssue.audit_id == audit_id)
            if severity:
                q = q.where(AuditIssue.severity == severity)
            if category:
                q = q.where(AuditIssue.category == category)
            rows = (await s.execute(q)).scalars().all()
            issues = [
                {
                    "id": r.id,
                    "page_url": r.page_url,
                    "category": r.category,
                    "severity": r.severity,
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "description": r.description,
                    "fix_suggestion": r.fix_suggestion,
                    "affected_value": r.affected_value,
                    "expected_value": r.expected_value,
                }
                for r in rows
            ]
            return issues, len(issues)

    # ── reports (Section 7.4) ──────────────────────────────────────────
    async def site_history(self, site_id: uuid.UUID) -> dict | None:
        from models import Audit, Site

        async with self._sm() as s:
            site = await s.get(Site, site_id)
            if site is None:
                return None
            rows = (
                await s.execute(
                    select(Audit)
                    .where(Audit.site_id == site_id)
                    .order_by(Audit.created_at.desc())
                )
            ).scalars().all()
            audits = [
                {
                    "audit_id": a.id,
                    "date": _date(a.completed_at or a.created_at),
                    "score": a.score_overall,
                    "critical": a.issues_critical or 0,
                    "warning": a.issues_warning or 0,
                }
                for a in rows
            ]
            scored = [a for a in rows if a.score_overall is not None]
            if len(scored) >= 2:
                delta = scored[0].score_overall - scored[1].score_overall
                trend = f"{'+' if delta >= 0 else ''}{delta} points since previous audit"
            else:
                trend = "Not enough audits for a trend yet"
            return {
                "site_id": site_id,
                "site_name": site.name,
                "audits": audits,
                "trend": trend,
            }

    async def summary(self) -> dict:
        from models import Site

        async with self._sm() as s:
            sites = (await s.execute(select(Site))).scalars().all()
            healthy = warning = critical = 0
            total_c = total_w = 0
            scores: list[int] = []
            site_rows = []
            for site in sites:
                la = await self._latest_complete_audit(s, site.id)
                score = la.score_overall if la else None
                st = health_status(score)
                if st == "healthy":
                    healthy += 1
                elif st == "warning":
                    warning += 1
                elif st == "critical":
                    critical += 1
                if score is not None:
                    scores.append(score)
                if la:
                    total_c += la.issues_critical or 0
                    total_w += la.issues_warning or 0
                site_rows.append(
                    {
                        "name": site.name,
                        "score": score,
                        "status": st,
                        "last_audited": _date(site.last_audit_at),
                    }
                )
            return {
                "sites_total": len(sites),
                "sites_healthy": healthy,
                "sites_warning": warning,
                "sites_critical": critical,
                "avg_score_all_sites": (
                    round(sum(scores) / len(scores)) if scores else 0
                ),
                "total_critical_issues": total_c,
                "total_warning_issues": total_w,
                "sites": site_rows,
            }

    async def compare(
        self, audit_a: uuid.UUID, audit_b: uuid.UUID
    ) -> dict | None:
        from models import Audit

        async with self._sm() as s:
            a = await s.get(Audit, audit_a)
            b = await s.get(Audit, audit_b)
            if a is None or b is None:
                return None

            def side(x):
                return {
                    "audit_id": x.id,
                    "date": _date(x.completed_at or x.created_at),
                    "scores": {
                        "overall": x.score_overall,
                        "technical": x.score_technical,
                        "content": x.score_content,
                        "eeeat": x.score_eeeat,
                        "performance": x.score_performance,
                        "structure": x.score_structure,
                    },
                    "issues_critical": x.issues_critical or 0,
                    "issues_warning": x.issues_warning or 0,
                    "issues_info": x.issues_info or 0,
                }

            return {
                "site_id": a.site_id,
                "a": side(a),
                "b": side(b),
                "score_delta": (b.score_overall or 0) - (a.score_overall or 0),
            }

    # ── api tokens (Section 7.5) ───────────────────────────────────────
    async def list_tokens(self) -> list[dict]:
        from models import ApiToken

        async with self._sm() as s:
            rows = (
                await s.execute(
                    select(ApiToken).order_by(ApiToken.created_at.desc())
                )
            ).scalars().all()
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "token_prefix": t.token_prefix,
                    "scopes": t.scopes,
                    "is_active": t.is_active,
                    "last_used_at": t.last_used_at,
                    "expires_at": t.expires_at,
                    "created_at": t.created_at,
                }
                for t in rows
            ]

    async def create_token(
        self, name, scopes, expires_at, token_hash, token_prefix
    ) -> dict:
        from models import ApiToken

        async with self._sm() as s:
            tok = ApiToken(
                name=name,
                scopes=scopes,
                expires_at=expires_at,
                token_hash=token_hash,
                token_prefix=token_prefix,
            )
            s.add(tok)
            await s.commit()
            await s.refresh(tok)
            return {"id": tok.id, "name": tok.name, "scopes": tok.scopes}

    async def revoke_token(self, token_id: uuid.UUID) -> bool:
        from models import ApiToken

        async with self._sm() as s:
            tok = await s.get(ApiToken, token_id)
            if tok is None:
                return False
            tok.is_active = False
            await s.commit()
            return True

    async def get_tokens_by_prefix(self, prefix: str) -> list[dict]:
        from models import ApiToken

        async with self._sm() as s:
            rows = (
                await s.execute(
                    select(ApiToken).where(ApiToken.token_prefix == prefix)
                )
            ).scalars().all()
            return [
                {
                    "id": t.id,
                    "token_hash": t.token_hash,
                    "scopes": t.scopes,
                    "is_active": t.is_active,
                    "expires_at": t.expires_at,
                }
                for t in rows
            ]

    async def touch_token_used(self, token_id, when) -> None:
        from models import ApiToken

        async with self._sm() as s:
            await s.execute(
                update(ApiToken)
                .where(ApiToken.id == token_id)
                .values(last_used_at=when)
            )
            await s.commit()

    # ── webhooks (Section 7.6) ─────────────────────────────────────────
    @staticmethod
    def _webhook_out(w) -> dict:
        return {
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "events": w.events,
            "is_active": w.is_active,
            "last_triggered_at": w.last_triggered_at,
            "created_at": w.created_at,
        }

    async def list_webhooks(self) -> list[dict]:
        from models import Webhook

        async with self._sm() as s:
            rows = (
                await s.execute(
                    select(Webhook).order_by(Webhook.created_at.desc())
                )
            ).scalars().all()
            return [self._webhook_out(w) for w in rows]

    async def create_webhook(self, name, url, events, secret) -> dict:
        from models import Webhook

        async with self._sm() as s:
            wh = Webhook(name=name, url=url, events=events, secret=secret)
            s.add(wh)
            await s.commit()
            await s.refresh(wh)
            return self._webhook_out(wh)

    async def delete_webhook(self, webhook_id: uuid.UUID) -> bool:
        from models import Webhook

        async with self._sm() as s:
            wh = await s.get(Webhook, webhook_id)
            if wh is None:
                return False
            await s.execute(delete(Webhook).where(Webhook.id == webhook_id))
            await s.commit()
            return True

    async def list_active_webhooks(self, event: str) -> list[WebhookInfo]:
        from models import Webhook

        async with self._sm() as s:
            rows = (
                await s.execute(
                    select(Webhook).where(Webhook.is_active.is_(True))
                )
            ).scalars().all()
        return [
            WebhookInfo(
                id=w.id, url=w.url, secret=w.secret, events=w.events or []
            )
            for w in rows
            if event in (w.events or [])
        ]

    async def touch_webhook(self, webhook_id, when) -> None:
        from models import Webhook

        async with self._sm() as s:
            await s.execute(
                update(Webhook)
                .where(Webhook.id == webhook_id)
                .values(last_triggered_at=when)
            )
            await s.commit()


# Type alias used in dependency signatures. Tests override get_repository
# with an in-memory fake (duck-typed); no formal Protocol needed.
Repository = SqlAlchemyRepository


def get_repository() -> Repository:
    """FastAPI dependency — overridden in tests."""
    return SqlAlchemyRepository(get_sessionmaker())


__all__ = ["Repository", "SqlAlchemyRepository", "get_repository", "health_status"]
