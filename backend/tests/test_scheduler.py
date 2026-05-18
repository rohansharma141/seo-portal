"""Step 7 verification — scheduler job wiring + run_scheduled_audits, using
an in-memory fake repo (no DB, no time-based firing)."""

import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.audit_pipeline import AuditInfo, SiteInfo
from services.scheduler import configure_jobs, run_scheduled_audits


def test_configure_jobs_registers_weekly_and_monthly():
    sched = AsyncIOScheduler(timezone="UTC")
    configure_jobs(sched)
    jobs = {j.id: j for j in sched.get_jobs()}

    assert set(jobs) == {"weekly_audits", "monthly_audits"}

    weekly = jobs["weekly_audits"]
    assert weekly.kwargs == {"schedule": "weekly"}
    assert "day_of_week='mon'" in str(weekly.trigger)
    assert "hour='6'" in str(weekly.trigger)

    monthly = jobs["monthly_audits"]
    assert monthly.kwargs == {"schedule": "monthly"}
    assert "day='1'" in str(monthly.trigger)
    assert "hour='7'" in str(monthly.trigger)


class FakeRepo:
    def __init__(self):
        self.sites: dict = {}
        self.audits: dict = {}
        self.issues: list = []
        self.touched: list = []

    def add_site(self, schedule: str, active: bool = True):
        sid = uuid.uuid4()
        self.sites[sid] = {
            "id": sid,
            "schedule": schedule,
            "is_active": active,
            "url": f"https://site-{sid.hex[:6]}.test",
            "max_pages": 100,
        }
        return sid

    async def list_due_sites(self, schedule):
        return [
            sid
            for sid, s in self.sites.items()
            if s["is_active"] and s["schedule"] == schedule
        ]

    async def create_audit(self, site_id, triggered_by):
        aid = uuid.uuid4()
        self.audits[aid] = {
            "id": aid,
            "site_id": site_id,
            "status": "pending",
            "triggered_by": triggered_by,
        }
        return aid

    async def get_audit(self, aid):
        a = self.audits.get(aid)
        return (
            AuditInfo(id=a["id"], site_id=a["site_id"], status=a["status"])
            if a
            else None
        )

    async def get_site(self, sid):
        s = self.sites.get(sid)
        return (
            SiteInfo(id=s["id"], url=s["url"], max_pages=s["max_pages"])
            if s
            else None
        )

    async def update_audit(self, aid, **fields):
        self.audits[aid].update(fields)

    async def add_issues(self, aid, issues):
        self.issues.extend(issues)

    async def touch_site_last_audit(self, sid, when):
        self.touched.append(sid)

    async def list_active_webhooks(self, event):
        return []

    async def touch_webhook(self, wid, when):
        pass


async def test_run_scheduled_audits_only_due_active_sites():
    repo = FakeRepo()
    a = repo.add_site("weekly")
    b = repo.add_site("weekly")
    repo.add_site("monthly")  # wrong schedule
    repo.add_site("weekly", active=False)  # inactive

    await run_scheduled_audits("weekly", repo)

    assert len(repo.audits) == 2
    assert {x["site_id"] for x in repo.audits.values()} == {a, b}
    assert all(x["status"] == "complete" for x in repo.audits.values())
    assert all(x["triggered_by"] == "scheduled" for x in repo.audits.values())
    assert sorted(repo.touched) == sorted([a, b])


async def test_run_scheduled_audits_no_due_sites_is_noop():
    repo = FakeRepo()
    repo.add_site("monthly")
    await run_scheduled_audits("weekly", repo)
    assert repo.audits == {}


async def test_run_scheduled_audits_isolates_failures(monkeypatch):
    from services import audit_pipeline

    repo = FakeRepo()
    repo.add_site("weekly")
    repo.add_site("weekly")

    async def boom(*a, **k):
        raise RuntimeError("crawler down")

    monkeypatch.setattr(audit_pipeline, "crawl_site", boom)
    await run_scheduled_audits("weekly", repo)

    # both still produced an audit row, both marked failed (not crashed)
    assert len(repo.audits) == 2
    assert all(x["status"] == "failed" for x in repo.audits.values())
