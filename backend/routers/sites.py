"""/api/v1/sites endpoints — Section 7.2."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from middleware.auth import require_scopes
from schemas.site import (
    SiteCreate,
    SiteDetailOut,
    SiteListOut,
    SiteOut,
    SiteUpdate,
)
from services.repository import Repository, get_repository

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=SiteListOut, dependencies=[Depends(require_scopes("site:read"))])
async def list_sites(repo: Repository = Depends(get_repository)):
    sites = await repo.list_sites()
    return {"sites": sites, "total": len(sites)}


@router.post(
    "",
    response_model=SiteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scopes("site:write"))],
)
async def create_site(
    payload: SiteCreate, repo: Repository = Depends(get_repository)
):
    try:
        return await repo.create_site(payload.model_dump())
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A site with domain '{payload.domain}' already exists.",
        )


@router.get(
    "/{site_id}",
    response_model=SiteDetailOut,
    dependencies=[Depends(require_scopes("site:read"))],
)
async def get_site(
    site_id: UUID, repo: Repository = Depends(get_repository)
):
    site = await repo.get_site_detail(site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.patch(
    "/{site_id}",
    response_model=SiteDetailOut,
    dependencies=[Depends(require_scopes("site:write"))],
)
async def update_site(
    site_id: UUID,
    payload: SiteUpdate,
    repo: Repository = Depends(get_repository),
):
    fields = payload.model_dump(exclude_unset=True)
    site = await repo.update_site(site_id, fields)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.delete(
    "/{site_id}", dependencies=[Depends(require_scopes("site:write"))]
)
async def delete_site(
    site_id: UUID, repo: Repository = Depends(get_repository)
):
    """Soft delete — sets is_active=false (Section 7.2)."""
    ok = await repo.soft_delete_site(site_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"status": "deleted", "id": str(site_id)}
