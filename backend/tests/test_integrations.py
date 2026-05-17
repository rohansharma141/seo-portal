"""Step 4 verification — mock integrations (Section 6) and their flow through
the rules engine + scorer (Section 5)."""

import pytest

from config import settings
from services.analyser import analyse_audit
from services.crawler import PAGE_DATA_SCHEMA, crawl_site
from services.gsc import get_gsc_performance
from services.scorer import calculate_score, count_by_severity
from utils.seo_rules import evaluate_pages

SITE = "https://kedar.estate"


async def test_mock_crawl_shape_and_max_pages():
    pages = await crawl_site(SITE)
    assert len(pages) == 3
    for page in pages:
        assert set(page) >= set(PAGE_DATA_SCHEMA), set(PAGE_DATA_SCHEMA) - set(page)
    # max_pages caps the result; always at least one page.
    assert len(await crawl_site(SITE, max_pages=1)) == 1
    assert len(await crawl_site(SITE, max_pages=2)) == 2


async def test_homepage_reference_values_are_stable():
    home = (await crawl_site(SITE))[0]
    assert home["url"] == SITE
    assert home["title"] == "Mock Homepage Title — Kedar Estate"
    assert home["lcp_ms"] == 2800
    assert home["structured_data"] is None
    assert home["is_homepage"] is True


async def test_mock_data_flows_through_scorer():
    pages = await crawl_site(SITE)
    issues = evaluate_pages(pages)
    scores = calculate_score(issues)
    counts = count_by_severity(issues)

    assert len(issues) == 10
    assert counts == {"critical": 1, "warning": 6, "info": 3}
    assert sum(counts.values()) == len(issues)
    assert scores == {
        "overall": 87,
        "technical": 65,
        "content": 93,
        "eeeat": 100,
        "performance": 94,
        "structure": 100,
    }
    for key, val in scores.items():
        assert 0 <= val <= 100, key

    rule_ids = {i["rule_id"] for i in issues}
    assert "missing_structured_data" in rule_ids  # homepage
    assert "broken_internal_links" in rule_ids  # project (critical)


async def test_gsc_mock_shape():
    data = await get_gsc_performance(SITE)
    assert data["data_source"] == "mock"
    for key in (
        "total_clicks_90d",
        "total_impressions_90d",
        "avg_ctr",
        "avg_position",
        "top_queries",
        "top_pages",
        "low_ctr_pages",
        "quick_wins",
        "indexing_errors",
        "indexed_pages",
    ):
        assert key in data


async def test_analyser_mock_shape():
    pages = await crawl_site(SITE)
    issues = evaluate_pages(pages)
    scores = calculate_score(issues)
    result = await analyse_audit(SITE, pages, issues, scores, {})

    assert set(result) >= {
        "summary",
        "quick_wins",
        "content_assessment",
        "priority_actions",
        "positive_signals",
        "data_source",
    }
    assert result["data_source"] == "mock"
    assert SITE in result["summary"]
    assert str(scores["overall"]) in result["summary"]
    assert len(result["quick_wins"]) == 3
    for win in result["quick_wins"]:
        assert set(win) == {"title", "effort", "impact", "description"}
    assert isinstance(result["priority_actions"], list)
    assert isinstance(result["positive_signals"], list)


@pytest.mark.parametrize(
    "attr,call",
    [
        ("firecrawl_api_key", lambda: crawl_site(SITE)),
        ("gsc_credentials_path", lambda: get_gsc_performance(SITE)),
        ("anthropic_api_key", lambda: analyse_audit(SITE, [], [], {}, {})),
    ],
)
async def test_real_path_is_a_placeholder_when_configured(monkeypatch, attr, call):
    # Configuring a key must switch off mock mode and hit the
    # not-yet-implemented real path (clean NotImplementedError, not a crash).
    monkeypatch.setattr(settings, attr, "configured-value")
    with pytest.raises(NotImplementedError, match=r"\[PLACEHOLDER\]"):
        await call()
