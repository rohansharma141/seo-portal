"""Pydantic schemas for API tokens — Section 7.5.

The raw token is returned exactly once (TokenCreatedOut); every other
response exposes only the prefix (Section 14).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

DEFAULT_SCOPES = ["audit:read", "audit:write", "site:read"]
VALID_SCOPES = {
    "audit:read",
    "audit:write",
    "site:read",
    "site:write",
    "webhook:read",
    "webhook:write",
}


class TokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: list(DEFAULT_SCOPES))
    expires_at: Optional[datetime] = None


class TokenCreatedOut(BaseModel):
    id: UUID
    name: str
    token: str
    token_prefix: str
    scopes: list[str]
    warning: str = "Store this token securely. It will not be shown again."


class TokenOut(BaseModel):
    id: UUID
    name: str
    token_prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class TokenListOut(BaseModel):
    tokens: list[TokenOut]
    total: int
