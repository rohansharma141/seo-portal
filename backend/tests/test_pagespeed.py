"""Addendum v1.2 — PageSpeed Insights integration. The real HTTP fetch is
monkeypatched so tests are fast, deterministic and offline."""

import uuid

import pytest

from config import settings
from services import pagespeed
from services.audit_pipeline import AuditInfo, SiteInfo, run_audit
from services.pagespeed import (
    _mock_psi,
    _parse_psi,
    apply_psi_to_pages,
    get_pagespeed_batch,
    get_pagespeed_data,
    psi_opportunity_issues,
    select_psi_urls,
)
from utils.seo_rules import evaluate_page

# Synthetic PSI API response.
PSI_JSON = {
    "lighthouseResult": {
        "categories": {"performance": {"score": 0.72}},
        "audits": {
            "largest-contentful-paint": {"numericValue": 3600},
            "cumulative-layout-shift": {"numericValue": 0.04},
            "interaction-to-next-paint": {"numericValue": 250},
            "first-contentful-paint": {"numericValue": 1800},
            "total-blocking-time": {"numericValue": 320},
            "speed-index": {"numericValue": 4100},
            "render-blocking-resources": {
                "title": "Eliminate render-blocking resources",
                "description": "Resources are blocking the first paint.",
                "details": {"overallSavingsMs": 1500},
            },
            "unused-css-rules": {
                "title": "Reduce unused CSS",
                "description": "Remove dead rules from stylesheets.",
                "details": {"overallSavingsMs": 300},
            },
            "uses-text-compression": {
                "title": "Enable text compression",
                "description": "Compress text resources.",
                "details": {"overallSavingsMs": 0},
            },
        },
    },
    "loadingExperience": {
        "metrics": {"LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2900}}
    },
}


# ── parsing ─────────────────────────────────────────────────────────────
def test_parse_psi_shape():
    d = _parse_psi(PSI_JSON, "https://kedar.estate", "mobile")
    assert d["data_source"] == "psi_api"
    assert d["performance_score"] == 72
    assert d["lab"] == {
        "lcp_ms": 3600,
        "cls": 0.04,
        "inp_ms": 250,
        "fcp_ms": 1800,
        "tbt_ms": 320,
        "speed_index_ms": 4100,
    }
    assert d["field"]["has_field_data"] is True
    assert d["field"]["lcp_ms"] == 2900
    # only opportunities with savings_ms > 0
    assert {o["id"] for o in d["opportunities"]} == {
        "render-blocking-resources",
        "unused-css-rules",
    }


def test_mock_psi_shape():
    d = _mock_psi("https://kedar.estate", "mobile", error="timeout")
    assert d["data_source"] == "mock"
    assert d["performance_score"] == 0
    assert d["lab"]["lcp_ms"] is None
    assert d["error"] == "timeout"
    assert "PSI_API_KEY" in d["note"]


# ── fetch + fallback ────────────────────────────────────────────────────
async def test_get_pagespeed_data_success(monkeypatch):
    async def fake_fetch(params):
        return PSI_JSON

    monkeypatch.setattr(pagespeed, "_fetch_psi", fake_fetch)
    d = await get_pagespeed_data("https://kedar.estate")
    assert d["data_source"] == "psi_api" and d["performance_score"] == 72


async def test_get_pagespeed_data_falls_back_to_mock(monkeypatch):
    async def boom(params):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(pagespeed, "_fetch_psi", boom)
    d = await get_pagespeed_data("https://kedar.estate")
    assert d["data_source"] == "mock" and d["error"] == "rate limited"


async def test_get_pagespeed_batch_caps_url_count(monkeypatch):
    async def fake_fetch(params):
        return PSI_JSON

    monkeypatch.setattr(pagespeed, "_fetch_psi", fake_fetch)
    urls = [f"https://x{i}.test" for i in range(8)]
    assert len(await get_pagespeed_batch(urls, max_urls=3)) == 3
    assert await get_pagespeed_batch([], max_urls=3) == []


# ── helpers ─────────────────────────────────────────────────────────────
def test_select_psi_urls_homepage_first_and_capped():
    pages = [
        {"url": "https://a/blog", "is_homepage": False},
        {"url": "https://a/", "is_homepage": True},
        {"url": "https://a/projects", "is_homepage": False},
        {"url": "https://a/blog", "is_homepage": False},  # dup
    ]
    assert select_psi_urls(pages, 5)[0] == "https://a/"
    assert len(select_psi_urls(pages, 2)) == 2


def test_apply_psi_to_pages_merges_only_real_data():
    pages = [
        {"url": "https://a/", "lcp_ms": 2800, "cls_score": 0.05},
        {"url": "https://a/x", "lcp_ms": 1800, "cls_score": 0.04},
    ]
    psi = [
        _parse_psi(PSI_JSON, "https://a/", "mobile"),  # psi_api
        _mock_psi("https://a/x", "mobile"),  # mock — must not degrade
    ]
    apply_psi_to_pages(pages, psi)
    assert pages[0]["lcp_ms"] == 3600  # overwritten with real value
    assert pages[0]["inp_ms"] == 250
    assert pages[1]["lcp_ms"] == 1800  # mock result left the page untouched


def test_psi_opportunity_issues_severity():
    parsed = _parse_psi(PSI_JSON, "https://a/", "mobile")
    issues = psi_opportunity_issues(parsed)
    by_rule = {i["rule_id"]: i for i in issues}
    assert by_rule["psi_render-blocking-resources"]["severity"] == "warning"
    assert by_rule["psi_unused-css-rules"]["severity"] == "info"
    assert all(i["category"] == "performance" for i in issues)


def test_inp_rule_fires_on_real_inp():
    ids = {i["rule_id"] for i in evaluate_page({"url": "https://a", "inp_ms": 250})}
    assert "inp_poor" in ids
    ids_ok = {i["rule_id"] for i in evaluate_page({"url": "https://a", "inp_ms": 150})}
    assert "inp_poor" not in ids_ok


# ── run_audit with PSI enabled ──────────────────────────────────────────
class FakeRepo:
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

    async def get_site(self, sid):
        s = self.sites.get(sid)
        return (
            SiteInfo(id=s["id"], url=s["url"], max_pages=s["max_pages"], domain=s["domain"])
            if s
            else None
        )

    async def create_audit(self, site_id, triggered_by):
        aid = uuid.uuid4()
        self.audits[aid] = {"id": aid, "site_id": site_id, "status": "pending"}
        return aid

    async def get_audit(self, aid):
        a = self.audits.get(aid)
        return AuditInfo(id=a["id"], site_id=a["site_id"], status=a["status"]) if a else None

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


async def test_run_audit_with_psi_enabled(monkeypatch):
    async def fake_fetch(params):
        return PSI_JSON

    monkeypatch.setattr(pagespeed, "_fetch_psi", fake_fetch)
    monkeypatch.setattr(settings, "psi_enabled", True)

    repo = FakeRepo()
    aid = await repo.create_audit(repo.site_id, "manual")
    await run_audit(aid, repo)

    a = repo.audits[aid]
    assert a["status"] == "complete"
    psi = a["audit_metadata"]["pagespeed"]
    assert len(psi) == 3  # mock crawl returns 3 pages
    assert all(r["data_source"] == "psi_api" for r in psi)
    # PSI opportunities became performance issues
    assert any(i["rule_id"].startswith("psi_") for i in repo.issues)
    # real INP (250ms) merged into pages -> inp_poor raised
    assert any(i["rule_id"] == "inp_poor" for i in repo.issues)
