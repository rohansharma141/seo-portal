"""SEO scoring logic — Section 5.3. Pure Python, no external dependencies.

Overall score is a weighted average of five category scores. Each issue
deducts from its category: critical -15, warning -5, info -1. Category and
overall scores are clamped to [0, 100].
"""

CATEGORIES = ["technical", "content", "eeeat", "performance", "structure"]

WEIGHTS = {
    "technical": 0.30,
    "content": 0.25,
    "eeeat": 0.20,
    "performance": 0.15,
    "structure": 0.10,
}

DEDUCTIONS = {"critical": 15, "warning": 5, "info": 1}


def calculate_score(issues: list[dict]) -> dict:
    """Given issue dicts (each with ``category`` and ``severity``), compute
    per-category scores and the weighted overall score.

    Returns: ``{"overall", "technical", "content", "eeeat",
    "performance", "structure"}`` — all ints 0–100.
    """
    scores = {}
    for cat in CATEGORIES:
        cat_issues = [i for i in issues if i.get("category") == cat]
        deduct = sum(DEDUCTIONS.get(i.get("severity"), 0) for i in cat_issues)
        scores[cat] = max(0, 100 - deduct)

    overall = sum(scores[cat] * WEIGHTS[cat] for cat in CATEGORIES)
    return {
        "overall": round(overall),
        "technical": scores["technical"],
        "content": scores["content"],
        "eeeat": scores["eeeat"],
        "performance": scores["performance"],
        "structure": scores["structure"],
    }


def count_by_severity(issues: list[dict]) -> dict:
    """Count issues by severity — feeds ``audits.issues_{critical,warning,info}``
    (Section 4.2)."""
    counts = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        sev = issue.get("severity")
        if sev in counts:
            counts[sev] += 1
    return counts
