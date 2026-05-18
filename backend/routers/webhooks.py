"""/api/v1/webhooks endpoints — Section 7.6."""

from types import SimpleNamespace
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from middleware.auth import require_scopes
from schemas.webhook import (
    VALID_EVENTS,
    WebhookCreate,
    WebhookListOut,
    WebhookOut,
    WebhookTestRequest,
    WebhookTestResult,
)
from services.repository import Repository, get_repository
from services.webhook_dispatcher import deliver

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get(
    "",
    response_model=WebhookListOut,
    dependencies=[Depends(require_scopes("webhook:read"))],
)
async def list_webhooks(repo: Repository = Depends(get_repository)):
    hooks = await repo.list_webhooks()
    return {"webhooks": hooks, "total": len(hooks)}


@router.post(
    "",
    response_model=WebhookOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scopes("webhook:write"))],
)
async def create_webhook(
    payload: WebhookCreate, repo: Repository = Depends(get_repository)
):
    invalid = set(payload.events) - VALID_EVENTS
    if invalid:
        raise HTTPException(
            status_code=422, detail=f"Unknown events: {sorted(invalid)}"
        )
    return await repo.create_webhook(
        name=payload.name,
        url=payload.url,
        events=payload.events,
        secret=payload.secret,
    )


@router.post(
    "/test",
    response_model=WebhookTestResult,
    dependencies=[Depends(require_scopes("webhook:write"))],
)
async def test_webhook(payload: WebhookTestRequest):
    """Send a signed test payload to an arbitrary URL (Section 7.6)."""
    sub = SimpleNamespace(
        id="test", url=payload.url, secret=payload.secret
    )
    results = await deliver(
        [sub],
        "webhook.test",
        {"message": "Test payload from Building10X SEO Portal."},
    )
    delivered = bool(results and results[0][1])
    return {
        "delivered": delivered,
        "detail": (
            "Test payload delivered."
            if delivered
            else "Delivery failed — check the URL is reachable."
        ),
    }


@router.delete(
    "/{webhook_id}",
    dependencies=[Depends(require_scopes("webhook:write"))],
)
async def delete_webhook(
    webhook_id: UUID, repo: Repository = Depends(get_repository)
):
    ok = await repo.delete_webhook(webhook_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "deleted", "id": str(webhook_id)}
