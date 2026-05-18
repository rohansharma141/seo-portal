"""/api/v1/reports endpoints — Section 7.4."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.auth import require_scopes
from schemas.report import (
    CompareOut,
    CrossCompareOut,
    SiteHistoryOut,
    SummaryOut,
)
from services.compare_service import CompareError, get_comparison
from services.repository import Repository, get_repository

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/summary",
    response_model=SummaryOut,
    dependencies=[Depends(require_scopes("site:read"))],
)
async def summary(repo: Repository = Depends(get_repository)):
    return await repo.summary()


@router.get(
    "/compare",
    response_model=CrossCompareOut,
    dependencies=[Depends(require_scopes("site:read"))],
)
async def compare_sites(
    site_ids: str = Query(
        ..., description="Comma-separated list of 2-5 site UUIDs"
    ),
    repo: Repository = Depends(get_repository),
):
    """Cross-site comparison (Addendum v1.1). `?site_ids=uuid1,uuid2,...`"""
    ids = [s.strip() for s in site_ids.split(",") if s.strip()]
    try:
        return await get_comparison(ids, repo)
    except CompareError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get(
    "/site/{site_id}/history",
    response_model=SiteHistoryOut,
    dependencies=[Depends(require_scopes("site:read"))],
)
async def site_history(
    site_id: UUID, repo: Repository = Depends(get_repository)
):
    data = await repo.site_history(site_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return data


@router.get(
    "/site/{site_id}/compare",
    response_model=CompareOut,
    dependencies=[Depends(require_scopes("site:read"))],
)
async def compare_audits(
    site_id: UUID,
    a: UUID,
    b: UUID,
    repo: Repository = Depends(get_repository),
):
    """Compare two audits side by side (`?a=<audit>&b=<audit>`)."""
    data = await repo.compare(a, b)
    if data is None:
        raise HTTPException(
            status_code=404, detail="One or both audits not found"
        )
    return data
