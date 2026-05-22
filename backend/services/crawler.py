"""Firecrawl integration — Section 6.1.

Real crawl when ``FIRECRAWL_API_KEY`` is set: start a Firecrawl /crawl job,
poll to completion, and parse each page's HTML into the PAGE_DATA_SCHEMA the
SEO rules consume. With no key, returns realistic mock data of the same shape.

NOTE: the real path has not been exercised against the live Firecrawl API
during the build — validate the field mapping when the key is first set.
"""

import asyncio
import json
import logging
import re
from urllib.parse import urljoin, urlparse

from config import settings

logger = logging.getLogger("seo_portal.crawler")

FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"
_POLL_INTERVAL_S = 4
_MAX_POLLS = 90  # ~6 minutes


async def crawl_site(url: str, max_pages: int = 100) -> list[dict]:
    """Crawl a website; return page-data dicts (PAGE_DATA_SCHEMA).

    Real Firecrawl when FIRECRAWL_API_KEY is set, else realistic mock data.
    """
    if not settings.firecrawl_enabled:
        logger.info("FIRECRAWL_API_KEY unset — returning mock crawl for %s", url)
        return _mock_crawl_result(url, max_pages)
    logger.info("Crawling %s via Firecrawl (limit=%s)", url, max_pages)
    return await _firecrawl_crawl(url, max_pages)


async def _firecrawl_crawl(url: str, max_pages: int) -> list[dict]:
    """Real Firecrawl crawl — start a job, poll to completion, parse pages.
    Raises on failure so the audit is recorded as failed (never silently
    mocked when the operator has configured a real key)."""
    import httpx

    headers = {"Authorization": f"Bearer {settings.firecrawl_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        start = await client.post(
            f"{FIRECRAWL_BASE_URL}/crawl",
            headers=headers,
            json={
                "url": url,
                "limit": max_pages,
                "scrapeOptions": {"formats": ["html", "markdown"]},
            },
        )
        start.raise_for_status()
        job_id = start.json().get("id")
        if not job_id:
            raise RuntimeError("Firecrawl did not return a crawl job id")

        for _ in range(_MAX_POLLS):
            await asyncio.sleep(_POLL_INTERVAL_S)
            poll = await client.get(
                f"{FIRECRAWL_BASE_URL}/crawl/{job_id}", headers=headers
            )
            poll.raise_for_status()
            body = poll.json()
            status = body.get("status")
            if status == "completed":
                items = await _collect_all(client, body, headers)
                pages = [_parse_firecrawl_page(it, url) for it in items]
                _flag_duplicates(pages)
                logger.info(
                    "Firecrawl crawl of %s done — %d pages", url, len(pages)
                )
                return pages
            if status == "failed":
                raise RuntimeError(f"Firecrawl crawl failed for {url}")
    raise RuntimeError(f"Firecrawl crawl timed out for {url}")


async def _collect_all(client, body: dict, headers: dict) -> list[dict]:
    """Gather all page items, following Firecrawl's `next` pagination."""
    items = list(body.get("data") or [])
    nxt = body.get("next")
    while nxt:
        resp = await client.get(nxt, headers=headers)
        resp.raise_for_status()
        page = resp.json()
        items.extend(page.get("data") or [])
        nxt = page.get("next")
    return items


def _meta(soup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"name": name})
    return tag.get("content") if tag and tag.get("content") else None


def _meta_prop(soup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop})
    return tag.get("content") if tag and tag.get("content") else None


def _heading_broken(soup) -> bool:
    """True if heading levels skip a level (e.g. H1 → H3 with no H2)."""
    prev = 0
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        lvl = int(h.name[1])
        if prev and lvl > prev + 1:
            return True
        prev = lvl
    return False


def _parse_firecrawl_page(item: dict, site_url: str) -> dict:
    """Parse one Firecrawl page result into the PAGE_DATA_SCHEMA shape."""
    from bs4 import BeautifulSoup

    meta = item.get("metadata") or {}
    html = item.get("html") or ""
    markdown = item.get("markdown") or ""
    page_url = (
        meta.get("sourceURL")
        or meta.get("url")
        or item.get("url")
        or site_url
    )
    soup = BeautifulSoup(html, "html.parser")

    title = meta.get("title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    description = meta.get("description") or _meta(soup, "description")

    def headings(level: str) -> list[str]:
        return [h.get_text(strip=True) for h in soup.find_all(level)]

    images = [
        {
            "src": img.get("src", ""),
            "alt": img.get("alt"),
            "width": img.get("width"),
            "height": img.get("height"),
        }
        for img in soup.find_all("img")
    ]

    host = urlparse(page_url).netloc
    internal_links: list[str] = []
    external_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        netloc = urlparse(href).netloc
        (internal_links if not netloc or netloc == host else external_links).append(href)

    canon = soup.find("link", attrs={"rel": "canonical"})
    canonical = (canon.get("href") if canon else None) or meta.get("canonical")
    robots = (_meta(soup, "robots") or "").lower()

    structured_data = None
    jsonld = soup.find("script", attrs={"type": "application/ld+json"})
    if jsonld and jsonld.string:
        try:
            structured_data = json.loads(jsonld.string)
        except (ValueError, TypeError):
            structured_data = {"_unparsed": True}

    text = soup.get_text(" ", strip=True) or markdown
    time_tag = soup.find("time")
    publish_date = _meta_prop(soup, "article:published_time") or (
        time_tag.get("datetime") if time_tag else None
    )

    path = urlparse(page_url).path.strip("/")
    is_homepage = path == ""
    if is_homepage:
        page_type = "homepage"
    elif path.startswith("blog"):
        page_type = "blog"
    elif path.startswith(("project", "propert")):
        page_type = "project"
    else:
        page_type = "other"

    return {
        "url": page_url,
        "title": title,
        "meta_description": description,
        "h1": headings("h1"),
        "h2": headings("h2"),
        "h3": headings("h3"),
        "word_count": len(text.split()),
        "images": images,
        "internal_links": internal_links,
        "external_links": external_links,
        "broken_links": [],  # Firecrawl does not report these
        "canonical": canonical,
        "noindex": "noindex" in robots,
        "structured_data": structured_data,
        "has_author_byline": bool(
            soup.find(attrs={"rel": "author"})
            or soup.find(class_=re.compile(r"author|byline", re.I))
            or _meta_prop(soup, "article:author")
        ),
        "has_contact_info": bool(
            soup.find("a", href=re.compile(r"^(tel:|mailto:)", re.I))
        ),
        "publish_date": publish_date,
        "is_homepage": is_homepage,
        "page_type": page_type,
        "lcp_ms": None,  # filled by PageSpeed Insights (Addendum v1.2)
        "cls_score": None,
        "heading_hierarchy_broken": _heading_broken(soup),
        "title_duplicate": False,  # set by _flag_duplicates
        "meta_duplicate": False,
    }


def _flag_duplicates(pages: list[dict]) -> None:
    """Mark title_duplicate / meta_duplicate across the crawled page set."""

    def tally(key: str) -> dict:
        seen: dict[str, int] = {}
        for p in pages:
            v = (p.get(key) or "").strip()
            if v:
                seen[v] = seen.get(v, 0) + 1
        return seen

    titles = tally("title")
    metas = tally("meta_description")
    for p in pages:
        t = (p.get("title") or "").strip()
        m = (p.get("meta_description") or "").strip()
        p["title_duplicate"] = bool(t and titles.get(t, 0) > 1)
        p["meta_duplicate"] = bool(m and metas.get(m, 0) > 1)


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
