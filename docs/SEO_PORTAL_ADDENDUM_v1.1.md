# SEO PORTAL — ADDENDUM SPEC v1.1
# Cross-Site Comparison + Backlink Placeholder
# Feed this to Claude Code alongside SEO_PORTAL_BUILD_DOC.md
# Add AFTER Step 7 (Scheduler) is complete. Does not modify any existing code.

---

## CONTEXT

You have already built Steps 1–7 per SEO_PORTAL_BUILD_DOC.md. This addendum adds two
features that were not in the original spec:

1. Cross-site comparison — compare SEO scores across 2 or more different sites
2. Backlink placeholder — structured placeholder in audit data with DataForSEO as the
   future integration target

Both features slot into the existing architecture without modifying anything already built.
New files only, plus additions to existing routers and frontend pages.

---

## FEATURE 1: CROSS-SITE COMPARISON

### 1.1 What it does

Accepts 2–5 site_ids, fetches the most recent completed audit for each, and returns
scores and issue counts side by side. Used to compare:
- Kedar Estate vs PropOS vs a competitor site (manually registered)
- Any set of broker landing pages against each other
- Your site vs a competitor you've added to the portal

### 1.2 New API endpoint — add to routers/reports.py

```
GET /api/v1/reports/compare?site_ids=uuid1,uuid2,uuid3
```

Rules:
- Minimum 2 site_ids, maximum 5
- Returns 400 if fewer than 2 or more than 5 provided
- Returns 404 if any site_id does not exist
- Returns 422 if any site has no completed audit yet (include which sites are missing)
- Fetches the most recent audit with status="complete" for each site_id
- site_ids passed as comma-separated query param string, parse and split server-side

**Request:**
```
GET /api/v1/reports/compare?site_ids=uuid-kedar,uuid-propos,uuid-competitor
Authorization: Bearer pse_xxxx
```

**Response shape:**
```json
{
  "generated_at": "2026-05-18T10:00:00Z",
  "sites": [
    {
      "site_id": "uuid-kedar",
      "site_name": "Kedar Estate",
      "domain": "kedar.estate",
      "site_type": "brokerage",
      "audit_id": "uuid",
      "audit_date": "2026-05-17T10:00:00Z",
      "scores": {
        "overall": 74,
        "technical": 70,
        "content": 80,
        "eeeat": 65,
        "performance": 75,
        "structure": 85
      },
      "issues": {
        "critical": 2,
        "warning": 8,
        "info": 3
      },
      "pages_crawled": 12,
      "rank": 2
    },
    {
      "site_id": "uuid-propos",
      "site_name": "PropOS",
      "domain": "propos.in",
      "site_type": "saas",
      "audit_id": "uuid",
      "audit_date": "2026-05-16T10:00:00Z",
      "scores": {
        "overall": 82,
        "technical": 85,
        "content": 78,
        "eeeat": 80,
        "performance": 88,
        "structure": 79
      },
      "issues": {
        "critical": 0,
        "warning": 5,
        "info": 4
      },
      "pages_crawled": 28,
      "rank": 1
    }
  ],
  "leader": {
    "site_id": "uuid-propos",
    "site_name": "PropOS",
    "overall_score": 82
  },
  "category_leaders": {
    "technical": "uuid-propos",
    "content": "uuid-kedar",
    "eeeat": "uuid-propos",
    "performance": "uuid-propos",
    "structure": "uuid-kedar"
  },
  "gaps": [
    {
      "category": "eeeat",
      "site_id": "uuid-kedar",
      "site_name": "Kedar Estate",
      "score": 65,
      "leader_score": 80,
      "gap": 15,
      "note": "Largest gap — highest priority to close"
    }
  ]
}
```

Notes on response fields:
- `rank`: integer 1 = highest overall score among the compared sites
- `leader`: the site with the highest overall score
- `category_leaders`: for each of the 5 categories, which site_id leads
- `gaps`: for each site, identify its worst category gap vs the category leader,
  sorted by gap size descending. Include only gaps > 10 points.

### 1.3 Service logic — add to services/ as compare_service.py

```python
# services/compare_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.site import Site
from models.audit import Audit

SCORE_KEYS = ["overall", "technical", "content", "eeeat", "performance", "structure"]

async def get_comparison(site_ids: list[str], db: AsyncSession) -> dict:
    """
    Fetches latest completed audit for each site_id.
    Calculates ranks, leaders, and gaps.
    Raises ValueError with message if validation fails.
    """
    if len(site_ids) < 2:
        raise ValueError("At least 2 site_ids required")
    if len(site_ids) > 5:
        raise ValueError("Maximum 5 site_ids allowed")

    results = []
    missing_audits = []

    for site_id in site_ids:
        # Fetch site
        site = await db.get(Site, site_id)
        if not site:
            raise ValueError(f"Site not found: {site_id}")

        # Fetch latest completed audit
        stmt = (
            select(Audit)
            .where(Audit.site_id == site_id, Audit.status == "complete")
            .order_by(desc(Audit.completed_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        audit = result.scalar_one_or_none()

        if not audit:
            missing_audits.append(site.name)
            continue

        results.append({
            "site_id": str(site.id),
            "site_name": site.name,
            "domain": site.domain,
            "site_type": site.site_type,
            "audit_id": str(audit.id),
            "audit_date": audit.completed_at.isoformat(),
            "scores": {
                "overall": audit.score_overall,
                "technical": audit.score_technical,
                "content": audit.score_content,
                "eeeat": audit.score_eeeat,
                "performance": audit.score_performance,
                "structure": audit.score_structure,
            },
            "issues": {
                "critical": audit.issues_critical,
                "warning": audit.issues_warning,
                "info": audit.issues_info,
            },
            "pages_crawled": audit.pages_crawled,
        })

    if missing_audits:
        raise ValueError(
            f"No completed audits found for: {', '.join(missing_audits)}. "
            f"Trigger an audit for these sites first."
        )

    # Sort by overall score descending and assign rank
    results.sort(key=lambda x: x["scores"]["overall"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    # Leader (highest overall)
    leader = results[0]

    # Category leaders
    category_leaders = {}
    for cat in ["technical", "content", "eeeat", "performance", "structure"]:
        best = max(results, key=lambda x: x["scores"][cat])
        category_leaders[cat] = best["site_id"]

    # Gaps — for each site, find worst category gap vs leader of that category
    gaps = []
    for site_data in results:
        for cat in ["technical", "content", "eeeat", "performance", "structure"]:
            leader_id = category_leaders[cat]
            if site_data["site_id"] == leader_id:
                continue
            leader_data = next(r for r in results if r["site_id"] == leader_id)
            gap = leader_data["scores"][cat] - site_data["scores"][cat]
            if gap > 10:
                gaps.append({
                    "category": cat,
                    "site_id": site_data["site_id"],
                    "site_name": site_data["site_name"],
                    "score": site_data["scores"][cat],
                    "leader_score": leader_data["scores"][cat],
                    "gap": gap,
                })

    gaps.sort(key=lambda x: x["gap"], reverse=True)
    if gaps:
        gaps[0]["note"] = "Largest gap — highest priority to close"

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sites": results,
        "leader": {
            "site_id": leader["site_id"],
            "site_name": leader["site_name"],
            "overall_score": leader["scores"]["overall"],
        },
        "category_leaders": category_leaders,
        "gaps": gaps,
    }
```

### 1.4 Router addition — append to routers/reports.py

```python
@router.get("/compare")
async def compare_sites(
    site_ids: str = Query(..., description="Comma-separated list of 2–5 site UUIDs"),
    db: AsyncSession = Depends(get_db),
    current_token: APIToken = Depends(require_auth),
):
    """Compare latest audit scores across multiple sites."""
    ids = [s.strip() for s in site_ids.split(",") if s.strip()]
    try:
        result = await get_comparison(ids, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result
```

### 1.5 Frontend — new page: /compare

**Route:** `/compare`  
**Nav label:** "Compare Sites"  
**Add to sidebar** between "Sites" and "API Tokens"

**Page layout:**

```
┌─────────────────────────────────────────────────────┐
│  Compare Sites                                       │
│                                                      │
│  [Site selector — dropdown, multi-select, max 5]    │
│  [+ Add site]  [Compare →]                          │
└─────────────────────────────────────────────────────┘

┌─── Score Overview ──────────────────────────────────┐
│                                                      │
│  [Kedar Estate]    [PropOS]    [Competitor]          │
│       74               82           61               │
│    (rank #2)        (rank #1)    (rank #3)           │
│                                                      │
│  [Score comparison bar chart — horizontal bars      │
│   grouped by category, one bar per site per row]    │
└─────────────────────────────────────────────────────┘

┌─── Category Breakdown table ────────────────────────┐
│  Category    │ Kedar Estate │ PropOS │ Competitor   │
│  Technical   │    70        │  85 🏆 │    62        │
│  Content     │    80 🏆     │  78    │    65        │
│  E-E-A-T     │    65        │  80 🏆 │    55        │
│  Performance │    75        │  88 🏆 │    70        │
│  Structure   │    85 🏆     │  79    │    68        │
└─────────────────────────────────────────────────────┘

┌─── Gaps to close ───────────────────────────────────┐
│  Biggest opportunities vs the leader:               │
│  [gap cards sorted by gap size]                     │
└─────────────────────────────────────────────────────┘
```

**Implementation notes:**
- Site selector: multi-select dropdown populated from GET /api/v1/sites
- Disable "Compare" button until ≥ 2 sites selected
- Show max 5 in selector — disable adding more once 5 selected
- Trophy emoji 🏆 on highest score per category row
- Bar chart: use recharts `BarChart` with grouped bars, one `Bar` per site
- Colour per site: use a fixed palette [Indigo, Emerald, Amber, Rose, Violet]
  assigned in order of site selection, consistent across table and chart
- Gaps section: card per gap, sorted by gap size. Show: site name, category,
  their score, leader score, gap amount. Amber border for gaps 10–20, Red for >20
- Empty state: "Select 2 or more sites and click Compare to see results"
- Loading state: skeleton bars in chart area
- Share: add a "Copy link" button that encodes site_ids into URL query params
  so the comparison is bookmarkable: `/compare?site_ids=uuid1,uuid2`

---

## FEATURE 2: BACKLINK PLACEHOLDER

### 2.1 What it does

Adds a `backlinks` object to every audit result. When no API key is configured,
returns a clearly labelled placeholder with mock-shaped data. When DataForSEO
API key is set (future), fetches real data. No other audit logic changes.

### 2.2 New service file — services/backlinks.py

```python
# services/backlinks.py
# Backlink data integration — DataForSEO as target provider
# Currently runs in placeholder/mock mode when no API key is configured.

import os
import httpx
from datetime import datetime

DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN", "")       # [PLACEHOLDER]
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "") # [PLACEHOLDER]
DATAFORSEO_BASE = "https://api.dataforseo.com/v3"

async def get_backlink_data(domain: str) -> dict:
    """
    Fetches backlink summary for a domain.

    Real implementation: POST to DataForSEO
    /backlinks/summary/live with the domain.
    Cost: ~$0.0015 per request at standard pricing.

    Returns BacklinkData dict (same shape regardless of source).
    """
    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        return _mock_backlink_data(domain)

    # TODO: implement real DataForSEO call when credentials are set
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         f"{DATAFORSEO_BASE}/backlinks/summary/live",
    #         auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
    #         json=[{"target": domain, "include_subdomains": True}]
    #     )
    #     data = response.json()["tasks"][0]["result"][0]
    #     return _parse_dataforseo_response(data, domain)
    raise NotImplementedError(
        "[PLACEHOLDER] Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD to enable real backlink data"
    )


def _mock_backlink_data(domain: str) -> dict:
    """
    Mock backlink data — same shape as real DataForSEO response after parsing.
    Returns zeroed data appropriate for a new/untracked site.
    """
    return {
        "domain": domain,
        "data_source": "mock",                  # "dataforseo" when real
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "domain_rank": 0,                       # DataForSEO's domain rank score (0–100)
        "referring_domains": 0,                 # Unique domains linking to this domain
        "referring_pages": 0,                   # Total pages with at least one backlink
        "backlinks_total": 0,                   # Total backlink count
        "backlinks_dofollow": 0,                # Follow links count
        "backlinks_nofollow": 0,                # Nofollow links count
        "broken_backlinks": 0,                  # Links pointing to 404 pages
        "top_referring_domains": [],            # List of {domain, rank, backlinks_count}
        "anchor_distribution": [],              # List of {anchor_text, count, percent}
        "new_lost": {
            "new_referring_domains_30d": 0,     # New domains linking in last 30 days
            "lost_referring_domains_30d": 0,    # Domains that stopped linking in last 30 days
        },
        "placeholder_note": (
            "Backlink data is not yet configured. "
            "Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD environment variables to enable. "
            "Cost: ~₹0.12 per domain lookup. Free alternative: use Ahrefs Webmaster Tools "
            "at ahrefs.com/webmaster-tools for your own verified sites."
        )
    }


def _parse_dataforseo_response(data: dict, domain: str) -> dict:
    """Parse real DataForSEO response into BacklinkData shape."""
    # TODO: implement when DATAFORSEO credentials are set
    return {
        "domain": domain,
        "data_source": "dataforseo",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
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
            "lost_referring_domains_30d": data.get("lost_referring_domains", 0),
        },
        "placeholder_note": None,
    }
```

### 2.3 Wire into audit pipeline — one addition to run_audit()

In the existing `run_audit()` function (Step 5 of original build doc), add one call
after scoring is complete and before saving to DB:

```python
# In run_audit(), after calculate_score(), before saving audit record:

from services.backlinks import get_backlink_data

# Fetch backlink data (mock if no credentials configured)
backlink_data = await get_backlink_data(site.domain)

# Save to audit record — add backlink_data to the audit's metadata JSONB field:
audit.metadata = {
    **(audit.metadata or {}),
    "backlinks": backlink_data
}
```

No schema change needed — `metadata JSONB` column already exists on the audits table
per the original build doc. Backlink data lives in `audit.metadata["backlinks"]`.

### 2.4 Expose in existing audit endpoint

In `GET /api/v1/audits/{audit_id}` response (already built in routers/audits.py),
add `backlinks` field pulled from `audit.metadata.get("backlinks", {})`:

```python
# In the existing audit detail response dict, add:
"backlinks": audit.metadata.get("backlinks", {}) if audit.metadata else {}
```

That's the only change to an existing file.

### 2.5 New environment variables — add to .env.example

```bash
# ─── BACKLINK DATA (DataForSEO) ──────────────────────────────
# Get credentials at dataforseo.com — pay-per-use, no monthly minimum
# Cost: ~$0.0015 per domain lookup (~₹0.12)
# Leave empty to use mock placeholder data
DATAFORSEO_LOGIN=                                      # [PLACEHOLDER]
DATAFORSEO_PASSWORD=                                   # [PLACEHOLDER]
```

### 2.6 Frontend — backlinks panel in audit report page

In the existing Audit Report page (`/sites/[siteId]/audits/[auditId]`), add a
"Backlinks" section after the Scores section and before the Issues panel.

**When placeholder (data_source = "mock"):**
```
┌─── Backlinks ───────────────────────────────────────────────┐
│                                                              │
│  🔗 Backlink data not configured          [Connect →]       │
│                                                              │
│  Set DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD to see:         │
│  Domain rank · Referring domains · Total backlinks           │
│  New/lost domains · Top referring sites · Anchor text        │
│                                                              │
│  Cost: ~₹0.12 per audit  ·  dataforseo.com                  │
│  Free alternative: Ahrefs Webmaster Tools (your sites only) │
└─────────────────────────────────────────────────────────────┘
```

**When real data (data_source = "dataforseo"):**
```
┌─── Backlinks  [via DataForSEO]  [fetched_at date] ──────────┐
│                                                              │
│  Domain Rank    Ref. Domains    Total Links    Broken Links  │
│      47              312           8,420            23       │
│                                                              │
│  New domains (30d): +12     Lost domains (30d): -4          │
│                                                              │
│  Top referring domains:                                      │
│  [table: domain | rank | backlink count]                     │
│                                                              │
│  Anchor text distribution:                                   │
│  [horizontal bar chart: anchor | % of links]                │
└─────────────────────────────────────────────────────────────┘
```

Styling notes:
- Placeholder state: Amber border, amber background, amber text — consistent with
  other placeholder cards in the Settings page
- Real data state: same card style as the Scores section
- "Connect →" button links to `/settings` where the env var instructions are shown

### 2.7 Settings page addition

In the existing Settings page integration status cards, add DataForSEO as a fourth card:

```
DataForSEO                              ● Not configured
Backlink data for audit reports
Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD
~₹0.12 per domain lookup · dataforseo.com
```

---

## SUMMARY — FILES TOUCHED / CREATED

### New files (create from scratch):
```
backend/services/compare_service.py     Feature 1 service logic
backend/services/backlinks.py           Feature 2 service + placeholder
frontend/src/app/compare/page.tsx       Feature 1 frontend page
```

### Existing files (minimal additions only):
```
backend/routers/reports.py              Add GET /api/v1/reports/compare endpoint
backend/services/audit_pipeline.py     Add backlink_data fetch call in run_audit()
backend/routers/audits.py              Add "backlinks" field to audit detail response
backend/.env.example                   Add DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD
frontend/src/components/layout/Sidebar Add "Compare Sites" nav item
frontend/src/app/sites/[siteId]/audits/[auditId]/page.tsx  Add Backlinks panel
frontend/src/app/settings/page.tsx     Add DataForSEO status card
```

### No changes to:
```
Database schema        (backlinks stored in existing metadata JSONB)
models/                (no new models needed)
Auth/middleware        (same JWT auth applies to new endpoint automatically)
Scheduler              (no scheduled backlink fetches — only on audit trigger)
```

---

## BUILD ORDER FOR THIS ADDENDUM

Do Feature 2 (backlinks) first — it's simpler and only touches one new file
plus minor additions to existing files. Feature 1 (compare) is independent and
can be done second.

```
Step A: Create services/backlinks.py
Step B: Add backlink fetch call to run_audit() in audit pipeline
Step C: Add "backlinks" field to GET /api/v1/audits/{id} response
Step D: Add DATAFORSEO vars to .env.example
Step E: Add Backlinks panel to audit report frontend page
Step F: Add DataForSEO card to Settings page
        ── verify Feature 2 works end-to-end before proceeding ──
Step G: Create services/compare_service.py
Step H: Add GET /api/v1/reports/compare endpoint to routers/reports.py
Step I: Create /compare frontend page with site selector + chart + table
Step J: Add "Compare Sites" to sidebar nav
        ── verify Feature 1 works end-to-end ──
```

---

*Addendum v1.1 — May 2026*
*Parent document: SEO_PORTAL_BUILD_DOC.md*
*Apply after Step 7 (Scheduler) of the original build sequence*
