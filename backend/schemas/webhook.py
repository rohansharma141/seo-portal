"""Pydantic schemas for webhook subscriptions — Section 7.6.

The HMAC secret is write-only — accepted on create, never returned.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

DEFAULT_EVENTS = ["audit.complete", "audit.failed"]
VALID_EVENTS = {"audit.complete", "audit.failed"}


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=1000)
    events: list[str] = Field(default_factory=lambda: list(DEFAULT_EVENTS))
    secret: Optional[str] = Field(default=None, max_length=255)


class WebhookOut(BaseModel):
    id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: Optional[datetime] = None
    created_at: datetime


class WebhookListOut(BaseModel):
    webhooks: list[WebhookOut]
    total: int


class WebhookTestRequest(BaseModel):
    url: str = Field(min_length=1, max_length=1000)
    secret: Optional[str] = Field(default=None, max_length=255)


class WebhookTestResult(BaseModel):
    delivered: bool
    detail: str
