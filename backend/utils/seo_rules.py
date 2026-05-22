"""All SEO check rules — Section 5.2. Pure logic, no external dependencies.

Each rule is a dict: ``id``, ``name``, ``severity`` (critical|warning|info),
``category`` (technical|content|eeeat|performance|structure), ``check`` (a
callable taking the page-data dict and returning truthy on violation),
``description`` (what's wrong) and ``fix`` (how to fix it).

``evaluate_page`` runs every rule against one page-data dict (PageData schema,
Section 6.1) and returns issue dicts shaped for the ``audit_issues`` table
(Section 4.3). ``evaluate_pages`` aggregates across a whole crawl.
"""

import logging
import re

logger = logging.getLogger("seo_portal.seo_rules")


# ── TECHNICAL ───────────────────────────────────────────────────────────
RULE_TECHNICAL = [
    {
        "id": "missing_title_tag",
        "name": "Missing Title Tag",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: not page.get("title"),
        "description": "Page has no <title> tag. Title tags are critical for indexing and click-through rates.",
        "fix": "Add a descriptive <title> tag between 50–60 characters. Include the primary keyword and brand name.",
    },
    {
        "id": "title_too_short",
        "name": "Title Tag Too Short",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: page.get("title") and len(page["title"]) < 30,
        "description": "Title tag is under 30 characters. Too short to be descriptive.",
        "fix": "Expand the title to 50–60 characters with primary keyword + location + brand.",
    },
    {
        "id": "title_too_long",
        "name": "Title Tag Too Long",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: page.get("title") and len(page["title"]) > 60,
        "description": "Title tag is over 60 characters. Google truncates at ~600px.",
        "fix": "Shorten the title to 50–60 characters without losing the primary keyword.",
    },
    {
        "id": "missing_meta_description",
        "name": "Missing Meta Description",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("meta_description"),
        "description": "No meta description. While not a direct ranking factor, it affects click-through rate from search results.",
        "fix": "Add a unique meta description of 120–160 characters. Summarise the page and include a call to action.",
    },
    {
        "id": "meta_description_too_long",
        "name": "Meta Description Too Long",
        "severity": "info",
        "category": "technical",
        "check": lambda page: page.get("meta_description")
        and len(page["meta_description"]) > 160,
        "description": "Meta description exceeds 160 characters and will be truncated in search results.",
        "fix": "Shorten to 120–160 characters, keeping the most important information at the start.",
    },
    {
        "id": "missing_h1",
        "name": "Missing H1 Tag",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: not page.get("h1") or len(page.get("h1", [])) == 0,
        "description": "Page has no H1 heading. H1 is a key on-page SEO signal.",
        "fix": "Add one H1 tag containing the primary keyword for this page.",
    },
    {
        "id": "multiple_h1",
        "name": "Multiple H1 Tags",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: len(page.get("h1", [])) > 1,
        "description": "Page has multiple H1 tags. Only one H1 per page is best practice.",
        "fix": "Keep only one H1 tag. Convert additional H1s to H2 or H3 as appropriate.",
    },
    {
        "id": "images_missing_alt",
        "name": "Images Missing Alt Text",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: any(
            not img.get("alt") for img in page.get("images", [])
        ),
        "description": "One or more images have no alt attribute. Alt text helps Google understand images and aids accessibility.",
        "fix": "Add descriptive alt text to every image. Describe what the image shows, not the filename.",
    },
    {
        "id": "no_canonical_tag",
        "name": "Missing Canonical Tag",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("canonical"),
        "description": "No canonical tag found. Without it, Google may index duplicate versions of this page.",
        "fix": "Add <link rel='canonical' href='[full URL]'> in the <head> of every page.",
    },
    {
        "id": "http_not_https",
        "name": "Not Served Over HTTPS",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: page.get("url", "").startswith("http://"),
        "description": "Page is served over HTTP. HTTPS is a ranking signal and Chrome marks HTTP as 'Not Secure'.",
        "fix": "Configure SSL certificate and redirect all HTTP to HTTPS at server level.",
    },
    {
        "id": "noindex_detected",
        "name": "Noindex Tag Detected",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: page.get("noindex") is True,
        "description": "Page has a noindex meta tag. Google will NOT index this page.",
        "fix": "Remove the <meta name='robots' content='noindex'> tag if this page should appear in search.",
    },
    {
        "id": "missing_structured_data",
        "name": "No Structured Data (Schema.org)",
        "severity": "warning",
        "category": "technical",
        "check": lambda page: not page.get("structured_data"),
        "description": "No JSON-LD or Schema.org markup found. Structured data enables rich results in Google.",
        "fix": "Add appropriate JSON-LD schema. For real estate pages: RealEstateAgent + Product. For blog posts: Article.",
    },
    {
        "id": "broken_internal_links",
        "name": "Broken Internal Links",
        "severity": "critical",
        "category": "technical",
        "check": lambda page: len(page.get("broken_links", [])) > 0,
        "description": "Page has internal links pointing to 404 or error pages.",
        "fix": "Fix or remove broken internal links. Update URLs or redirect old pages.",
    },
]

# ── CONTENT ─────────────────────────────────────────────────────────────
RULE_CONTENT = [
    {
        "id": "thin_content",
        "name": "Thin Content",
        "severity": "warning",
        "category": "content",
        "check": lambda page: page.get("word_count", 0) < 300,
        "description": "Page has fewer than 300 words. Thin content rarely ranks well.",
        "fix": "Expand content to at least 600 words with genuine, first-hand information relevant to the page topic.",
    },
    {
        "id": "commodity_content_risk",
        "name": "Potential Commodity Content",
        "severity": "info",
        "category": "content",
        "check": lambda page: page.get("word_count", 0) < 500
        and not page.get("has_author_byline"),
        "description": "Short page with no author attribution. May not pass Google's E-E-A-T evaluation.",
        "fix": "Add a named author byline and expand content with first-hand expertise, specific data, and unique insights.",
    },
    {
        "id": "duplicate_title_across_site",
        "name": "Duplicate Title Tag",
        "severity": "critical",
        "category": "content",
        "check": lambda page: page.get("title_duplicate") is True,
        "description": "This title tag appears on more than one page on the site.",
        "fix": "Every page must have a unique title tag. Rewrite to reflect the specific content of this page.",
    },
    {
        "id": "duplicate_meta_description",
        "name": "Duplicate Meta Description",
        "severity": "warning",
        "category": "content",
        "check": lambda page: page.get("meta_duplicate") is True,
        "description": "This meta description is used on multiple pages.",
        "fix": "Write a unique meta description for every page. Describe what specifically this page offers.",
    },
    {
        "id": "no_images",
        "name": "No Images Found",
        "severity": "info",
        "category": "content",
        "check": lambda page: len(page.get("images", [])) == 0
        and page.get("page_type") in ["project", "property", "blog"],
        "description": "No images found on a page that would benefit from visual content.",
        "fix": "Add high-quality, relevant images. For property pages: site visit photos. For blog posts: featured images.",
    },
]

# ── E-E-A-T ─────────────────────────────────────────────────────────────
RULE_EEEAT = [
    {
        "id": "no_author_byline",
        "name": "No Author Byline",
        "severity": "warning",
        "category": "eeeat",
        "check": lambda page: not page.get("has_author_byline")
        and page.get("page_type") in ["blog", "review", "article"],
        "description": "Content page has no visible author attribution. E-E-A-T requires showing WHO created the content.",
        "fix": "Add a named author byline with a link to the author's bio page. Include their relevant credentials.",
    },
    {
        "id": "no_publish_date",
        "name": "No Publication Date",
        "severity": "info",
        "category": "eeeat",
        "check": lambda page: not page.get("publish_date")
        and page.get("page_type") in ["blog", "review", "article"],
        "description": "No publication date visible on content page. Freshness signals matter for trust.",
        "fix": "Show the publication date (and last updated date) prominently on all content pages.",
    },
    {
        "id": "no_contact_info",
        "name": "No Contact Information",
        "severity": "warning",
        "category": "eeeat",
        "check": lambda page: not page.get("has_contact_info")
        and page.get("is_homepage"),
        "description": "Homepage has no visible contact information. Trust signals require clear contact details.",
        "fix": "Add phone number, email, and physical address to homepage and contact page.",
    },
]

# ── PERFORMANCE ─────────────────────────────────────────────────────────
RULE_PERFORMANCE = [
    {
        "id": "lcp_poor",
        "name": "Poor LCP (Largest Contentful Paint)",
        "severity": "critical",
        "category": "performance",
        "check": lambda page: page.get("lcp_ms", 0) > 4000,
        "description": "LCP is over 4 seconds. Google considers anything over 2.5s 'Poor'. This suppresses rankings.",
        "fix": "Optimise: compress images to WebP, lazy load below-fold images, enable server-side rendering, reduce JS bundle size.",
    },
    {
        "id": "lcp_needs_improvement",
        "name": "LCP Needs Improvement",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: 2500 < page.get("lcp_ms", 0) <= 4000,
        "description": "LCP is between 2.5–4 seconds. Should be under 2.5s.",
        "fix": "Compress images, enable caching, reduce server response time.",
    },
    {
        "id": "cls_poor",
        "name": "High Cumulative Layout Shift",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: page.get("cls_score", 0) > 0.1,
        "description": "CLS score exceeds 0.1. Page content is shifting as it loads, harming UX and rankings.",
        "fix": "Set explicit width and height on all images and embeds. Avoid inserting content above existing content.",
    },
    {
        # Addendum v1.2 — fed real INP from PageSpeed Insights lab data.
        "id": "inp_poor",
        "name": "Poor INP (Interaction to Next Paint)",
        "severity": "warning",
        "category": "performance",
        "check": lambda page: page.get("inp_ms", 0) > 200,
        "description": "INP is over 200ms. Interactions feel sluggish; Google's threshold for 'good' is 200ms.",
        "fix": "Reduce JavaScript execution time, break up long tasks, and defer non-critical third-party scripts.",
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
        "fix": "Convert images to WebP format. In Next.js, use the built-in <Image> component which auto-converts.",
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
        "fix": "Add explicit width and height attributes to all <img> tags. Use aspect-ratio CSS as alternative.",
    },
]

# ── STRUCTURE ───────────────────────────────────────────────────────────
RULE_STRUCTURE = [
    {
        "id": "non_descriptive_url",
        "name": "Non-Descriptive URL",
        "severity": "warning",
        "category": "structure",
        "check": lambda page: bool(
            re.search(r"[?&=]|\d{6,}", page.get("url", ""))
        ),
        "description": "URL contains query parameters or numeric IDs instead of descriptive words.",
        "fix": "Use descriptive slugs like /projects/godrej-samaris-sector-53 instead of /p?id=12345.",
    },
    {
        "id": "url_uppercase",
        "name": "URL Contains Uppercase Characters",
        "severity": "info",
        "category": "structure",
        "check": lambda page: any(
            c.isupper() for c in page.get("url", "").split("//")[-1]
        ),
        "description": "URLs with uppercase characters can cause duplicate content issues.",
        "fix": "Use all-lowercase URLs. Configure server to redirect uppercase to lowercase versions.",
    },
    {
        "id": "no_internal_links",
        "name": "Page Has No Internal Links",
        "severity": "warning",
        "category": "structure",
        "check": lambda page: len(page.get("internal_links", [])) == 0,
        "description": "Page is an orphan with no internal links pointing to other pages. Reduces crawl depth and PageRank flow.",
        "fix": "Add at least 2–3 internal links to related pages using descriptive anchor text.",
    },
    {
        "id": "heading_hierarchy_broken",
        "name": "Broken Heading Hierarchy",
        "severity": "info",
        "category": "structure",
        "check": lambda page: page.get("heading_hierarchy_broken") is True,
        "description": "Heading levels skip (e.g. H1 → H3 with no H2). Hurts accessibility and structure signals.",
        "fix": "Use headings in order: H1 → H2 → H3. Do not skip levels.",
    },
]

RULES_BY_CATEGORY = {
    "technical": RULE_TECHNICAL,
    "content": RULE_CONTENT,
    "eeeat": RULE_EEEAT,
    "performance": RULE_PERFORMANCE,
    "structure": RULE_STRUCTURE,
}

ALL_RULES = [
    rule for rules in RULES_BY_CATEGORY.values() for rule in rules
]


def _issue_from_rule(rule: dict, page: dict) -> dict:
    """Shape a matched rule into an ``audit_issues`` row (Section 4.3).

    ``affected_value`` / ``expected_value`` stay None here — they are
    page-specific and enriched later by the analyser (Section 6.3), not
    derivable from a pure rule.
    """
    return {
        "page_url": page.get("url"),
        "category": rule["category"],
        "severity": rule["severity"],
        "rule_id": rule["id"],
        "rule_name": rule["name"],
        "description": rule["description"],
        "fix_suggestion": rule["fix"],
        "affected_value": None,
        "expected_value": None,
    }


def evaluate_page(page: dict) -> list[dict]:
    """Run every rule against one page-data dict. Returns issue dicts.

    A rule whose check raises (malformed crawl data) is logged and skipped
    rather than aborting the whole audit.
    """
    issues: list[dict] = []
    for rule in ALL_RULES:
        try:
            triggered = bool(rule["check"](page))
        except Exception:  # noqa: BLE001 — never let one bad rule kill the audit
            logger.warning(
                "Rule %s raised on page %s; skipping",
                rule["id"],
                page.get("url"),
                exc_info=True,
            )
            continue
        if triggered:
            issues.append(_issue_from_rule(rule, page))
    return issues


def evaluate_pages(pages: list[dict]) -> list[dict]:
    """Evaluate a whole crawl. Flat list of issues across all pages."""
    issues: list[dict] = []
    for page in pages:
        issues.extend(evaluate_page(page))
    return issues
