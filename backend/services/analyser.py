"""Claude API analysis engine [PLACEHOLDER] — Section 6.3.

When ``ANTHROPIC_API_KEY`` is unset, returns a mock analysis shaped
identically to the real Claude response. The real path (later step) uses
Haiku 4.5 with SEO_STRATEGY_CLAUDE_CODE.md as system-prompt context
(Section 13).
"""

import logging

from config import settings

logger = logging.getLogger("seo_portal.analyser")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # cost-efficient for audits


async def analyse_audit(
    site_url: str,
    pages_data: list[dict],
    issues: list[dict],
    scores: dict,
    gsc_data: dict,
    seo_strategy_context: str = "",
) -> dict:
    """Generate a narrative analysis of the audit.

    Returns an AnalysisResult dict:
      summary: str               — 2–3 paragraph executive summary
      quick_wins: list[dict]     — top 3 highest-impact, lowest-effort fixes
      content_assessment: str    — content quality vs E-E-A-T
      priority_actions: list     — ordered recommended actions
      positive_signals: list     — what's already working
    """
    if not settings.anthropic_enabled:
        # [PLACEHOLDER] no API key configured → mock analysis
        logger.info("ANTHROPIC_API_KEY unset — returning mock analysis")
        return _mock_analysis(site_url, issues, scores)

    # TODO: implement real Claude API call when ANTHROPIC_API_KEY is set
    # from anthropic import AsyncAnthropic
    # client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    # system = seo_strategy_context  # contents of SEO_STRATEGY_CLAUDE_CODE.md
    # user = build_prompt(site_url, pages_data, issues, scores, gsc_data)
    # resp = await client.messages.create(model=CLAUDE_MODEL, system=system,
    #     max_tokens=2000, messages=[{"role": "user", "content": user}])
    # return json.loads(resp.content[0].text)  # schema per Section 13
    raise NotImplementedError(
        "[PLACEHOLDER] Real Claude analysis is not implemented yet. "
        "Unset ANTHROPIC_API_KEY to use mock analysis."
    )


def _mock_analysis(site_url: str, issues: list[dict], scores: dict) -> dict:
    """Mock AI analysis — identical shape to the real Claude response."""
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")

    return {
        "summary": (
            f"Audit complete for {site_url}. Overall SEO health score is "
            f"{scores.get('overall', 0)}/100. Found {critical_count} critical "
            f"issues requiring immediate attention and {warning_count} "
            f"warnings. [MOCK: Connect ANTHROPIC_API_KEY for AI-generated "
            f"insights.]"
        ),
        "quick_wins": [
            {
                "title": "Add missing title tags",
                "effort": "low",
                "impact": "high",
                "description": "Several pages are missing title tags. This is a 5-minute fix per page.",
            },
            {
                "title": "Fix images missing alt text",
                "effort": "low",
                "impact": "medium",
                "description": "Add descriptive alt text to all images. Can be scripted.",
            },
            {
                "title": "Add JSON-LD structured data",
                "effort": "medium",
                "impact": "high",
                "description": "Add schema markup to enable rich results in Google.",
            },
        ],
        "content_assessment": "[MOCK] Connect ANTHROPIC_API_KEY for content quality assessment.",
        "priority_actions": [
            "Fix all critical technical issues first",
            "Add structured data to all pages",
            "Expand thin content pages to 600+ words",
        ],
        "positive_signals": [
            "HTTPS configured",
            "Mobile-responsive layout detected",
        ],
        "data_source": "mock",
    }
