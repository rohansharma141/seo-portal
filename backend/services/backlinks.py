"""Backlink data integration [PLACEHOLDER] — Addendum v1.1 §2.

DataForSEO is the target provider. When DATAFORSEO_LOGIN/PASSWORD are unset
(`settings.dataforseo_enabled` is False), returns a clearly-labelled mock with
the same shape as the parsed real response. Gated through `settings` for
consistency with the other integrations (crawler/gsc/analyser).
"""

import logging
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger("seo_portal.backlinks")

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_backlink_data(domain: str) -> dict:
    """Backlink summary for a domain.

    Real implementation: POST DataForSEO /backlinks/summary/live
    (~$0.0015 / request). Returns BacklinkData (same shape either source).
    """
    if not settings.dataforseo_enabled:
        logger.info(
            "DATAFORSEO creds unset — returning mock backlink data for %s",
            domain,
        )
        return _mock_backlink_data(domain)

    # TODO: implement real DataForSEO call when credentials are set
    # import httpx
    # async with httpx.AsyncClient(timeout=30) as client:
    #     resp = await client.post(
    #         f"{DATAFORSEO_BASE}/backlinks/summary/live",
    #         auth=(settings.dataforseo_login, settings.dataforseo_password),
    #         json=[{"target": domain, "include_subdomains": True}],
    #     )
    #     data = resp.json()["tasks"][0]["result"][0]
    #     return _parse_dataforseo_response(data, domain)
    raise NotImplementedError(
        "[PLACEHOLDER] Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD to "
        "enable real backlink data."
    )


def _mock_backlink_data(domain: str) -> dict:
    """Mock — same shape as the real response after parsing. Zeroed, as for a
    new/untracked site."""
    return {
        "domain": domain,
        "data_source": "mock",  # "dataforseo" when real
        "fetched_at": _now_iso(),
        "domain_rank": 0,
        "referring_domains": 0,
        "referring_pages": 0,
        "backlinks_total": 0,
        "backlinks_dofollow": 0,
        "backlinks_nofollow": 0,
        "broken_backlinks": 0,
        "top_referring_domains": [],
        "anchor_distribution": [],
        "new_lost": {
            "new_referring_domains_30d": 0,
            "lost_referring_domains_30d": 0,
        },
        "placeholder_note": (
            "Backlink data is not yet configured. Set DATAFORSEO_LOGIN and "
            "DATAFORSEO_PASSWORD environment variables to enable. Cost: "
            "~₹0.12 per domain lookup. Free alternative: use Ahrefs Webmaster "
            "Tools at ahrefs.com/webmaster-tools for your own verified sites."
        ),
    }


def _parse_dataforseo_response(data: dict, domain: str) -> dict:
    """Parse a real DataForSEO response into BacklinkData shape."""
    return {
        "domain": domain,
        "data_source": "dataforseo",
        "fetched_at": _now_iso(),
        "domain_rank": data.get("rank", 0),
        "referring_domains": data.get("referring_domains", 0),
        "referring_pages": data.get("referring_pages", 0),
        "backlinks_total": data.get("backlinks", 0),
        "backlinks_dofollow": data.get("dofollow", 0),
        "backlinks_nofollow": data.get("nofollow", 0),
        "broken_backlinks": data.get("broken_backlinks", 0),
        "top_referring_domains": data.get("referring_domains_top", []),
        "anchor_distribution": data.get("anchors", []),
        "new_lost": {
            "new_referring_domains_30d": data.get("new_referring_domains", 0),
            "lost_referring_domains_30d": data.get(
                "lost_referring_domains", 0
            ),
        },
        "placeholder_note": None,
    }
