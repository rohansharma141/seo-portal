"""/api/v1/audits endpoints — Section 7.3."""

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)

from middleware.auth import require_scopes
from schemas.audit import (
    AuditCreate,
    AuditCreatedOut,
    AuditIssuesOut,
    AuditListOut,
    AuditOut,
    AuditStatusOut,
)
from services.audit_pipeline import run_audit
from services.repository import Repository, get_repository

router = APIRouter(prefix="/audits", tags=["audits"])

ESTIMATED_SECONDS = 120


@router.get(
    "",
    response_model=AuditListOut,
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def list_audits(
    site_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repo: Repository = Depends(get_repository),
):
    items, total = await repo.list_audits(site_id, limit, offset)
    return {
        "audits": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "",
    response_model=AuditCreatedOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_scopes("audit:write"))],
)
async def trigger_audit(
    payload: AuditCreate,
    background_tasks: BackgroundTasks,
    repo: Repository = Depends(get_repository),
):
    site = await repo.get_site(payload.site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    audit_id = await repo.create_audit(payload.site_id, payload.triggered_by)
    # run_audit opens its own sessions per call, so it is safe to run after
    # the response is sent (Section 11, Step 5).
    background_tasks.add_task(run_audit, audit_id, repo)
    return {
        "audit_id": audit_id,
        "status": "pending",
        "site_id": payload.site_id,
        "message": (
            f"Audit queued. Poll /api/v1/audits/{audit_id}/status for progress."
        ),
        "estimated_seconds": ESTIMATED_SECONDS,
    }


@router.get(
    "/{audit_id}",
    response_model=AuditOut,
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def get_audit(
    audit_id: UUID, repo: Repository = Depends(get_repository)
):
    audit = await repo.get_audit_out(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.get(
    "/{audit_id}/issues",
    response_model=AuditIssuesOut,
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def get_audit_issues(
    audit_id: UUID,
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    repo: Repository = Depends(get_repository),
):
    result = await repo.get_issues(audit_id, severity, category)
    if result is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    issues, total = result
    return {
        "issues": issues,
        "total": total,
        "filters": {"severity": severity, "category": category},
    }


@router.get(
    "/{audit_id}/status",
    response_model=AuditStatusOut,
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def get_audit_status(
    audit_id: UUID, repo: Repository = Depends(get_repository)
):
    st = await repo.get_audit_status(audit_id)
    if st is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    return st
