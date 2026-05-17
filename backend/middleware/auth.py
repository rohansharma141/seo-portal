"""Authentication — Section 14.

Two bearer credentials are accepted on `Authorization: Bearer <token>`:

* **API token** (starts with ``settings.api_token_prefix``, e.g. ``pse_``):
  looked up by its 8-char prefix, bcrypt-verified, checked for active/expiry,
  scoped per the token row. ``last_used_at`` is updated on use.
* **JWT** (anything else): HS256, verified with ``settings.jwt_secret``.
  Portal/admin sessions; granted the wildcard scope ``*``.

Tokens are never stored in plaintext (bcrypt only) and shown once on create.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from services.repository import Repository, get_repository

# ── Token crypto ────────────────────────────────────────────────────────


def generate_api_token() -> tuple[str, str]:
    """Return (raw_token, token_prefix). Raw is shown once; prefix is stored
    for display (Section 4.4, VARCHAR(10) — first 8 chars)."""
    raw = f"{settings.api_token_prefix}{secrets.token_urlsafe(32)}"
    return raw, raw[:8]


def hash_token(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_token(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    scopes: Optional[list[str]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload = {"sub": subject, "scopes": scopes or ["*"], "exp": exp}
    return jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )


# ── Principal + dependencies ────────────────────────────────────────────


@dataclass
class Principal:
    kind: str  # "jwt" | "api_token"
    subject: str
    scopes: set[str] = field(default_factory=set)
    token_id: Optional[UUID] = None

    def has_scope(self, scope: str) -> bool:
        return "*" in self.scopes or scope in self.scopes


_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _is_expired(expires_at: Optional[datetime]) -> bool:
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


async def get_principal(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    repo: Repository = Depends(get_repository),
) -> Principal:
    if creds is None or not creds.credentials:
        raise _UNAUTHORIZED
    token = creds.credentials

    if token.startswith(settings.api_token_prefix):
        prefix = token[:8]
        candidates = await repo.get_tokens_by_prefix(prefix)
        for row in candidates:
            if not row["is_active"]:
                continue
            if _is_expired(row.get("expires_at")):
                continue
            if verify_token(token, row["token_hash"]):
                await repo.touch_token_used(
                    row["id"], datetime.now(timezone.utc)
                )
                return Principal(
                    kind="api_token",
                    subject=str(row["id"]),
                    scopes=set(row.get("scopes") or []),
                    token_id=row["id"],
                )
        raise _UNAUTHORIZED

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _UNAUTHORIZED
    return Principal(
        kind="jwt",
        subject=str(payload.get("sub", "")),
        scopes=set(payload.get("scopes", ["*"])),
    )


def require_scopes(*needed: str):
    """Dependency factory enforcing that the principal holds every scope."""

    async def _dep(
        principal: Principal = Depends(get_principal),
    ) -> Principal:
        for scope in needed:
            if not principal.has_scope(scope):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}",
                )
        return principal

    return _dep
