# SEO Analysis Portal — Claude Code Build Document
# Version 1.0 | May 2026
# Feed this document to Claude Code at the start of every build session.

---

## 0. DOCUMENT PURPOSE

This document instructs Claude Code to build a standalone SEO Analysis Portal. It covers:
- Full system architecture
- Tech stack with exact versions
- Database schema
- API contract (all endpoints)
- Frontend page specifications
- Integration placeholders (Firecrawl, GSC MCP, Claude API)
- File/folder structure
- Environment variable manifest
- Build sequence (what to build in what order)

Build everything described. Where credentials are marked `[PLACEHOLDER]`, insert the placeholder string and add a `TODO` comment. Do not skip any section.

---

## 1. PROJECT OVERVIEW

**Product name:** Prithvi SEO Portal  
**Purpose:** Standalone web portal + REST API for automated SEO auditing of websites. Built for Kedar Estate and PropOS internal use, with API exposure for PropOS to call programmatically when auditing broker-generated landing pages.

**Core capabilities:**
1. Register any website (domain) for monitoring
2. Trigger on-demand SEO audits (crawl → analyse → score → report)
3. Scheduled automatic audits (weekly by default)
4. View audit history and trend over time
5. Detailed issue breakdown with fix suggestions
6. REST API exposing all audit features for PropOS integration
7. Webhook callbacks when audits complete (PropOS can subscribe)

**User types:**
- Admin (Rohan): full access, can add/remove sites, view all audits
- API consumer (PropOS backend): token-authenticated, can trigger audits and read results via API

---

## 2. TECH STACK

| Layer | Choice | Version | Notes |
|---|---|---|---|
| Backend | FastAPI | 0.115.x | Async, Python 3.12 |
| Database | PostgreSQL via Supabase | latest | Use Supabase client |
| ORM | SQLAlchemy (async) | 2.x | With asyncpg driver |
| Task queue | APScheduler | 3.x | For scheduled audits |
| Web crawling | Firecrawl API | — | [PLACEHOLDER — see Section 6] |
| GSC data | GSC API via google-auth | — | [PLACEHOLDER — see Section 6] |
| AI analysis | Anthropic Claude API (Haiku 4.5) | — | [PLACEHOLDER — see Section 6] |
| Frontend | Next.js | 14.x | TypeScript, App Router |
| Styling | Tailwind CSS | 3.x | Custom design tokens |
| Auth | Supabase Auth | — | Email/password for portal |
| API auth | JWT bearer tokens | — | For programmatic API access |
| Deployment | Hetzner (backend) + Vercel (frontend) | — | |
| DNS/CDN | Cloudflare | — | |
| Email | Resend | — | Audit complete notifications |
| Monitoring | BetterStack | — | Uptime + logs |

---

## 3. FOLDER STRUCTURE

Build exactly this structure:

```
seo-portal/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # All env vars, settings
│   ├── database.py                # Supabase + SQLAlchemy setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── site.py                # Site model
│   │   ├── audit.py               # Audit + AuditIssue models
│   │   ├── api_token.py           # API token model
│   │   └── webhook.py             # Webhook subscription model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── site.py                # Pydantic schemas for Site
│   │   ├── audit.py               # Pydantic schemas for Audit
│   │   └── api_token.py           # Pydantic schemas for API tokens
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sites.py               # /api/v1/sites endpoints
│   │   ├── audits.py              # /api/v1/audits endpoints
│   │   ├── reports.py             # /api/v1/reports endpoints
│   │   ├── tokens.py              # /api/v1/tokens endpoints
│   │   └── webhooks.py            # /api/v1/webhooks endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crawler.py             # Firecrawl integration [PLACEHOLDER]
│   │   ├── gsc.py                 # Google Search Console integration [PLACEHOLDER]
│   │   ├── analyser.py            # Claude API analysis engine [PLACEHOLDER]
│   │   ├── scorer.py              # SEO scoring logic (pure Python, no external dep)
│   │   ├── scheduler.py           # APScheduler setup + jobs
│   │   ├── notifier.py            # Resend email notifications [PLACEHOLDER]
│   │   └── webhook_dispatcher.py  # HTTP webhook firing
│   ├── middleware/
│   │   ├── auth.py                # JWT verification middleware
│   │   └── rate_limit.py          # Upstash Redis rate limiting [PLACEHOLDER]
│   ├── utils/
│   │   ├── seo_rules.py           # All SEO check rules (pure logic)
│   │   └── helpers.py             # URL normalisation, slug gen, etc.
│   ├── tests/
│   │   ├── test_scorer.py
│   │   ├── test_seo_rules.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx                  # Dashboard / home
    │   │   ├── sites/
    │   │   │   ├── page.tsx              # All sites list
    │   │   │   └── [siteId]/
    │   │   │       ├── page.tsx          # Site detail + audit history
    │   │   │       └── audits/
    │   │   │           └── [auditId]/
    │   │   │               └── page.tsx  # Single audit report
    │   │   ├── api-tokens/
    │   │   │   └── page.tsx              # API token management
    │   │   └── settings/
    │   │       └── page.tsx              # Global settings
    │   ├── components/
    │   │   ├── ui/                       # Reusable UI primitives
    │   │   ├── sites/                    # Site-specific components
    │   │   ├── audits/                   # Audit report components
    │   │   └── layout/                  # Nav, sidebar, header
    │   ├── lib/
    │   │   ├── api.ts                    # API client (typed)
    │   │   └── utils.ts
    │   └── types/
    │       └── index.ts                  # All shared TypeScript types
    ├── public/
    ├── tailwind.config.ts
    ├── next.config.ts
    ├── tsconfig.json
    └── .env.example
```

---

## 4. DATABASE SCHEMA

Use Supabase (PostgreSQL). Create all tables via SQLAlchemy models AND provide matching SQL migration files.

### 4.1 sites table
```sql
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,               -- Human label e.g. "Kedar Estate"
    domain VARCHAR(255) NOT NULL UNIQUE,      -- e.g. "kedar.estate"
    url VARCHAR(500) NOT NULL,                -- Full URL e.g. "https://kedar.estate"
    site_type VARCHAR(50) NOT NULL            -- "brokerage" | "saas" | "broker_landing" | "other"
        DEFAULT 'other',
    schedule VARCHAR(50) NOT NULL             -- "weekly" | "monthly" | "manual"
        DEFAULT 'weekly',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_pages INTEGER NOT NULL DEFAULT 100,   -- Crawl depth limit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_audit_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'              -- Flexible extra fields
);
```

### 4.2 audits table
```sql
CREATE TABLE audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
        -- "pending" | "crawling" | "analysing" | "scoring" | "complete" | "failed"
    triggered_by VARCHAR(50) NOT NULL DEFAULT 'manual',
        -- "manual" | "scheduled" | "api" | "deploy_hook"
    score_overall INTEGER,                   -- 0-100
    score_technical INTEGER,                 -- 0-100
    score_content INTEGER,                   -- 0-100
    score_eeeat INTEGER,                     -- 0-100 (E-E-A-T)
    score_performance INTEGER,               -- 0-100
    score_structure INTEGER,                 -- 0-100
    pages_crawled INTEGER DEFAULT 0,
    issues_critical INTEGER DEFAULT 0,
    issues_warning INTEGER DEFAULT 0,
    issues_info INTEGER DEFAULT 0,
    crawl_data JSONB DEFAULT '[]',           -- Raw Firecrawl output per page
    gsc_data JSONB DEFAULT '{}',             -- GSC snapshot at audit time [PLACEHOLDER]
    analysis_summary TEXT,                   -- Claude's narrative summary
    quick_wins JSONB DEFAULT '[]',           -- Top 3 high-impact easy fixes
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message TEXT                       -- Populated if status = "failed"
);
```

### 4.3 audit_issues table
```sql
CREATE TABLE audit_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
    page_url VARCHAR(1000),                  -- NULL = site-wide issue
    category VARCHAR(100) NOT NULL,
        -- "technical" | "content" | "eeeat" | "performance" | "structure" | "schema"
    severity VARCHAR(20) NOT NULL,
        -- "critical" | "warning" | "info"
    rule_id VARCHAR(100) NOT NULL,           -- e.g. "missing_title_tag"
    rule_name VARCHAR(255) NOT NULL,         -- e.g. "Missing Title Tag"
    description TEXT NOT NULL,              -- What's wrong
    fix_suggestion TEXT NOT NULL,           -- Exactly how to fix it
    affected_value TEXT,                    -- Current value (e.g. the bad title)
    expected_value TEXT,                    -- What it should be
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_issues_audit_id ON audit_issues(audit_id);
CREATE INDEX idx_audit_issues_severity ON audit_issues(severity);
CREATE INDEX idx_audit_issues_category ON audit_issues(category);
```

### 4.4 api_tokens table
```sql
CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,              -- e.g. "PropOS Production"
    token_hash VARCHAR(255) NOT NULL UNIQUE, -- bcrypt hash of the token
    token_prefix VARCHAR(10) NOT NULL,       -- First 8 chars for display e.g. "pse_xxxx"
    scopes JSONB NOT NULL DEFAULT '["audit:read","audit:write","site:read"]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,                  -- NULL = never expires
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.5 webhooks table
```sql
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    events JSONB NOT NULL DEFAULT '["audit.complete","audit.failed"]',
    secret VARCHAR(255),                     -- HMAC secret for signature verification
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 5. SEO SCORING ENGINE (Pure Python — No External Dependencies)

This is the core of the portal. Build it as pure Python logic in `services/scorer.py` and `utils/seo_rules.py`. It must work even with all external integrations mocked.

### 5.1 Score calculation

Overall score = weighted average:
- Technical: 30% weight
- Content: 25% weight  
- E-E-A-T: 20% weight
- Performance: 15% weight
- Structure: 10% weight

Each category scored 0–100. Each issue deducts points:
- Critical: -15 points
- Warning: -5 points
- Info: -1 point

Minimum score: 0. Maximum: 100.

### 5.2 Complete rule set — implement ALL of these

Build each as a separate check function in `utils/seo_rules.py`. Each function takes page data (dict) and returns a list of issues or empty list.

**TECHNICAL RULES:**
```python
RULE_TECHNICAL = [
    {
        "id": "missing_title_tag",
        "name": "Missing Title Tag",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: not page.get("title"),
        "description": "Page has no <title> tag. Title tags are critical for indexing and click-through rates.",
        "fix": "Add a descriptive <title> tag between 50–60 characters. Include the primary keyword and brand name."
    },
    {
        "id": "title_too_short",
        "name": "Title Tag Too Short",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: page.get("title") and len(page["title"]) < 30,
        "description": "Title tag is under 30 characters. Too short to be descriptive.",
        "fix": "Expand the title to 50–60 characters with primary keyword + location + brand."
    },
    {
        "id": "title_too_long",
        "name": "Title Tag Too Long",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: page.get("title") and len(page["title"]) > 60,
        "description": f"Title tag is over 60 characters. Google truncates at ~600px.",
        "fix": "Shorten the title to 50–60 characters without losing the primary keyword."
    },
    {
        "id": "missing_meta_description",
        "name": "Missing Meta Description",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("meta_description"),
        "description": "No meta description. While not a direct ranking factor, it affects click-through rate from search results.",
        "fix": "Add a unique meta description of 120–160 characters. Summarise the page and include a call to action."
    },
    {
        "id": "meta_description_too_long",
        "name": "Meta Description Too Long",
        "severity": "info",
        "category": "technical",
        "check": lambda page: page.get("meta_description") and len(page["meta_description"]) > 160,
        "description": "Meta description exceeds 160 characters and will be truncated in search results.",
        "fix": "Shorten to 120–160 characters, keeping the most important information at the start."
    },
    {
        "id": "missing_h1",
        "name": "Missing H1 Tag",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: not page.get("h1") or len(page.get("h1", [])) == 0,
        "description": "Page has no H1 heading. H1 is a key on-page SEO signal.",
        "fix": "Add one H1 tag containing the primary keyword for this page."
    },
    {
        "id": "multiple_h1",
        "name": "Multiple H1 Tags",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: len(page.get("h1", [])) > 1,
        "description": f"Page has multiple H1 tags. Only one H1 per page is best practice.",
        "fix": "Keep only one H1 tag. Convert additional H1s to H2 or H3 as appropriate."
    },
    {
        "id": "images_missing_alt",
        "name": "Images Missing Alt Text",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: any(not img.get("alt") for img in page.get("images", [])),
        "description": "One or more images have no alt attribute. Alt text helps Google understand images and aids accessibility.",
        "fix": "Add descriptive alt text to every image. Describe what the image shows, not the filename."
    },
    {
        "id": "no_canonical_tag",
        "name": "Missing Canonical Tag",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("canonical"),
        "description": "No canonical tag found. Without it, Google may index duplicate versions of this page.",
        "fix": "Add <link rel='canonical' href='[full URL]'> in the <head> of every page."
    },
    {
        "id": "http_not_https",
        "name": "Not Served Over HTTPS",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: page.get("url", "").startswith("http://"),
        "description": "Page is served over HTTP. HTTPS is a ranking signal and Chrome marks HTTP as 'Not Secure'.",
        "fix": "Configure SSL certificate and redirect all HTTP to HTTPS at server level."
    },
    {
        "id": "noindex_detected",
        "name": "Noindex Tag Detected",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: page.get("noindex") is True,
        "description": "Page has a noindex meta tag. Google will NOT index this page.",
        "fix": "Remove the <meta name='robots' content='noindex'> tag if this page should appear in search."
    },
    {
        "id": "missing_structured_data",
        "name": "No Structured Data (Schema.org)",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("structured_data"),
        "description": "No JSON-LD or Schema.org markup found. Structured data enables rich results in Google.",
        "fix": "Add appropriate JSON-LD schema. For real estate pages: RealEstateAgent + Product. For blog posts: Article."
    },
    {
        "id": "broken_internal_links",
        "name": "Broken Internal Links",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: len(page.get("broken_links", [])) > 0,
        "description": "Page has internal links pointing to 404 or error pages.",
        "fix": "Fix or remove broken internal links. Update URLs or redirect old pages."
    },
]

RULE_CONTENT = [
    {
        "id": "thin_content",
        "name": "Thin Content",
        "severity": "warning",
        "category": "content",
        "check": lambda page: page.get("word_count", 0) < 300,
        "description": "Page has fewer than 300 words. Thin content rarely ranks well.",
        "fix": "Expand content to at least 600 words with genuine, first-hand information relevant to the page topic."
    },
    {
        "id": "commodity_content_risk",
        "name": "Potential Commodity Content",
        "severity": "info",
        "category": "content",
        "check": lambda page: page.get("word_count", 0) < 500 and not page.get("has_author_byline"),
        "description": "Short page with no author attribution. May not pass Google's E-E-A-T evaluation.",
        "fix": "Add a named author byline and expand content with first-hand expertise, specific data, and unique insights."
    },
    {
        "id": "duplicate_title_across_site",
        "name": "Duplicate Title Tag",
        "severity": "critical",
        "category": "content",
        "check": lambda page: page.get("title_duplicate") is True,
        "description": "This title tag appears on more than one page on the site.",
        "fix": "Every page must have a unique title tag. Rewrite to reflect the specific content of this page."
    },
    {
        "id": "duplicate_meta_description",
        "name": "Duplicate Meta Description",
        "severity": "warning",
        "category": "content",
        "check": lambda page: page.get("meta_duplicate") is True,
        "description": "This meta description is used on multiple pages.",
        "fix": "Write a unique meta description for every page. Describe what specifically this page offers."
    },
    {
        "id": "no_images",
        "name": "No Images Found",
        "severity": "info",
        "category": "content",
        "check": lambda page: len(page.get("images", [])) == 0 and page.get("page_type") in ["project", "property", "blog"],
        "description": "No images found on a page that would benefit from visual content.",
        "fix": "Add high-quality, relevant images. For property pages: site visit photos. For blog posts: featured images."
    },
]

RULE_EEEAT = [
    {
        "id": "no_author_byline",
        "name": "No Author Byline",
        "severity": "warning",
        "category": "eeeat",
        "check": lambda page: not page.get("has_author_byline") and page.get("page_type") in ["blog", "review", "article"],
        "description": "Content page has no visible author attribution. E-E-A-T requires showing WHO created the content.",
        "fix": "Add a named author byline with a link to the author's bio page. Include their relevant credentials."
    },
    {
        "id": "no_publish_date",
        "name": "No Publication Date",
        "severity": "info",
        "category": "eeeat",
        "check": lambda page: not page.get("publish_date") and page.get("page_type") in ["blog", "review", "article"],
        "description": "No publication date visible on content page. Freshness signals matter for trust.",
        "fix": "Show the publication date (and last updated date) prominently on all content pages."
    },
    {
        "id": "no_contact_info",
        "name": "No Contact Information",
        "severity": "warning",
        "category": "eeeat",
        "check": lambda page: not page.get("has_contact_info") and page.get("is_homepage"),
        "description": "Homepage has no visible contact information. Trust signals require clear contact details.",
        "fix": "Add phone number, email, and physical address to homepage and contact page."
    },
]

RULE_PERFORMANCE = [
    {
        "id": "lcp_poor",
        "name": "Poor LCP (Largest Contentful Paint)",
        "severity": "critical",
        "category": "performance",
        "check": lambda page: page.get("lcp_ms", 0) > 4000,
        "description": f"LCP is over 4 seconds. Google considers anything over 2.5s 'Poor'. This suppresses rankings.",
        "fix": "Optimise: compress images to WebP, lazy load below-fold images, enable server-side rendering, reduce JS bundle size."
    },
    {
        "id": "lcp_needs_improvement",
        "name": "LCP Needs Improvement",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: 2500 < page.get("lcp_ms", 0) <= 4000,
        "description": "LCP is between 2.5–4 seconds. Should be under 2.5s.",
        "fix": "Compress images, enable caching, reduce server response time."
    },
    {
        "id": "cls_poor",
        "name": "High Cumulative Layout Shift",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: page.get("cls_score", 0) > 0.1,
        "description": f"CLS score exceeds 0.1. Page content is shifting as it loads, harming UX and rankings.",
        "fix": "Set explicit width and height on all images and embeds. Avoid inserting content above existing content."
    },
    {
        "id": "images_not_webp",
        "name": "Images Not Using WebP Format",
        "severity": "info",
        "category": "performance",
        "check": lambda page: any(
            img.get("src", "").lower().endswith((".jpg", ".jpeg", ".png"))
            for img in page.get("images", [])
        ),
        "description": "Images are served in JPEG/PNG format. WebP provides 25–35% smaller file sizes.",
        "fix": "Convert images to WebP format. In Next.js, use the built-in <Image> component which auto-converts."
    },
    {
        "id": "images_no_dimensions",
        "name": "Images Missing Width/Height Attributes",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: any(
            not img.get("width") or not img.get("height")
            for img in page.get("images", [])
        ),
        "description": "Images without explicit dimensions cause layout shift (CLS) as they load.",
        "fix": "Add explicit width and height attributes to all <img> tags. Use aspect-ratio CSS as alternative."
    },
]

RULE_STRUCTURE = [
    {
        "id": "non_descriptive_url",
        "name": "Non-Descriptive URL",
        "severity": "warning",
        "category": "structure",
        "check": lambda page: bool(re.search(r'[?&=]|\d{6,}', page.get("url", ""))),
        "description": "URL contains query parameters or numeric IDs instead of descriptive words.",
        "fix": "Use descriptive slugs like /projects/godrej-samaris-sector-53 instead of /p?id=12345."
    },
    {
        "id": "url_uppercase",
        "name": "URL Contains Uppercase Characters",
        "severity": "info",
        "category": "structure",
        "check": lambda page: any(c.isupper() for c in page.get("url", "").split("//")[-1]),
        "description": "URLs with uppercase characters can cause duplicate content issues.",
        "fix": "Use all-lowercase URLs. Configure server to redirect uppercase to lowercase versions."
    },
    {
        "id": "no_internal_links",
        "name": "Page Has No Internal Links",
        "severity": "warning",
        "category": "structure",
        "check": lambda page: len(page.get("internal_links", [])) == 0,
        "description": "Page is an orphan with no internal links pointing to other pages. Reduces crawl depth and PageRank flow.",
        "fix": "Add at least 2–3 internal links to related pages using descriptive anchor text."
    },
    {
        "id": "heading_hierarchy_broken",
        "name": "Broken Heading Hierarchy",
        "severity": "info",
        "category": "structure",
        "check": lambda page: page.get("heading_hierarchy_broken") is True,
        "description": "Heading levels skip (e.g. H1 → H3 with no H2). Hurts accessibility and structure signals.",
        "fix": "Use headings in order: H1 → H2 → H3. Do not skip levels."
    },
]
```

### 5.3 Scoring function
```python
# In services/scorer.py

def calculate_score(issues: list[dict]) -> dict:
    """
    Given a list of issue dicts (each with category, severity),
    calculate scores per category and overall.
    """
    categories = ["technical", "content", "eeeat", "performance", "structure"]
    weights = {
        "technical": 0.30,
        "content": 0.25,
        "eeeat": 0.20,
        "performance": 0.15,
        "structure": 0.10,
    }
    deductions = {"critical": 15, "warning": 5, "info": 1}
    
    scores = {}
    for cat in categories:
        cat_issues = [i for i in issues if i["category"] == cat]
        deduct = sum(deductions.get(i["severity"], 0) for i in cat_issues)
        scores[cat] = max(0, 100 - deduct)
    
    overall = sum(scores[cat] * weights[cat] for cat in categories)
    return {
        "overall": round(overall),
        "technical": scores["technical"],
        "content": scores["content"],
        "eeeat": scores["eeeat"],
        "performance": scores["performance"],
        "structure": scores["structure"],
    }
```

---

## 6. EXTERNAL SERVICE INTEGRATIONS (PLACEHOLDERS)

All three integrations below are PLACEHOLDERS. Build the interface and mock responses. The mock must return realistic data shaped identically to what the real integration will return, so swapping in the real key later requires only updating the env var, not the code.

### 6.1 Firecrawl — `services/crawler.py`

```python
# services/crawler.py

import os
from typing import Optional

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")  # [PLACEHOLDER]
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"

async def crawl_site(url: str, max_pages: int = 100) -> list[dict]:
    """
    Crawls a website and returns a list of page data dicts.
    
    Real implementation: POST to Firecrawl /crawl endpoint with
    the site URL and max_pages limit. Poll /crawl/{job_id} until
    complete. Parse markdown output into structured page data.
    
    Returns list of dicts matching PageData schema (see below).
    """
    if not FIRECRAWL_API_KEY:
        # [PLACEHOLDER] Return mock data when no API key configured
        return _mock_crawl_result(url, max_pages)
    
    # TODO: implement real Firecrawl crawl when FIRECRAWL_API_KEY is set
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         f"{FIRECRAWL_BASE_URL}/crawl",
    #         headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
    #         json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown", "html"]}}
    #     )
    #     job_id = response.json()["id"]
    #     # poll until complete...
    raise NotImplementedError("[PLACEHOLDER] Set FIRECRAWL_API_KEY env var to enable real crawling")


def _mock_crawl_result(url: str, max_pages: int) -> list[dict]:
    """
    Returns realistic mock page data for development and testing.
    Shape is identical to real Firecrawl output after parsing.
    """
    return [
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
            "structured_data": None,  # Will trigger missing_structured_data rule
            "has_author_byline": False,
            "has_contact_info": True,
            "publish_date": None,
            "is_homepage": True,
            "page_type": "homepage",
            "lcp_ms": 2800,    # Will trigger lcp_needs_improvement rule
            "cls_score": 0.05,
            "heading_hierarchy_broken": False,
            "title_duplicate": False,
            "meta_duplicate": False,
        }
    ]


# PageData schema (for documentation — not enforced at runtime):
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
```

### 6.2 Google Search Console — `services/gsc.py`

```python
# services/gsc.py

import os

GSC_CREDENTIALS_PATH = os.getenv("GSC_CREDENTIALS_PATH", "")  # [PLACEHOLDER]
GSC_SITE_URL = os.getenv("GSC_SITE_URL", "")                  # [PLACEHOLDER]

async def get_gsc_performance(site_url: str, days: int = 90) -> dict:
    """
    Fetches search performance data from Google Search Console.
    
    Real implementation: use google-auth + googleapiclient.discovery
    to call searchanalytics.query() with dimensions=['page','query'].
    
    Returns GSCData dict (see schema below).
    """
    if not GSC_CREDENTIALS_PATH:
        # [PLACEHOLDER] Return mock GSC data
        return _mock_gsc_data(site_url)
    
    # TODO: implement real GSC fetch when GSC_CREDENTIALS_PATH is set
    # from google.oauth2 import service_account
    # from googleapiclient.discovery import build
    # ...
    raise NotImplementedError("[PLACEHOLDER] Set GSC_CREDENTIALS_PATH env var to enable GSC data")


def _mock_gsc_data(site_url: str) -> dict:
    """Mock GSC data — same shape as real GSC API response after parsing."""
    return {
        "total_clicks_90d": 0,        # New site — no traffic yet
        "total_impressions_90d": 0,
        "avg_ctr": 0.0,
        "avg_position": 0.0,
        "top_queries": [],             # List of {query, clicks, impressions, ctr, position}
        "top_pages": [],               # List of {page, clicks, impressions, ctr, position}
        "low_ctr_pages": [],           # Pages with >200 impressions and CTR < 2%
        "quick_wins": [],              # Queries at position 11-20 with >100 impressions
        "indexing_errors": 0,
        "indexed_pages": 0,
        "data_source": "mock",         # Will be "gsc_api" when real
    }
```

### 6.3 Claude API Analysis — `services/analyser.py`

```python
# services/analyser.py

import os
import json

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # [PLACEHOLDER]
CLAUDE_MODEL = "claude-haiku-4-5-20251001"               # Use Haiku for cost efficiency

async def analyse_audit(
    site_url: str,
    pages_data: list[dict],
    issues: list[dict],
    scores: dict,
    gsc_data: dict,
    seo_strategy_context: str = ""
) -> dict:
    """
    Uses Claude API to generate narrative analysis of the audit.
    
    Returns AnalysisResult dict:
    {
        "summary": str,           # 2–3 paragraph executive summary
        "quick_wins": list[dict], # Top 3 highest-impact, lowest-effort fixes
        "content_assessment": str,# Assessment of content quality vs E-E-A-T
        "priority_actions": list, # Ordered list of recommended actions
        "positive_signals": list, # What's already working well
    }
    """
    if not ANTHROPIC_API_KEY:
        return _mock_analysis(site_url, issues, scores)
    
    # TODO: implement real Claude API call when ANTHROPIC_API_KEY is set
    # Use the SEO_STRATEGY_CLAUDE_CODE.md content as system prompt context
    # Build a structured prompt from issues and scores
    # Parse JSON response from Claude
    raise NotImplementedError("[PLACEHOLDER] Set ANTHROPIC_API_KEY env var to enable AI analysis")


def _mock_analysis(site_url: str, issues: list[dict], scores: dict) -> dict:
    """Mock AI analysis — same shape as real Claude response."""
    critical_count = sum(1 for i in issues if i["severity"] == "critical")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    
    return {
        "summary": (
            f"Audit complete for {site_url}. Overall SEO health score is {scores.get('overall', 0)}/100. "
            f"Found {critical_count} critical issues requiring immediate attention and {warning_count} warnings. "
            f"[MOCK: Connect ANTHROPIC_API_KEY for AI-generated insights.]"
        ),
        "quick_wins": [
            {
                "title": "Add missing title tags",
                "effort": "low",
                "impact": "high",
                "description": "Several pages are missing title tags. This is a 5-minute fix per page."
            },
            {
                "title": "Fix images missing alt text",
                "effort": "low",
                "impact": "medium",
                "description": "Add descriptive alt text to all images. Can be scripted."
            },
            {
                "title": "Add JSON-LD structured data",
                "effort": "medium",
                "impact": "high",
                "description": "Add schema markup to enable rich results in Google."
            }
        ],
        "content_assessment": "[MOCK] Connect ANTHROPIC_API_KEY for content quality assessment.",
        "priority_actions": [
            "Fix all critical technical issues first",
            "Add structured data to all pages",
            "Expand thin content pages to 600+ words",
        ],
        "positive_signals": ["HTTPS configured", "Mobile-responsive layout detected"],
        "data_source": "mock",
    }
```

---

## 7. API CONTRACT (All Endpoints)

Base path: `/api/v1/`  
Auth: Bearer token in `Authorization` header for all non-health endpoints.  
Format: JSON request/response throughout.  
Versioning: All routes prefixed with `/api/v1/`.

### 7.1 Health

```
GET /health
Response: { "status": "ok", "version": "1.0.0", "timestamp": "ISO8601" }
Auth: None required
```

### 7.2 Sites

```
GET    /api/v1/sites                    List all registered sites
POST   /api/v1/sites                    Register a new site
GET    /api/v1/sites/{site_id}          Get site details + last audit summary
PATCH  /api/v1/sites/{site_id}          Update site settings
DELETE /api/v1/sites/{site_id}          Remove site (soft delete: sets is_active=false)
```

**POST /api/v1/sites request body:**
```json
{
  "name": "Kedar Estate",
  "domain": "kedar.estate",
  "url": "https://kedar.estate",
  "site_type": "brokerage",
  "schedule": "weekly",
  "max_pages": 100
}
```

**GET /api/v1/sites response:**
```json
{
  "sites": [
    {
      "id": "uuid",
      "name": "Kedar Estate",
      "domain": "kedar.estate",
      "url": "https://kedar.estate",
      "site_type": "brokerage",
      "schedule": "weekly",
      "is_active": true,
      "last_audit_at": "2026-05-01T10:00:00Z",
      "last_score": 74,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 7.3 Audits

```
GET  /api/v1/audits                       List all audits (paginated, filterable by site_id)
POST /api/v1/audits                       Trigger a new audit
GET  /api/v1/audits/{audit_id}            Get full audit result with all issues
GET  /api/v1/audits/{audit_id}/issues     Get issues for an audit (filterable by severity/category)
GET  /api/v1/audits/{audit_id}/status     Polling endpoint — get current audit status
```

**POST /api/v1/audits request body:**
```json
{
  "site_id": "uuid",
  "triggered_by": "api"
}
```

**POST /api/v1/audits response (audit started):**
```json
{
  "audit_id": "uuid",
  "status": "pending",
  "site_id": "uuid",
  "message": "Audit queued. Poll /api/v1/audits/{audit_id}/status for progress.",
  "estimated_seconds": 120
}
```

**GET /api/v1/audits/{audit_id} response (complete):**
```json
{
  "id": "uuid",
  "site_id": "uuid",
  "status": "complete",
  "scores": {
    "overall": 74,
    "technical": 70,
    "content": 80,
    "eeeat": 65,
    "performance": 75,
    "structure": 85
  },
  "pages_crawled": 12,
  "issues": {
    "critical": 2,
    "warning": 8,
    "info": 3
  },
  "analysis": {
    "summary": "...",
    "quick_wins": [...],
    "priority_actions": [...],
    "positive_signals": [...]
  },
  "gsc_snapshot": { ... },
  "started_at": "2026-05-17T10:00:00Z",
  "completed_at": "2026-05-17T10:02:30Z"
}
```

**GET /api/v1/audits/{audit_id}/issues response:**
```json
{
  "issues": [
    {
      "id": "uuid",
      "page_url": "https://kedar.estate/projects/godrej-samaris",
      "category": "technical",
      "severity": "critical",
      "rule_id": "missing_title_tag",
      "rule_name": "Missing Title Tag",
      "description": "Page has no <title> tag.",
      "fix_suggestion": "Add a descriptive <title> tag...",
      "affected_value": null,
      "expected_value": "Godrej Samaris Sector 53 Gurgaon | Kedar Estate"
    }
  ],
  "total": 13,
  "filters": { "severity": null, "category": null }
}
```

**GET /api/v1/audits/{audit_id}/status response:**
```json
{
  "audit_id": "uuid",
  "status": "crawling",
  "progress_message": "Crawling page 8 of ~100...",
  "pages_crawled": 8,
  "started_at": "2026-05-17T10:00:00Z"
}
```

### 7.4 Reports

```
GET /api/v1/reports/site/{site_id}/history    Audit history + score trend for a site
GET /api/v1/reports/site/{site_id}/compare    Compare two audits side by side
GET /api/v1/reports/summary                   Dashboard summary across all sites
```

**GET /api/v1/reports/site/{site_id}/history response:**
```json
{
  "site_id": "uuid",
  "site_name": "Kedar Estate",
  "audits": [
    { "audit_id": "uuid", "date": "2026-05-01", "score": 74, "critical": 2, "warning": 8 },
    { "audit_id": "uuid", "date": "2026-04-01", "score": 68, "critical": 4, "warning": 11 }
  ],
  "trend": "+6 points over last 30 days"
}
```

**GET /api/v1/reports/summary response:**
```json
{
  "sites_total": 3,
  "sites_healthy": 1,
  "sites_warning": 1,
  "sites_critical": 1,
  "avg_score_all_sites": 71,
  "total_critical_issues": 6,
  "total_warning_issues": 24,
  "sites": [
    { "name": "Kedar Estate", "score": 74, "status": "warning", "last_audited": "2026-05-01" },
    { "name": "PropOS", "score": 82, "status": "healthy", "last_audited": "2026-05-01" }
  ]
}
```

### 7.5 API Tokens

```
GET    /api/v1/tokens           List all API tokens (prefixes only, never full tokens)
POST   /api/v1/tokens           Create a new API token (returns full token ONCE)
DELETE /api/v1/tokens/{id}      Revoke a token
```

**POST /api/v1/tokens request:**
```json
{
  "name": "PropOS Production",
  "scopes": ["audit:read", "audit:write", "site:read"],
  "expires_at": null
}
```

**POST /api/v1/tokens response:**
```json
{
  "id": "uuid",
  "name": "PropOS Production",
  "token": "pse_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "token_prefix": "pse_xxxx",
  "scopes": ["audit:read", "audit:write", "site:read"],
  "warning": "Store this token securely. It will not be shown again."
}
```

### 7.6 Webhooks

```
GET    /api/v1/webhooks         List webhook subscriptions
POST   /api/v1/webhooks         Create webhook subscription
DELETE /api/v1/webhooks/{id}    Remove webhook
POST   /api/v1/webhooks/test    Send test payload to a webhook URL
```

**Webhook payload (sent on audit.complete):**
```json
{
  "event": "audit.complete",
  "timestamp": "2026-05-17T10:02:30Z",
  "data": {
    "audit_id": "uuid",
    "site_id": "uuid",
    "site_url": "https://kedar.estate",
    "score_overall": 74,
    "issues_critical": 2,
    "issues_warning": 8,
    "status": "complete"
  }
}
```

Include HMAC-SHA256 signature in `X-SEO-Signature` header using the webhook secret.

---

## 8. FRONTEND PAGES

Build with Next.js 14, TypeScript, Tailwind CSS. Use SSR for data pages. Mobile responsive.

### Design direction
- **Aesthetic:** Clean, data-dense, professional. Dark sidebar, light content area.
- **Font:** Use `Geist` (Vercel's font — already in Next.js) for UI, `Geist Mono` for code/scores.
- **Colours:** Slate-900 sidebar, White content, Indigo-600 primary, Emerald-500 for healthy, Amber-500 for warning, Red-500 for critical.
- **Score display:** Large circular gauge (SVG arc) for overall score. Colour = Emerald (80+), Amber (50–79), Red (<50).
- **Never use:** Generic purple gradients, Inter font, cookie-cutter SaaS layouts.

### Page 1: Dashboard (`/`)
- Header: "SEO Health Dashboard"
- Summary cards row: Total Sites | Avg Score | Critical Issues | Audits This Month
- Sites list table: Name | Score (gauge) | Last Audited | Status badge | Audit Now button
- Recent audits timeline (last 5 across all sites)
- Quick wins panel (top 3 cross-site actionable items)

### Page 2: Sites List (`/sites`)
- Searchable, filterable table of all sites
- Add New Site button → modal with form fields matching POST /api/v1/sites
- Each row: Site name | Domain | Type | Schedule | Score | Last audited | Actions

### Page 3: Site Detail (`/sites/[siteId]`)
- Site header: name, domain, site type, schedule badge
- Score trend chart (line chart: last 6 audits, score over time)
- Current score breakdown: 5 category scores as horizontal bar gauges
- Audit history table: Date | Score | Pages | Issues (C/W/I) | View button
- Trigger New Audit button (calls POST /api/v1/audits, then polls status)
- Live audit status display when audit is running (progress bar, status message)

### Page 4: Audit Report (`/sites/[siteId]/audits/[auditId]`)
- Top: Overall score gauge + summary stats (pages crawled, issue counts)
- AI Summary section (analysis.summary)
- Quick Wins cards (top 3, styled distinctively)
- Score breakdown table (5 categories with scores and issue counts)
- Issues panel with filter tabs: All | Critical | Warning | Info | By Category
- Each issue card: Rule name | Severity badge | Page URL | Description | Fix suggestion
- Expandable fix details with code snippets where relevant
- GSC Data panel (shows mock data with "Connect GSC" CTA when PLACEHOLDER)

### Page 5: API Tokens (`/api-tokens`)
- Table of existing tokens (prefix only, name, scopes, created, last used)
- Create Token button → modal → show full token ONCE with copy button and warning
- Revoke button per token
- API documentation section: show base URL, auth header format, link to /docs (FastAPI auto-docs)

### Page 6: Settings (`/settings`)
- Notification email (for Resend) — [PLACEHOLDER note]
- Default crawl max_pages
- Default schedule
- Integration status cards:
  - Firecrawl: status dot (red "Not configured" if no API key), link to docs
  - Google Search Console: status dot, link to docs
  - Claude API: status dot, link to docs
  - Resend (email): status dot, link to docs
  Each card shows: "Set [ENV_VAR_NAME] environment variable to activate"

---

## 9. BACKGROUND JOBS (APScheduler)

In `services/scheduler.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def setup_scheduler(app):
    # Weekly audits: every Monday at 06:00 UTC
    scheduler.add_job(
        run_scheduled_audits,
        trigger="cron",
        day_of_week="mon",
        hour=6,
        minute=0,
        id="weekly_audits",
        replace_existing=True,
        kwargs={"schedule": "weekly"}
    )
    # Monthly audits: 1st of month at 07:00 UTC
    scheduler.add_job(
        run_scheduled_audits,
        trigger="cron",
        day=1,
        hour=7,
        minute=0,
        id="monthly_audits",
        replace_existing=True,
        kwargs={"schedule": "monthly"}
    )
    scheduler.start()

async def run_scheduled_audits(schedule: str):
    """
    Fetch all active sites with matching schedule,
    trigger an audit for each, fire webhooks on complete.
    """
    # Fetch sites from DB where schedule=schedule and is_active=True
    # For each site: create audit record, run crawl → analyse → score → update record
    # Fire webhook on complete
    pass
```

---

## 10. ENVIRONMENT VARIABLES

Generate a complete `.env.example` file with all variables:

```bash
# ─── DATABASE ────────────────────────────────────────────────
SUPABASE_URL=https://your-project.supabase.co          # [PLACEHOLDER]
SUPABASE_KEY=your-supabase-anon-key                    # [PLACEHOLDER]
DATABASE_URL=postgresql+asyncpg://user:pass@host/db    # [PLACEHOLDER]

# ─── AUTHENTICATION ──────────────────────────────────────────
JWT_SECRET=your-jwt-secret-min-32-chars                # [PLACEHOLDER] Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ─── EXTERNAL INTEGRATIONS ───────────────────────────────────
# Firecrawl — get key at firecrawl.dev
# Leave empty to use mock data (portal still fully functional)
FIRECRAWL_API_KEY=                                     # [PLACEHOLDER]

# Google Search Console — service account JSON path
# Leave empty to use mock GSC data
GSC_CREDENTIALS_PATH=                                  # [PLACEHOLDER]
GSC_SITE_URL=                                          # [PLACEHOLDER] e.g. sc-domain:kedar.estate

# Anthropic Claude API — get key at console.anthropic.com
# Leave empty to use mock AI analysis
ANTHROPIC_API_KEY=                                     # [PLACEHOLDER]

# ─── NOTIFICATIONS ───────────────────────────────────────────
# Resend — get key at resend.com
RESEND_API_KEY=                                        # [PLACEHOLDER]
RESEND_FROM_EMAIL=seo@kedar.estate                     # [PLACEHOLDER]
NOTIFICATION_EMAIL=rohan@kedar.estate                  # [PLACEHOLDER]

# ─── RATE LIMITING ───────────────────────────────────────────
# Upstash Redis — get at upstash.com
UPSTASH_REDIS_URL=                                     # [PLACEHOLDER]
UPSTASH_REDIS_TOKEN=                                   # [PLACEHOLDER]

# ─── APP CONFIG ──────────────────────────────────────────────
ENVIRONMENT=development                                 # development | production
APP_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
API_TOKEN_PREFIX=pse_                                  # Prefix for generated API tokens
LOG_LEVEL=INFO

# ─── FRONTEND (Next.js) ──────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Prithvi SEO Portal
```

---

## 11. BUILD SEQUENCE FOR CLAUDE CODE

Execute in this exact order. Do not proceed to the next step until current step builds without errors.

```
STEP 1: Backend scaffolding
  - Create folder structure (Section 3)
  - Install requirements.txt
  - Set up FastAPI app in main.py with CORS
  - Set up config.py reading all env vars
  - Set up database.py with SQLAlchemy async engine
  - Run: uvicorn main:app --reload

STEP 2: Database models
  - Create all SQLAlchemy models (Section 4)
  - Create Alembic migrations OR direct CREATE TABLE SQL
  - Verify tables exist in Supabase

STEP 3: SEO rules engine
  - Implement all rules in utils/seo_rules.py (Section 5.2)
  - Implement scorer.py (Section 5.3)
  - Write and pass all tests in tests/test_seo_rules.py and tests/test_scorer.py

STEP 4: Integration placeholders
  - Implement crawler.py with mock (Section 6.1)
  - Implement gsc.py with mock (Section 6.2)
  - Implement analyser.py with mock (Section 6.3)
  - Verify mock data flows through scorer correctly

STEP 5: Audit pipeline
  - Wire crawler → seo_rules → scorer → analyser into a single run_audit() function
  - run_audit() must: create audit record → set status=crawling → crawl → 
    status=analysing → run rules → score → get AI analysis → status=complete → 
    save all issues to DB → fire webhooks
  - run_audit() runs as a background task (FastAPI BackgroundTasks)

STEP 6: API routers
  - Implement all routers (Section 7) in order: sites → audits → reports → tokens → webhooks
  - Add JWT middleware (auth.py)
  - Verify all endpoints return correct shapes via FastAPI /docs

STEP 7: Scheduler
  - Implement scheduler.py (Section 9)
  - Wire into FastAPI startup event

STEP 8: Frontend scaffolding
  - Create Next.js 14 app with TypeScript
  - Set up Tailwind with custom tokens
  - Build layout: sidebar + header + content area
  - Create typed API client in lib/api.ts mirroring all endpoints

STEP 9: Frontend pages
  - Build pages in order: Dashboard → Sites → Site Detail → Audit Report → API Tokens → Settings
  - Each page must handle: loading state, error state, empty state, and populated state
  - Audit report page must poll /status endpoint every 3 seconds when audit is running

STEP 10: Integration status + docs
  - Settings page integration cards showing [PLACEHOLDER] status
  - Ensure FastAPI /docs is accessible and complete
  - Generate openapi.json and save to /docs/openapi.json
  - Write /docs/API_USAGE.md with curl examples for all endpoints

STEP 11: Tests and README
  - Pass all backend tests
  - Write README.md with: project description, local setup steps, env var guide, 
    how to trigger your first audit, how to connect real integrations
```

---

## 12. PROPROS INTEGRATION NOTES

When PropOS calls this portal's API to auto-audit broker pages:

1. PropOS backend registers the broker's page as a site via `POST /api/v1/sites`
2. On broker page publish, PropOS calls `POST /api/v1/audits` with the site_id
3. PropOS polls `GET /api/v1/audits/{audit_id}/status` every 5 seconds, OR
4. PropOS subscribes a webhook via `POST /api/v1/webhooks` pointing to its own endpoint
5. On webhook receipt, PropOS reads the score and issue count
6. If score < 70 or critical_issues > 0: Prithvi sends WhatsApp to broker
7. PropOS reads full issues via `GET /api/v1/audits/{audit_id}/issues?severity=critical`
8. Prithvi presents issues to broker in plain language via WhatsApp

The audit portal is a standalone service. PropOS talks to it purely via the REST API using an API token with scopes `["audit:read", "audit:write", "site:read"]`.

---

## 13. LOADING THE SEO STRATEGY INTO CLAUDE ANALYSIS

When real Claude API integration is built (Step 5 of real integration, not placeholder):

Load `SEO_STRATEGY_CLAUDE_CODE.md` as system prompt context in `services/analyser.py`.

The prompt structure for real Claude API call:
```
System: [Contents of SEO_STRATEGY_CLAUDE_CODE.md]

User: You are auditing {site_url}. 
Pages crawled: {pages_crawled}
Overall score: {overall_score}/100
Issues found: {critical_count} critical, {warning_count} warnings, {info_count} info

Issue list (top 10 by severity):
{json.dumps(top_issues, indent=2)}

GSC data:
{json.dumps(gsc_data, indent=2)}

Provide:
1. A 2-3 paragraph executive summary of the site's SEO health
2. The top 3 "quick wins" — highest impact, lowest effort fixes
3. An assessment of content quality against E-E-A-T standards
4. 5 priority actions in order of impact

Respond ONLY in JSON matching this schema:
{"summary": str, "quick_wins": [{"title", "effort", "impact", "description"}], 
 "content_assessment": str, "priority_actions": [str], "positive_signals": [str]}
```

---

## 14. SECURITY REQUIREMENTS

Implement all of the following:

- JWT tokens expire in 24 hours (configurable via JWT_EXPIRE_MINUTES)
- API tokens are bcrypt-hashed in DB — never stored plaintext
- API tokens shown only once on creation
- Webhook payloads signed with HMAC-SHA256
- Rate limiting: 100 requests/minute per IP (Upstash Redis [PLACEHOLDER], use in-memory dict fallback if no Upstash configured)
- CORS: Allow only FRONTEND_URL origin in production
- All DB queries use parameterised statements (SQLAlchemy enforces this)
- No sensitive env vars logged
- `.env` in `.gitignore`

---

*Build document version 1.0 — May 2026*  
*Companion: SEO_STRATEGY_CLAUDE_CODE.md (feed both to Claude Code together)*
