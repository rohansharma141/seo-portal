"""Step 5 verification — run_audit orchestration + webhook signing, exercised
through an in-memory fake repository (no DB / no Supabase needed)."""

import hashlib
import hmac
import json
import uuid

import pytest

from services import audit_pipeline
from services.audit_pipeline import (
    AuditInfo,
    SiteInfo,
    WebhookInfo,
    run_audit,
)
from services.webhook_dispatcher import deliver, sign

SITE_URL = "https://kedar.estate"


class FakeRepo:
    """In-memory AuditRepository implementation for tests."""

    def __init__(self, site: SiteInfo, webhooks=None):
        self._site = site
        self.audits: dict[uuid.UUID, dict] = {}
        self.issues: list[dict] = []
        self.webhooks = webhooks or []
        self.site_last_audit = None
        self.touched_webhooks: list[uuid.UUID] = []

    async def create_audit(self, site_id, triggered_by):
        aid = uuid.uuid4()
        self.audits[aid] = {
            "id": aid,
            "site_id": site_id,
            "status": "pending",
            "triggered_by": triggered_by,
        }
        return aid

    async def get_audit(self, audit_id):
        a = self.audits.get(audit_id)
        return (
            AuditInfo(id=a["id"], site_id=a["site_id"], status=a["status"])
            if a
            else None
        )

    async def get_site(self, site_id):
        return self._site if site_id == self._site.id else None

    async def update_audit(self, audit_id, **fields):
        self.audits[audit_id].update(fields)

    async def add_issues(self, audit_id, issues):
        for i in issues:
            self.issues.append({**i, "audit_id": audit_id})

    async def touch_site_last_audit(self, site_id, when):
        self.site_last_audit = when

    async def list_active_webhooks(self, event):
        return [
            w
            for w in self.webhooks
            if getattr(w, "is_active", True) and event in w.events
        ]

    async def touch_webhook(self, webhook_id, when):
        self.touched_webhooks.append(webhook_id)


class Hook(WebhookInfo):
    def __init__(self, *, url, secret, events, is_active=True):
        super().__init__(id=uuid.uuid4(), url=url, secret=secret, events=events)
        self.is_active = is_active


def make_repo(webhooks=None):
    site = SiteInfo(id=uuid.uuid4(), url=SITE_URL, max_pages=100)
    return FakeRepo(site, webhooks=webhooks), site


class CaptureSender:
    def __init__(self, fail_urls=()):
        self.calls = []
        self._fail = set(fail_urls)

    async def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        if url in self._fail:
            raise RuntimeError("endpoint down")


# ── webhook signing / delivery ──────────────────────────────────────────
def test_sign_is_hmac_sha256_hex():
    sig = sign("s3cret", b"payload")
    assert sig == hmac.new(b"s3cret", b"payload", hashlib.sha256).hexdigest()
    assert len(sig) == 64 and sig == sig.lower()


async def test_deliver_signs_only_when_secret_present():
    signed = Hook(url="https://a.test", secret="k", events=["e"])
    unsigned = Hook(url="https://b.test", secret=None, events=["e"])
    sender = CaptureSender()
    results = await deliver([signed, unsigned], "e", {"x": 1}, sender=sender)

    assert [ok for _, ok in results] == [True, True]
    _, body_a, headers_a = sender.calls[0]
    _, _, headers_b = sender.calls[1]
    assert headers_a["X-SEO-Signature"] == "sha256=" + sign("k", body_a)
    assert "X-SEO-Signature" not in headers_b


async def test_deliver_is_best_effort():
    ok_hook = Hook(url="https://ok.test", secret=None, events=["e"])
    bad_hook = Hook(url="https://bad.test", secret=None, events=["e"])
    sender = CaptureSender(fail_urls=["https://bad.test"])
    results = await deliver([ok_hook, bad_hook], "e", {}, sender=sender)
    assert dict((str(i), ok) for i, ok in results)  # no exception raised
    assert sorted(ok for _, ok in results) == [False, True]


# ── run_audit ───────────────────────────────────────────────────────────
async def test_run_audit_happy_path():
    hook = Hook(
        url="https://propos.test/webhook",
        secret="whsec",
        events=["audit.complete", "audit.failed"],
    )
    repo, site = make_repo([hook])
    sender = CaptureSender()

    audit_id = await repo.create_audit(site.id, "manual")
    await run_audit(audit_id, repo, webhook_sender=sender)

    a = repo.audits[audit_id]
    assert a["status"] == "complete"
    assert a["pages_crawled"] == 3
    assert (
        a["score_overall"],
        a["score_technical"],
        a["score_content"],
        a["score_eeeat"],
        a["score_performance"],
        a["score_structure"],
    ) == (87, 65, 93, 100, 94, 100)
    assert (a["issues_critical"], a["issues_warning"], a["issues_info"]) == (
        1,
        6,
        3,
    )
    assert len(repo.issues) == 10
    assert SITE_URL in a["analysis_summary"] and "87" in a["analysis_summary"]
    assert len(a["quick_wins"]) == 3
    assert repo.site_last_audit is not None
    assert a["started_at"] is not None and a["completed_at"] is not None

    # webhook fired, signed, with the Section 7.6 payload
    assert len(sender.calls) == 1
    url, body, headers = sender.calls[0]
    assert url == hook.url
    assert headers["X-SEO-Signature"] == "sha256=" + sign("whsec", body)
    envelope = json.loads(body)
    assert envelope["event"] == "audit.complete"
    assert envelope["data"] == {
        "audit_id": str(audit_id),
        "site_id": str(site.id),
        "site_url": SITE_URL,
        "score_overall": 87,
        "issues_critical": 1,
        "issues_warning": 6,
        "status": "complete",
    }
    assert hook.id in repo.touched_webhooks


async def test_run_audit_failure_path(monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("crawler exploded")

    monkeypatch.setattr(audit_pipeline, "crawl_site", boom)

    hook = Hook(
        url="https://propos.test/webhook",
        secret=None,
        events=["audit.complete", "audit.failed"],
    )
    repo, site = make_repo([hook])
    sender = CaptureSender()

    audit_id = await repo.create_audit(site.id, "scheduled")
    await run_audit(audit_id, repo, webhook_sender=sender)

    a = repo.audits[audit_id]
    assert a["status"] == "failed"
    assert a["error_message"] == "crawler exploded"
    assert a["completed_at"] is not None
    assert repo.issues == []  # nothing persisted on failure

    assert len(sender.calls) == 1
    envelope = json.loads(sender.calls[0][1])
    assert envelope["event"] == "audit.failed"
    assert envelope["data"]["status"] == "failed"
    assert envelope["data"]["score_overall"] is None


async def test_run_audit_only_fires_subscribed_active_webhooks():
    subscribed = Hook(
        url="https://sub.test", secret=None, events=["audit.complete"]
    )
    other_event = Hook(
        url="https://other.test", secret=None, events=["audit.failed"]
    )
    inactive = Hook(
        url="https://off.test",
        secret=None,
        events=["audit.complete"],
        is_active=False,
    )
    repo, site = make_repo([subscribed, other_event, inactive])
    sender = CaptureSender()

    audit_id = await repo.create_audit(site.id, "api")
    await run_audit(audit_id, repo, webhook_sender=sender)

    called_urls = {c[0] for c in sender.calls}
    assert called_urls == {"https://sub.test"}


async def test_run_audit_missing_audit_is_safe():
    repo, _ = make_repo()
    sender = CaptureSender()
    await run_audit(uuid.uuid4(), repo, webhook_sender=sender)
    assert sender.calls == []  # no audit → no-op, no crash
