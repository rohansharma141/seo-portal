"""API tests — Section 7. Routers exercised through TestClient with an
in-memory fake repository and dependency overrides (no DB / no Supabase)."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from main import app
from middleware.auth import (
    Principal,
    create_access_token,
    generate_api_token,
    get_principal,
    hash_token,
)
from services import webhook_dispatcher
from services.audit_pipeline import AuditInfo, SiteInfo
from services.repository import get_repository

NOW = datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc)


class FakeRepo:
    """In-memory implementation of every repository method the routers,
    auth and pipeline call."""

    def __init__(self):
        self.site_id = uuid.uuid4()
        self.audit_id = uuid.uuid4()
        self.sites = {
            self.site_id: {
                "id": self.site_id,
                "name": "Kedar Estate",
                "domain": "kedar.estate",
                "url": "https://kedar.estate",
                "site_type": "brokerage",
                "schedule": "weekly",
                "is_active": True,
                "max_pages": 100,
                "last_audit_at": NOW,
                "created_at": NOW,
            }
        }
        self.audits = {
            self.audit_id: {
                "id": self.audit_id,
                "site_id": self.site_id,
                "status": "complete",
                "triggered_by": "manual",
                "score_overall": 87,
                "score_technical": 65,
                "score_content": 93,
                "score_eeeat": 100,
                "score_performance": 94,
                "score_structure": 100,
                "pages_crawled": 3,
                "issues_critical": 1,
                "issues_warning": 6,
                "issues_info": 3,
                "analysis_summary": "Audit complete for https://kedar.estate.",
                "quick_wins": [{"title": "x", "effort": "low", "impact": "high", "description": "y"}],
                "gsc_data": {"data_source": "mock"},
                "started_at": NOW,
                "completed_at": NOW,
                "created_at": NOW,
            }
        }
        self.issues = [
            {
                "id": uuid.uuid4(),
                "audit_id": self.audit_id,
                "page_url": "https://kedar.estate",
                "category": "technical",
                "severity": "critical",
                "rule_id": "broken_internal_links",
                "rule_name": "Broken Internal Links",
                "description": "d",
                "fix_suggestion": "f",
                "affected_value": None,
                "expected_value": None,
            }
        ]
        self.tokens: list[dict] = []
        self.webhooks: list[dict] = []
        self.touched_token = None

    # sites
    async def list_sites(self):
        return [self._site_out(s) for s in self.sites.values()]

    def _site_out(self, s):
        return {**{k: s[k] for k in (
            "id", "name", "domain", "url", "site_type", "schedule",
            "is_active", "last_audit_at", "created_at")}, "last_score": 87}

    async def create_site(self, data):
        sid = uuid.uuid4()
        rec = {"id": sid, "is_active": True, "last_audit_at": None,
               "created_at": NOW, **data}
        self.sites[sid] = rec
        return {**self._site_out(rec), "last_score": None}

    async def get_site_detail(self, site_id):
        s = self.sites.get(site_id)
        if not s:
            return None
        out = self._site_out(s)
        out["last_audit"] = {
            "audit_id": self.audit_id, "status": "complete",
            "score_overall": 87, "completed_at": NOW,
        }
        return out

    async def update_site(self, site_id, fields):
        s = self.sites.get(site_id)
        if not s:
            return None
        s.update(fields)
        return await self.get_site_detail(site_id)

    async def soft_delete_site(self, site_id):
        s = self.sites.get(site_id)
        if not s:
            return False
        s["is_active"] = False
        return True

    # pipeline seam
    async def get_site(self, site_id):
        s = self.sites.get(site_id)
        return SiteInfo(id=s["id"], url=s["url"], max_pages=s["max_pages"]) if s else None

    async def create_audit(self, site_id, triggered_by):
        aid = uuid.uuid4()
        self.audits[aid] = {
            "id": aid, "site_id": site_id, "status": "pending",
            "triggered_by": triggered_by, "pages_crawled": 0,
            "created_at": NOW, "score_overall": None,
        }
        return aid

    async def get_audit(self, audit_id):
        a = self.audits.get(audit_id)
        return AuditInfo(id=a["id"], site_id=a["site_id"], status=a["status"]) if a else None

    async def update_audit(self, audit_id, **fields):
        self.audits[audit_id].update(fields)

    async def add_issues(self, audit_id, issues):
        for i in issues:
            self.issues.append({**i, "id": uuid.uuid4(), "audit_id": audit_id})

    async def touch_site_last_audit(self, site_id, when):
        self.sites[site_id]["last_audit_at"] = when

    # audits read
    async def get_audit_out(self, audit_id):
        a = self.audits.get(audit_id)
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
                "priority_actions": [],
                "positive_signals": [],
            },
            "gsc_snapshot": a.get("gsc_data", {}),
            "started_at": a.get("started_at"),
            "completed_at": a.get("completed_at"),
        }

    async def list_audits(self, site_id, limit, offset):
        rows = [a for a in self.audits.values()
                if site_id is None or a["site_id"] == site_id]
        items = [{
            "id": a["id"], "site_id": a["site_id"], "status": a["status"],
            "score_overall": a.get("score_overall"),
            "triggered_by": a.get("triggered_by", "manual"),
            "created_at": a["created_at"], "completed_at": a.get("completed_at"),
        } for a in rows[offset:offset + limit]]
        return items, len(rows)

    async def get_audit_status(self, audit_id):
        a = self.audits.get(audit_id)
        if not a:
            return None
        return {
            "audit_id": a["id"], "status": a["status"],
            "progress_message": a["status"],
            "pages_crawled": a.get("pages_crawled", 0),
            "started_at": a.get("started_at"),
        }

    async def get_issues(self, audit_id, severity, category):
        if audit_id not in self.audits:
            return None
        rows = [i for i in self.issues if i["audit_id"] == audit_id
                and (severity is None or i["severity"] == severity)
                and (category is None or i["category"] == category)]
        return [{k: v for k, v in r.items() if k != "audit_id"} for r in rows], len(rows)

    # reports
    async def site_history(self, site_id):
        if site_id not in self.sites:
            return None
        return {
            "site_id": site_id, "site_name": self.sites[site_id]["name"],
            "audits": [{"audit_id": self.audit_id, "date": "2026-05-17",
                        "score": 87, "critical": 1, "warning": 6}],
            "trend": "+6 points since previous audit",
        }

    async def summary(self):
        return {
            "sites_total": 1, "sites_healthy": 1, "sites_warning": 0,
            "sites_critical": 0, "avg_score_all_sites": 87,
            "total_critical_issues": 1, "total_warning_issues": 6,
            "sites": [{"name": "Kedar Estate", "score": 87,
                       "status": "healthy", "last_audited": "2026-05-17"}],
        }

    async def compare(self, a, b):
        if a not in self.audits or b not in self.audits:
            return None
        return {
            "site_id": self.site_id,
            "a": {"audit_id": a, "date": "2026-05-01", "scores": {},
                  "issues_critical": 2, "issues_warning": 8, "issues_info": 3},
            "b": {"audit_id": b, "date": "2026-05-17", "scores": {},
                  "issues_critical": 1, "issues_warning": 6, "issues_info": 3},
            "score_delta": 13,
        }

    # tokens
    async def list_tokens(self):
        return [{
            "id": t["id"], "name": t["name"],
            "token_prefix": t["token_prefix"], "scopes": t["scopes"],
            "is_active": t["is_active"], "last_used_at": t.get("last_used_at"),
            "expires_at": t.get("expires_at"), "created_at": NOW,
        } for t in self.tokens]

    async def create_token(self, name, scopes, expires_at, token_hash, token_prefix):
        tid = uuid.uuid4()
        self.tokens.append({
            "id": tid, "name": name, "scopes": scopes,
            "expires_at": expires_at, "token_hash": token_hash,
            "token_prefix": token_prefix, "is_active": True,
        })
        return {"id": tid, "name": name, "scopes": scopes}

    async def revoke_token(self, token_id):
        for t in self.tokens:
            if t["id"] == token_id:
                t["is_active"] = False
                return True
        return False

    async def get_tokens_by_prefix(self, prefix):
        return [{
            "id": t["id"], "token_hash": t["token_hash"],
            "scopes": t["scopes"], "is_active": t["is_active"],
            "expires_at": t.get("expires_at"),
        } for t in self.tokens if t["token_prefix"] == prefix]

    async def touch_token_used(self, token_id, when):
        self.touched_token = token_id

    # webhooks
    async def list_webhooks(self):
        return list(self.webhooks)

    async def create_webhook(self, name, url, events, secret):
        rec = {"id": uuid.uuid4(), "name": name, "url": url,
               "events": events, "is_active": True,
               "last_triggered_at": None, "created_at": NOW}
        self.webhooks.append(rec)
        return rec

    async def delete_webhook(self, webhook_id):
        before = len(self.webhooks)
        self.webhooks = [w for w in self.webhooks if w["id"] != webhook_id]
        return len(self.webhooks) < before

    async def list_active_webhooks(self, event):
        return []

    async def touch_webhook(self, webhook_id, when):
        pass


ADMIN = Principal(kind="jwt", subject="admin", scopes={"*"})


@pytest.fixture
def repo():
    return FakeRepo()


@pytest.fixture
def client(repo):
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_principal] = lambda: ADMIN
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── health (Section 7.1) ────────────────────────────────────────────────
def test_health_ok():
    with TestClient(app) as c:
        body = c.get("/health").json()
    assert body["status"] == "ok" and body["version"] == "1.0.0"


# ── sites (7.2) ─────────────────────────────────────────────────────────
def test_list_sites_shape(client, repo):
    r = client.get("/api/v1/sites")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    s = body["sites"][0]
    assert s["domain"] == "kedar.estate" and s["last_score"] == 87


def test_create_get_patch_delete_site(client, repo):
    r = client.post("/api/v1/sites", json={
        "name": "PropOS", "domain": "propos.in", "url": "https://propos.in",
        "site_type": "saas"})
    assert r.status_code == 201
    sid = r.json()["id"]

    assert client.get(f"/api/v1/sites/{sid}").status_code == 200
    r = client.patch(f"/api/v1/sites/{sid}", json={"schedule": "monthly"})
    assert r.json()["schedule"] == "monthly"
    assert client.delete(f"/api/v1/sites/{sid}").json()["status"] == "deleted"

    assert client.get(f"/api/v1/sites/{uuid.uuid4()}").status_code == 404


# ── audits (7.3) ────────────────────────────────────────────────────────
def test_get_audit_shape(client, repo):
    r = client.get(f"/api/v1/audits/{repo.audit_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["scores"]["overall"] == 87
    assert body["issues"] == {"critical": 1, "warning": 6, "info": 3}
    assert set(body["analysis"]) == {
        "summary", "quick_wins", "priority_actions", "positive_signals"}


def test_list_and_status_and_issues(client, repo):
    lst = client.get("/api/v1/audits").json()
    assert lst["total"] == 1 and lst["limit"] == 50

    st = client.get(f"/api/v1/audits/{repo.audit_id}/status").json()
    assert st["status"] == "complete"

    iss = client.get(
        f"/api/v1/audits/{repo.audit_id}/issues?severity=critical").json()
    assert iss["total"] == 1
    assert iss["filters"] == {"severity": "critical", "category": None}
    assert client.get(f"/api/v1/audits/{uuid.uuid4()}/issues").status_code == 404


def test_trigger_audit_runs_pipeline(client, repo):
    r = client.post("/api/v1/audits", json={
        "site_id": str(repo.site_id), "triggered_by": "api"})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "pending" and body["estimated_seconds"] == 120
    new_id = body["audit_id"]
    # TestClient runs the BackgroundTask before returning → audit completed.
    done = client.get(f"/api/v1/audits/{new_id}").json()
    assert done["status"] == "complete"
    assert done["scores"]["overall"] == 87  # mock crawl → pinned score

    assert client.post("/api/v1/audits", json={
        "site_id": str(uuid.uuid4())}).status_code == 404


# ── reports (7.4) ───────────────────────────────────────────────────────
def test_reports(client, repo):
    h = client.get(f"/api/v1/reports/site/{repo.site_id}/history").json()
    assert h["site_name"] == "Kedar Estate" and h["audits"][0]["score"] == 87

    s = client.get("/api/v1/reports/summary").json()
    assert s["sites_total"] == 1 and s["sites"][0]["status"] == "healthy"

    c = client.get(
        f"/api/v1/reports/site/{repo.site_id}/compare"
        f"?a={repo.audit_id}&b={repo.audit_id}").json()
    assert c["score_delta"] == 13


# ── tokens (7.5) ────────────────────────────────────────────────────────
def test_token_lifecycle_admin_only(client, repo):
    r = client.post("/api/v1/tokens", json={
        "name": "PropOS Prod", "scopes": ["audit:read", "audit:write"]})
    assert r.status_code == 201
    body = r.json()
    assert body["token"].startswith("pse_")
    assert body["token_prefix"] == body["token"][:8]
    assert "token" not in client.get("/api/v1/tokens").json()["tokens"][0]

    tid = body["id"]
    assert client.delete(f"/api/v1/tokens/{tid}").json()["status"] == "revoked"

    bad = client.post("/api/v1/tokens", json={
        "name": "x", "scopes": ["bogus:scope"]})
    assert bad.status_code == 422


# ── webhooks (7.6) ──────────────────────────────────────────────────────
def test_webhook_crud_and_test(client, repo, monkeypatch):
    r = client.post("/api/v1/webhooks", json={
        "name": "PropOS", "url": "https://propos.in/hook",
        "events": ["audit.complete"], "secret": "s"})
    assert r.status_code == 201
    body = r.json()
    assert "secret" not in body
    wid = body["id"]

    assert client.get("/api/v1/webhooks").json()["total"] == 1

    sent = {}

    async def fake_sender(url, b, headers):
        sent["url"] = url

    monkeypatch.setattr(webhook_dispatcher, "_httpx_sender", fake_sender)
    t = client.post("/api/v1/webhooks/test", json={
        "url": "https://propos.in/hook", "secret": "s"})
    assert t.json()["delivered"] is True and sent["url"] == "https://propos.in/hook"

    assert client.delete(f"/api/v1/webhooks/{wid}").json()["status"] == "deleted"
    assert client.delete(f"/api/v1/webhooks/{uuid.uuid4()}").status_code == 404

    bad = client.post("/api/v1/webhooks", json={
        "name": "x", "url": "https://a", "events": ["nope"]})
    assert bad.status_code == 422


# ── auth (Section 14) ───────────────────────────────────────────────────
def test_auth_required_and_scoped(repo):
    # real auth dependency this time (only repo overridden)
    app.dependency_overrides[get_repository] = lambda: repo
    try:
        with TestClient(app) as c:
            assert c.get("/api/v1/sites").status_code == 401  # no bearer

            limited = create_access_token("u", scopes=["audit:read"])
            h = {"Authorization": f"Bearer {limited}"}
            assert c.get("/api/v1/sites", headers=h).status_code == 403  # needs site:read
            assert c.get("/api/v1/audits", headers=h).status_code == 200

            assert c.get(
                "/api/v1/sites",
                headers={"Authorization": "Bearer not-a-jwt"},
            ).status_code == 401

            # API-token path
            raw, prefix = generate_api_token()
            repo.tokens.append({
                "id": uuid.uuid4(), "name": "t", "scopes": ["audit:read"],
                "token_hash": hash_token(raw), "token_prefix": prefix,
                "is_active": True, "expires_at": None})
            ht = {"Authorization": f"Bearer {raw}"}
            assert c.get("/api/v1/audits", headers=ht).status_code == 200
            assert repo.touched_token is not None
            # token mgmt is admin-only → API token forbidden
            assert c.get("/api/v1/tokens", headers=ht).status_code == 403

            repo.tokens[0]["is_active"] = False
            assert c.get("/api/v1/audits", headers=ht).status_code == 401
    finally:
        app.dependency_overrides.clear()
