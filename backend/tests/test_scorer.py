"""Tests for services/scorer.py — Section 5.3."""

from services.scorer import (
    CATEGORIES,
    DEDUCTIONS,
    WEIGHTS,
    calculate_score,
    count_by_severity,
)


def test_no_issues_is_perfect():
    s = calculate_score([])
    assert s == {
        "overall": 100,
        "technical": 100,
        "content": 100,
        "eeeat": 100,
        "performance": 100,
        "structure": 100,
    }


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0
    assert set(WEIGHTS) == set(CATEGORIES)


def test_single_critical_technical():
    s = calculate_score([{"category": "technical", "severity": "critical"}])
    assert s["technical"] == 85  # 100 - 15
    assert s["content"] == 100
    # overall = 85*.30 + 100*(.25+.20+.15+.10) = 25.5 + 70 = 95.5 -> 96 (round-half-to-even)
    assert s["overall"] == 96


def test_deduction_values_match_spec():
    assert DEDUCTIONS == {"critical": 15, "warning": 5, "info": 1}


def test_category_floors_at_zero():
    issues = [{"category": "performance", "severity": "critical"}] * 10  # -150
    s = calculate_score(issues)
    assert s["performance"] == 0  # clamped, never negative
    # overall = 0*.15 + 100*.85 = 85
    assert s["overall"] == 85


def test_mixed_severities_per_category():
    issues = [
        {"category": "content", "severity": "critical"},  # -15
        {"category": "content", "severity": "warning"},  # -5
        {"category": "content", "severity": "info"},  # -1
        {"category": "structure", "severity": "warning"},  # -5
    ]
    s = calculate_score(issues)
    assert s["content"] == 79  # 100 - 21
    assert s["structure"] == 95
    expected = (
        100 * WEIGHTS["technical"]
        + 79 * WEIGHTS["content"]
        + 100 * WEIGHTS["eeeat"]
        + 100 * WEIGHTS["performance"]
        + 95 * WEIGHTS["structure"]
    )
    assert s["overall"] == round(expected)


def test_unknown_severity_or_category_is_ignored():
    s = calculate_score(
        [
            {"category": "technical", "severity": "bogus"},  # 0 deduction
            {"category": "nonsense", "severity": "critical"},  # no category
        ]
    )
    assert s["overall"] == 100


def test_count_by_severity():
    issues = [
        {"severity": "critical"},
        {"severity": "critical"},
        {"severity": "warning"},
        {"severity": "info"},
        {"severity": "info"},
        {"severity": "info"},
        {"severity": "weird"},  # ignored
    ]
    assert count_by_severity(issues) == {"critical": 2, "warning": 1, "info": 3}
    assert count_by_severity([]) == {"critical": 0, "warning": 0, "info": 0}
