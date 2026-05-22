"""PageSpeed Insights integration — Addendum v1.2.

Real Core Web Vitals from Google's free PSI API (same engine as
pagespeed.web.dev). Works without a key at low rate limits; `PSI_API_KEY`
raises the limit to 25k/day. Every failure (timeout, rate limit) falls back
to a mock so an audit never fails because of PSI.

PSI calls are slow (10-30s each) — `get_pagespeed_batch` runs them
concurrently and the caller caps the URL count (`PSI_MAX_URLS`).
"""

import asyncio
import logging
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger("seo_portal.pagespeed")

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_psi(params: dict) -> dict:
    """Raw PSI HTTP GET. Isolated so tests can monkeypatch it."""
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(PSI_ENDPOINT, params=params)
        resp.raise_for_status()
        return resp.json()


async def get_pagespeed_data(url: str, strategy: str = "mobile") -> dict:
    """Real Core Web Vitals + performance score for one URL.

    strategy: "mobile" (default — Google ranks mobile-first) or "desktop".
    Returns the PageSpeedData dict; falls back to a mock on any failure.
    """
    params = {"url": url, "strategy": strategy, "category": "performance"}
    if settings.psi_api_key:
        params["key"] = settings.psi_api_key
    try:
        raw = await _fetch_psi(params)
        return _parse_psi(raw, url, strategy)
    except Exception as e:  # noqa: BLE001 — never let PSI fail an audit
        logger.warning("PSI failed for %s (%s); using mock", url, e)
        return _mock_psi(url, strategy, error=str(e))


async def get_pagespeed_batch(
    urls: list[str], strategy: str = "mobile", max_urls: int | None = None
) -> list[dict]:
    """Run PSI for several URLs concurrently, capped at `max_urls`
    (default `settings.psi_max_urls`)."""
    cap = max_urls if max_urls is not None else settings.psi_max_urls
    capped = urls[: max(0, cap)]
    if not capped:
        return []
    return list(
        await asyncio.gather(
            *(get_pagespeed_data(u, strategy) for u in capped)
        )
    )


def _parse_psi(data: dict, url: str, strategy: str) -> dict:
    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    cats = lh.get("categories", {})

    def metric(key: str, field: str = "numericValue"):
        return audits.get(key, {}).get(field)

    field = data.get("loadingExperience", {}).get("metrics", {})

    def field_p75(key: str):
        return field.get(key, {}).get("percentile")

    return {
        "url": url,
        "strategy": strategy,
        "data_source": "psi_api",
        "performance_score": round(
            (cats.get("performance", {}).get("score") or 0) * 100
        ),
        "lab": {
            "lcp_ms": metric("largest-contentful-paint"),
            "cls": metric("cumulative-layout-shift"),
            "inp_ms": metric("interaction-to-next-paint"),
            "fcp_ms": metric("first-contentful-paint"),
            "tbt_ms": metric("total-blocking-time"),
            "speed_index_ms": metric("speed-index"),
        },
        "field": {
            "lcp_ms": field_p75("LARGEST_CONTENTFUL_PAINT_MS"),
            "cls": field_p75("CUMULATIVE_LAYOUT_SHIFT_SCORE"),
            "inp_ms": field_p75("INTERACTION_TO_NEXT_PAINT"),
            "has_field_data": bool(field),
        },
        "opportunities": [
            {
                "id": k,
                "title": v.get("title"),
                "savings_ms": v.get("details", {}).get(
                    "overallSavingsMs", 0
                ),
                "description": v.get("description"),
            }
            for k, v in audits.items()
            if v.get("details", {}).get("overallSavingsMs", 0) > 0
        ][:10],
        "fetched_at": _now_iso(),
    }


def _mock_psi(url: str, strategy: str, error: str | None = None) -> dict:
    return {
        "url": url,
        "strategy": strategy,
        "data_source": "mock",
        "performance_score": 0,
        "lab": {
            "lcp_ms": None,
            "cls": None,
            "inp_ms": None,
            "fcp_ms": None,
            "tbt_ms": None,
            "speed_index_ms": None,
        },
        "field": {"has_field_data": False},
        "opportunities": [],
        "error": error,
        "note": (
            "PSI unavailable. The API works without a key at low rate "
            "limits; set PSI_API_KEY (free, console.cloud.google.com) for "
            "25k/day."
        ),
        "fetched_at": _now_iso(),
    }


# ── Pipeline helpers ────────────────────────────────────────────────────


def select_psi_urls(pages: list[dict], max_urls: int) -> list[str]:
    """Representative URLs to PSI-test: homepage first, then others, capped."""
    homepage = [p["url"] for p in pages if p.get("is_homepage")]
    others = [
        p["url"] for p in pages if not p.get("is_homepage") and p.get("url")
    ]
    ordered: list[str] = []
    for u in homepage + others:
        if u and u not in ordered:
            ordered.append(u)
    return ordered[: max(0, max_urls)]


def apply_psi_to_pages(pages: list[dict], psi_results: list[dict]) -> None:
    """Overwrite a page's estimated CWV with real PSI lab values — only when
    PSI actually succeeded and returned a value (never degrade to None)."""
    by_url = {
        r.get("url"): r
        for r in psi_results
        if r.get("data_source") == "psi_api"
    }
    for page in pages:
        r = by_url.get(page.get("url"))
        if not r:
            continue
        lab = r.get("lab", {})
        if lab.get("lcp_ms") is not None:
            page["lcp_ms"] = lab["lcp_ms"]
        if lab.get("cls") is not None:
            page["cls_score"] = lab["cls"]
        if lab.get("inp_ms") is not None:
            page["inp_ms"] = lab["inp_ms"]


def psi_opportunity_issues(psi: dict) -> list[dict]:
    """Convert PSI opportunities into Performance-category audit issues."""
    issues: list[dict] = []
    for op in psi.get("opportunities", []):
        savings = op.get("savings_ms") or 0
        if savings <= 0:
            continue
        desc = op.get("description") or ""
        issues.append(
            {
                "page_url": psi.get("url"),
                "category": "performance",
                "severity": "warning" if savings > 1000 else "info",
                "rule_id": f"psi_{op.get('id', 'opportunity')}",
                "rule_name": op.get("title") or op.get("id") or "PSI opportunity",
                "description": desc,
                "fix_suggestion": desc,
                "affected_value": f"~{savings} ms potential savings",
                "expected_value": None,
            }
        )
    return issues
