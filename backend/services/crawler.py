"""Firecrawl integration [PLACEHOLDER] — Section 6.1.

When ``FIRECRAWL_API_KEY`` is unset the portal returns realistic mock page
data shaped identically to parsed Firecrawl output (PAGE_DATA_SCHEMA), so
swapping in the real key later only changes the env var, not the callers.
"""

import logging

from config import settings

logger = logging.getLogger("seo_portal.crawler")

FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"


async def crawl_site(url: str, max_pages: int = 100) -> list[dict]:
    """Crawl a website; return a list of page-data dicts (PAGE_DATA_SCHEMA).

    Real implementation: POST to Firecrawl /crawl with the site URL and
    max_pages limit, poll /crawl/{job_id} until complete, parse the
    markdown/html output into structured page data.
    """
    if not settings.firecrawl_enabled:
        # [PLACEHOLDER] no API key configured → realistic mock data
        logger.info("FIRECRAWL_API_KEY unset — returning mock crawl for %s", url)
        return _mock_crawl_result(url, max_pages)

    # TODO: implement real Firecrawl crawl when FIRECRAWL_API_KEY is set
    # import httpx
    # async with httpx.AsyncClient(timeout=60) as client:
    #     response = await client.post(
    #         f"{FIRECRAWL_BASE_URL}/crawl",
    #         headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
    #         json={"url": url, "limit": max_pages,
    #               "scrapeOptions": {"formats": ["markdown", "html"]}},
    #     )
    #     job_id = response.json()["id"]
    #     # poll f"{FIRECRAWL_BASE_URL}/crawl/{job_id}" until status == "completed"
    #     # then parse each page into PAGE_DATA_SCHEMA shape and return
    raise NotImplementedError(
        "[PLACEHOLDER] Real Firecrawl crawling is not implemented yet. "
        "Unset FIRECRAWL_API_KEY to use mock data."
    )


def _mock_crawl_result(url: str, max_pages: int) -> list[dict]:
    """Realistic mock page data for development and testing. Shape is
    identical to real Firecrawl output after parsing. The first page is the
    Section 6.1 reference homepage (kept verbatim); the project and blog
    pages add multi-page realism that exercises more rules."""
    url = url.rstrip("/")
    pages = [
        {
            "url": url,
            "title": "Mock Homepage Title — Kedar Estate",
            "meta_description": "Mock meta description for the homepage, approximately 140 characters long to simulate real content here.",
            "h1": ["Mock H1 Heading for Homepage"],
            "h2": ["About Us", "Our Projects", "Contact"],
            "h3": [],
            "word_count": 450,
            "images": [
                {"src": f"{url}/hero.jpg", "alt": "", "width": 1200, "height": 600},
                {"src": f"{url}/logo.png", "alt": "Logo", "width": 200, "height": 80},
            ],
            "internal_links": [f"{url}/projects", f"{url}/contact"],
            "external_links": ["https://rera.haryana.gov.in"],
            "broken_links": [],
            "canonical": f"{url}/",
            "noindex": False,
            "structured_data": None,  # triggers missing_structured_data
            "has_author_byline": False,
            "has_contact_info": True,
            "publish_date": None,
            "is_homepage": True,
            "page_type": "homepage",
            "lcp_ms": 2800,  # triggers lcp_needs_improvement
            "cls_score": 0.05,
            "heading_hierarchy_broken": False,
            "title_duplicate": False,
            "meta_duplicate": False,
        },
        {
            "url": f"{url}/projects/godrej-samaris-sector-53",
            "title": "Godrej Samaris Sector 53",  # short → title_too_short
            "meta_description": None,  # → missing_meta_description
            "h1": ["Godrej Samaris"],
            "h2": ["Overview", "Pricing"],
            "h3": ["Construction Quality"],
            "word_count": 220,  # → thin_content + commodity_content_risk
            "images": [
                {
                    "src": f"{url}/img/samaris-1.webp",
                    "alt": "Godrej Samaris tower exterior",
                    "width": 1024,
                    "height": 768,
                }
            ],
            "internal_links": [f"{url}/projects"],
            "external_links": [],
            "broken_links": [f"{url}/old-page"],  # → broken_internal_links
            "canonical": f"{url}/projects/godrej-samaris-sector-53",
            "noindex": False,
            "structured_data": {"@type": "Product"},
            "has_author_byline": False,
            "has_contact_info": False,
            "publish_date": None,
            "is_homepage": False,
            "page_type": "project",
            "lcp_ms": 1800,
            "cls_score": 0.04,
            "heading_hierarchy_broken": False,
            "title_duplicate": False,
            "meta_duplicate": False,
        },
        {
            "url": f"{url}/blog/golf-course-road-market-2026",
            "title": "Golf Course Road Market Analysis 2026 | Kedar Estate",
            "meta_description": "Our 2026 read on Golf Course Road Gurgaon: price trends, supply pipeline, and what our last eight closures reveal about demand.",
            "h1": ["Golf Course Road Gurgaon Market Analysis 2026"],
            "h2": ["Price Trends", "Supply Pipeline", "What Our Closures Show"],
            "h3": ["Methodology"],
            "word_count": 1450,
            "images": [
                {
                    "src": f"{url}/img/gcr-trend.webp",
                    "alt": "Golf Course Road price trend chart 2024 to 2026",
                    "width": 1200,
                    "height": 700,
                }
            ],
            "internal_links": [f"{url}/projects", f"{url}/blog"],
            "external_links": ["https://haryanarera.gov.in"],
            "broken_links": [],
            "canonical": f"{url}/blog/golf-course-road-market-2026",
            "noindex": False,
            "structured_data": {"@type": "Article"},
            "has_author_byline": True,
            "has_contact_info": True,
            "publish_date": "2026-05-10",
            "is_homepage": False,
            "page_type": "blog",
            "lcp_ms": 1600,
            "cls_score": 0.02,
            "heading_hierarchy_broken": False,
            "title_duplicate": False,
            "meta_duplicate": False,
        },
    ]
    return pages[: max(1, max_pages)]


# PageData schema (documentation only — not enforced at runtime):
PAGE_DATA_SCHEMA = {
    "url": str,
    "title": "str | None",
    "meta_description": "str | None",
    "h1": "list[str]",
    "h2": "list[str]",
    "h3": "list[str]",
    "word_count": int,
    "images": "list[{src, alt, width, height}]",
    "internal_links": "list[str]",
    "external_links": "list[str]",
    "broken_links": "list[str]",
    "canonical": "str | None",
    "noindex": bool,
    "structured_data": "dict | None",
    "has_author_byline": bool,
    "has_contact_info": bool,
    "publish_date": "str | None",
    "is_homepage": bool,
    "page_type": "str",  # "homepage"|"project"|"blog"|"contact"|"other"
    "lcp_ms": "int | None",
    "cls_score": "float | None",
    "heading_hierarchy_broken": bool,
    "title_duplicate": bool,
    "meta_duplicate": bool,
}
