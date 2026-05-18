"""Cross-site comparison — Addendum v1.1 Feature 1.

Adapted from the addendum's sample (which used a raw AsyncSession) to the
project's repository abstraction so it stays testable with a fake repo.
Validation follows the addendum's **Rules** (400 / 404 / 422), not its
sample router (which collapsed everything to 422).
"""

from datetime import datetime, timezone

CATEGORIES = ["technical", "content", "eeeat", "performance", "structure"]


class CompareError(Exception):
    """Raised on validation failure; carries the HTTP status to return."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _ov(site: dict) -> int:
    return site["scores"].get("overall") or 0


async def get_comparison(site_ids: list[str], repo) -> dict:
    """Compare the latest completed audit across 2–5 sites."""
    if len(site_ids) < 2:
        raise CompareError(400, "At least 2 site_ids required")
    if len(site_ids) > 5:
        raise CompareError(400, "Maximum 5 site_ids allowed")

    results: list[dict] = []
    missing_audits: list[str] = []

    for site_id in site_ids:
        site = await repo.get_site_basic(site_id)
        if site is None:
            raise CompareError(404, f"Site not found: {site_id}")

        audit = await repo.latest_complete_audit_summary(site_id)
        if audit is None:
            missing_audits.append(site["name"])
            continue

        results.append(
            {
                "site_id": str(site["id"]),
                "site_name": site["name"],
                "domain": site["domain"],
                "site_type": site["site_type"],
                "audit_id": str(audit["audit_id"]),
                "audit_date": audit["audit_date"],
                "scores": audit["scores"],
                "issues": audit["issues"],
                "pages_crawled": audit["pages_crawled"],
            }
        )

    if missing_audits:
        raise CompareError(
            422,
            f"No completed audits found for: {', '.join(missing_audits)}. "
            f"Trigger an audit for these sites first.",
        )

    # Rank by overall score (desc)
    results.sort(key=_ov, reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    leader = results[0]

    # Per-category leader
    category_leaders = {
        cat: max(results, key=lambda x: x["scores"].get(cat) or 0)["site_id"]
        for cat in CATEGORIES
    }

    # Worst category gaps vs each category leader (only > 10 pts)
    gaps: list[dict] = []
    for site_data in results:
        for cat in CATEGORIES:
            leader_id = category_leaders[cat]
            if site_data["site_id"] == leader_id:
                continue
            leader_data = next(
                r for r in results if r["site_id"] == leader_id
            )
            gap = (leader_data["scores"].get(cat) or 0) - (
                site_data["scores"].get(cat) or 0
            )
            if gap > 10:
                gaps.append(
                    {
                        "category": cat,
                        "site_id": site_data["site_id"],
                        "site_name": site_data["site_name"],
                        "score": site_data["scores"].get(cat) or 0,
                        "leader_score": leader_data["scores"].get(cat) or 0,
                        "gap": gap,
                        "note": None,
                    }
                )

    gaps.sort(key=lambda x: x["gap"], reverse=True)
    if gaps:
        gaps[0]["note"] = "Largest gap — highest priority to close"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sites": results,
        "leader": {
            "site_id": leader["site_id"],
            "site_name": leader["site_name"],
            "overall_score": _ov(leader),
        },
        "category_leaders": category_leaders,
        "gaps": gaps,
    }
