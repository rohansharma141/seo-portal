"""/api/v1/tokens endpoints — Section 7.5.

Token management is admin-only: it requires a JWT principal (portal/Supabase
session), never an API token — issuing or revoking credentials via an API
token would be a privilege-escalation path.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from middleware.auth import Principal, generate_api_token, get_principal, hash_token
from schemas.api_token import (
    VALID_SCOPES,
    TokenCreate,
    TokenCreatedOut,
    TokenListOut,
)
from services.repository import Repository, get_repository

router = APIRouter(prefix="/tokens", tags=["tokens"])


async def require_admin(
    principal: Principal = Depends(get_principal),
) -> Principal:
    if principal.kind != "jwt":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token management requires an admin (portal) session.",
        )
    return principal


@router.get(
    "", response_model=TokenListOut, dependencies=[Depends(require_admin)]
)
async def list_tokens(repo: Repository = Depends(get_repository)):
    tokens = await repo.list_tokens()
    return {"tokens": tokens, "total": len(tokens)}


@router.post(
    "",
    response_model=TokenCreatedOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_token(
    payload: TokenCreate, repo: Repository = Depends(get_repository)
):
    invalid = set(payload.scopes) - VALID_SCOPES
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown scopes: {sorted(invalid)}",
        )
    raw, prefix = generate_api_token()
    created = await repo.create_token(
        name=payload.name,
        scopes=payload.scopes,
        expires_at=payload.expires_at,
        token_hash=hash_token(raw),
        token_prefix=prefix,
    )
    # The raw token is returned exactly once and never persisted.
    return {
        "id": created["id"],
        "name": created["name"],
        "token": raw,
        "token_prefix": prefix,
        "scopes": created["scopes"],
    }


@router.delete("/{token_id}", dependencies=[Depends(require_admin)])
async def revoke_token(
    token_id: UUID, repo: Repository = Depends(get_repository)
):
    ok = await repo.revoke_token(token_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"status": "revoked", "id": str(token_id)}
