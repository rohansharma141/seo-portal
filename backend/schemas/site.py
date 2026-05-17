"""Pydantic schemas for Site — Section 7.2."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

SiteType = Literal["brokerage", "saas", "broker_landing", "other"]
Schedule = Literal["weekly", "monthly", "manual"]


class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=500)
    site_type: SiteType = "other"
    schedule: Schedule = "weekly"
    max_pages: int = Field(default=100, ge=1, le=1000)


class SiteUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=500)
    site_type: Optional[SiteType] = None
    schedule: Optional[Schedule] = None
    max_pages: Optional[int] = Field(default=None, ge=1, le=1000)
    is_active: Optional[bool] = None


class SiteOut(BaseModel):
    id: UUID
    name: str
    domain: str
    url: str
    site_type: str
    schedule: str
    is_active: bool
    last_audit_at: Optional[datetime] = None
    last_score: Optional[int] = None
    created_at: datetime


class SiteListOut(BaseModel):
    sites: list[SiteOut]
    total: int


class LastAuditSummary(BaseModel):
    audit_id: UUID
    status: str
    score_overall: Optional[int] = None
    completed_at: Optional[datetime] = None


class SiteDetailOut(SiteOut):
    last_audit: Optional[LastAuditSummary] = None
