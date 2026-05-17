"""/api/v1/reports endpoints — Section 7.4."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from middleware.auth import require_scopes
from schemas.report import CompareOut, SiteHistoryOut, SummaryOut
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
