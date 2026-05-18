"""Addendum v1.1 — backlink placeholder (Feature 2) and cross-site
comparison (Feature 1). Repository-pattern fakes, no DB."""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app
from middleware.auth import Principal, get_principal
from services import backlinks as backlinks_mod
from services.audit_pipeline import AuditInfo, SiteInfo, run_audit
from services.backlinks import _mock_backlink_data, get_backlink_data
from services.compare_service import CompareError, get_comparison
from services.repository import get_repository

ADMIN = Principal(kind="jwt", subject="admin", scopes={"*"})


# ── Feature 2: backlinks service ────────────────────────────────────────
def test_mock_backlink_shape():
    d = _mock_backlink_data("kedar.estate")
    assert d["domain"] == "kedar.estate"
    assert d["data_source"] == "mock"
    assert d["placeholder_note"] and "DATAFORSEO" in d["placeholder_note"]
    for k in (
        "domain_rank",
        "referring_domains",
        "backlinks_total",
        "broken_backlinks",
        "top_referring_domains",
        "anchor_distribution",
        "new_lost",
        "fetched_at",
    ):
        assert k in d
    assert d["new_lost"] == {
        "new_referring_domains_30d": 0,
        "lost_referring_domains_30d": 0,
    }


async def test_get_backlink_data_mock_when_unconfigured():
    d = await get_backlink_data("propos.in")
    assert d["data_source"] == "mock" and d["domain"] == "propos.in"


async def test_get_backlink_data_placeholder_when_configured(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "dataforseo_login", "x")
    monkeypatch.setattr(settings, "dataforseo_password", "y")
    with pytest.raises(NotImplementedError, match=r"\[PLACEHOLDER\]"):
        await get_backlink_data("kedar.estate")


# ── Shared pipeline fake (Feature 2 end-to-end + audits endpoint) ───────
class PipelineFake:
    def __init__(self):
        self.site_id = uuid.uuid4()
        self.sites = {
            self.site_id: {
                "id": self.site_id,
                "url": "https://kedar.estate",
                "domain": "kedar.estate",
                "max_pages": 100,
            }
        }
        self.audits: dict = {}
        self.issues: list = []

    async def get_site(self, site_id):
        s = self.sites.get(site_id)
        return (
            SiteInfo(
                id=s["id"], url=s["url"], max_pages=s["max_pages"],
                domain=s["domain"],
            )
            if s
            else None
        )

    async def create_audit(self, site_id, triggered_by):
        aid = uuid.uuid4()
        self.audits[aid] = {
            "id": aid, "site_id": site_id, "status": "pending",
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

    async def update_audit(self, aid, **fields):
        self.audits[aid].update(fields)

    async def add_issues(self, aid, issues):
        self.issues.extend(issues)

    async def touch_site_last_audit(self, sid, when):
        pass

    async def list_active_webhooks(self, event):
        return []

    async def touch_webhook(self, wid, when):
        pass

    async def get_audit_out(self, aid):
        a = self.audits.get(aid)
        if not a:
            return None
        return {
            "id": a["id"], "site_id": a["site_id"], "status": a["status"],
            "scores": {
                "overall": a.get("score_overall"),
                "technical": a.get("score_technical"),
                "content": a.get("score_content"),
                "eeeat": a.get("score_eeeat"),
                "performance": a.get("score_performance"),
                "structure": a.get("score_structure"),
            },
            "pages_crawled": a.get("pages_crawled", 0),
            "issues": {
                "critical": a.get("issues_critical", 0),
                "warning": a.get("issues_warning", 0),
                "info": a.get("issues_info", 0),
            },
            "analysis": {
                "summary": a.get("analysis_summary"),
                "quick_wins": a.get("quick_wins", []),
                "priority_actions": [], "positive_signals": [],
            },
            "gsc_snapshot": a.get("gsc_data", {}),
            "backlinks": (a.get("audit_metadata") or {}).get("backlinks", {}),
            "started_at": a.get("started_at"),
            "completed_at": a.get("completed_at"),
        }


async def test_run_audit_stores_backlinks_in_metadata():
    repo = PipelineFake()
    aid = await repo.create_audit(repo.site_id, "manual")
    await run_audit(aid, repo)

    a = repo.audits[aid]
    assert a["status"] == "complete"
    bl = a["audit_metadata"]["backlinks"]
    assert bl["data_source"] == "mock"
    assert bl["domain"] == "kedar.estate"


def test_audit_endpoint_exposes_backlinks():
    repo = PipelineFake()
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_principal] = lambda: ADMIN
    try:
        with TestClient(app) as c:
            r = c.post(
                "/api/v1/audits",
                json={"site_id": str(repo.site_id), "triggered_by": "api"},
            )
            assert r.status_code == 202
            aid = r.json()["audit_id"]
            body = c.get(f"/api/v1/audits/{aid}").json()
            assert body["backlinks"]["data_source"] == "mock"
            assert body["backlinks"]["domain"] == "kedar.estate"
    finally:
        app.dependency_overrides.clear()


# ── Feature 1: cross-site comparison ────────────────────────────────────
class CompareFake:
    def __init__(self):
        self._data: dict = {}

    def add(self, name, domain, site_type, scores=None):
        sid = uuid.uuid4()
        basic = {
            "id": sid, "name": name, "domain": domain,
            "site_type": site_type,
        }
        summary = (
            {
                "audit_id": uuid.uuid4(),
                "audit_date": "2026-05-17T10:00:00+00:00",
                "scores": scores,
                "issues": {"critical": 1, "warning": 5, "info": 2},
                "pages_crawled": 12,
            }
            if scores
            else None
        )
        self._data[str(sid)] = (basic, summary)
        return sid

    async def get_site_basic(self, site_id):
        e = self._data.get(str(site_id))
        return e[0] if e else None

    async def latest_complete_audit_summary(self, site_id):
        e = self._data.get(str(site_id))
        return e[1] if e else None


KEDAR = {"overall": 70, "technical": 70, "content": 80, "eeeat": 65,
         "performance": 75, "structure": 85}
PROPOS = {"overall": 82, "technical": 85, "content": 78, "eeeat": 80,
          "performance": 88, "structure": 79}


async def test_comparison_ranks_leaders_and_gaps():
    repo = CompareFake()
    a = repo.add("Kedar Estate", "kedar.estate", "brokerage", KEDAR)
    b = repo.add("PropOS", "propos.in", "saas", PROPOS)

    out = await get_comparison([str(a), str(b)], repo)

    by_id = {s["site_id"]: s for s in out["sites"]}
    assert by_id[str(b)]["rank"] == 1 and by_id[str(a)]["rank"] == 2
    assert out["leader"]["site_id"] == str(b)
    assert out["category_leaders"]["content"] == str(a)  # 80 > 78
    assert out["category_leaders"]["technical"] == str(b)  # 85 > 70

    # Kedar gaps vs leader: technical 15, eeeat 15, performance 13 (all >10)
    kedar_gaps = {g["category"]: g["gap"] for g in out["gaps"]
                  if g["site_id"] == str(a)}
    assert kedar_gaps == {"technical": 15, "eeeat": 15, "performance": 13}
    assert out["gaps"][0]["note"] == "Largest gap — highest priority to close"
    assert all(g["gap"] > 10 for g in out["gaps"])


async def test_comparison_validation_errors():
    repo = CompareFake()
    a = repo.add("A", "a.com", "other", KEDAR)
    b = repo.add("B", "b.com", "other", PROPOS)
    no_audit = repo.add("C", "c.com", "other", None)

    with pytest.raises(CompareError) as e1:
        await get_comparison([str(a)], repo)
    assert e1.value.status_code == 400

    with pytest.raises(CompareError) as e2:
        await get_comparison([str(a)] * 6, repo)
    assert e2.value.status_code == 400

    with pytest.raises(CompareError) as e3:
        await get_comparison([str(a), str(uuid.uuid4())], repo)
    assert e3.value.status_code == 404

    with pytest.raises(CompareError) as e4:
        await get_comparison([str(a), str(no_audit)], repo)
    assert e4.value.status_code == 422 and "C" in e4.value.detail


def test_compare_endpoint():
    repo = CompareFake()
    a = repo.add("Kedar Estate", "kedar.estate", "brokerage", KEDAR)
    b = repo.add("PropOS", "propos.in", "saas", PROPOS)
    bad = repo.add("NoAudit", "n.com", "other", None)

    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_principal] = lambda: ADMIN
    try:
        with TestClient(app) as c:
            r = c.get(f"/api/v1/reports/compare?site_ids={a},{b}")
            assert r.status_code == 200
            body = r.json()
            assert body["leader"]["site_name"] == "PropOS"
            assert len(body["sites"]) == 2

            assert c.get(
                f"/api/v1/reports/compare?site_ids={a}"
            ).status_code == 400
            assert c.get(
                f"/api/v1/reports/compare?site_ids={a},{uuid.uuid4()}"
            ).status_code == 404
            assert c.get(
                f"/api/v1/reports/compare?site_ids={a},{bad}"
            ).status_code == 422
    finally:
        app.dependency_overrides.clear()
