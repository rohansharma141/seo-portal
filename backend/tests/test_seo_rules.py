"""Tests for utils/seo_rules.py — Section 5.2."""

import pytest

from services.scorer import calculate_score
from utils.seo_rules import (
    ALL_RULES,
    RULES_BY_CATEGORY,
    evaluate_page,
    evaluate_pages,
)

VALID_SEVERITIES = {"critical", "warning", "info"}


# A page crafted to violate no rule at all.
CLEAN_PAGE = {
    "url": "https://kedar.estate/projects/godrej-samaris-sector-53",
    "title": "Godrej Samaris Sector 53 Gurgaon Review | Kedar Estate",
    "meta_description": (
        "First-hand review of Godrej Samaris in Sector 53 Gurgaon: 3BHK "
        "pricing, site-visit notes, and honest pros and cons."
    ),
    "h1": ["Godrej Samaris Sector 53 Gurgaon — Honest Review"],
    "images": [
        {
            "src": "https://kedar.estate/img/lobby.webp",
            "alt": "Marble entrance lobby of Godrej Samaris",
            "width": 800,
            "height": 600,
        }
    ],
    "canonical": "https://kedar.estate/projects/godrej-samaris-sector-53",
    "noindex": False,
    "structured_data": {"@type": "Product"},
    "broken_links": [],
    "word_count": 820,
    "has_author_byline": True,
    "title_duplicate": False,
    "meta_duplicate": False,
    "page_type": "project",
    "publish_date": "2026-05-16",
    "has_contact_info": True,
    "is_homepage": False,
    "lcp_ms": 1900,
    "cls_score": 0.03,
    "internal_links": [
        "https://kedar.estate/projects",
        "https://kedar.estate/blog/golf-course-road",
    ],
    "heading_hierarchy_broken": False,
}


def test_all_rules_are_well_formed():
    seen_ids = set()
    for category, rules in RULES_BY_CATEGORY.items():
        assert rules, f"{category} has no rules"
        for rule in rules:
            assert set(rule) >= {
                "id",
                "name",
                "severity",
                "category",
                "check",
                "description",
                "fix",
            }
            assert rule["severity"] in VALID_SEVERITIES
            assert rule["category"] == category
            assert callable(rule["check"])
            assert rule["id"] not in seen_ids, f"duplicate id {rule['id']}"
            seen_ids.add(rule["id"])
    assert len(ALL_RULES) == len(seen_ids)


def test_clean_page_has_zero_issues():
    assert evaluate_page(CLEAN_PAGE) == []
    # Meta description must stay within the 160-char limit for the page to be clean.
    assert len(CLEAN_PAGE["meta_description"]) <= 160


def test_empty_page_triggers_expected_rules():
    issues = evaluate_page({})
    ids = {i["rule_id"] for i in issues}
    assert ids == {
        "missing_title_tag",
        "missing_meta_description",
        "missing_h1",
        "no_canonical_tag",
        "missing_structured_data",
        "thin_content",
        "commodity_content_risk",
        "no_internal_links",
    }
    # Issue shape matches the audit_issues table (Section 4.3).
    sample = issues[0]
    assert set(sample) == {
        "page_url",
        "category",
        "severity",
        "rule_id",
        "rule_name",
        "description",
        "fix_suggestion",
        "affected_value",
        "expected_value",
    }


def test_empty_page_scores():
    s = calculate_score(evaluate_page({}))
    # technical: 15+5+15+5+5 = 45 -> 55 ; content: 5+1 = 6 -> 94 ; structure: 5 -> 95
    assert s == {
        "overall": 84,  # 16.5+23.5+20+15+9.5 = 84.5 -> 84 (round-half-to-even)
        "technical": 55,
        "content": 94,
        "eeeat": 100,
        "performance": 100,
        "structure": 95,
    }


@pytest.mark.parametrize(
    "page,expected_id",
    [
        ({"title": "x" * 65, "url": "https://a.com"}, "title_too_long"),
        ({"title": "short", "url": "https://a.com"}, "title_too_short"),
        ({"url": "https://a.com", "lcp_ms": 5000}, "lcp_poor"),
        ({"url": "https://a.com", "lcp_ms": 3000}, "lcp_needs_improvement"),
        ({"url": "https://a.com", "cls_score": 0.4}, "cls_poor"),
        ({"url": "https://a.com/p?id=12"}, "non_descriptive_url"),
        ({"url": "https://a.com/path/9999999"}, "non_descriptive_url"),
        ({"url": "https://a.com/Camellias"}, "url_uppercase"),
        ({"url": "http://a.com"}, "http_not_https"),
        ({"url": "https://a.com", "noindex": True}, "noindex_detected"),
        (
            {"url": "https://a.com", "h1": ["one", "two"]},
            "multiple_h1",
        ),
        (
            {
                "url": "https://a.com",
                "images": [{"src": "/x.jpg", "alt": "", "width": 0, "height": 0}],
            },
            "images_missing_alt",
        ),
    ],
)
def test_targeted_rule_triggers(page, expected_id):
    ids = {i["rule_id"] for i in evaluate_page(page)}
    assert expected_id in ids


def test_lcp_poor_and_needs_improvement_are_mutually_exclusive():
    poor = {i["rule_id"] for i in evaluate_page({"url": "https://a.com", "lcp_ms": 5000})}
    assert "lcp_poor" in poor and "lcp_needs_improvement" not in poor


def test_rule_check_exception_is_swallowed():
    # word_count is a str -> the thin_content comparison would raise; the
    # engine must skip that rule, not crash the audit.
    issues = evaluate_page({"url": "https://a.com", "word_count": "lots"})
    assert isinstance(issues, list)


def test_evaluate_pages_aggregates():
    pages = [{}, {"url": "https://a.com", "title": "y" * 65}]
    issues = evaluate_pages(pages)
    assert len(issues) == len(evaluate_page(pages[0])) + len(
        evaluate_page(pages[1])
    )
    assert {i["page_url"] for i in issues} == {None, "https://a.com"}
