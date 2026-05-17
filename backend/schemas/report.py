"""Pydantic schemas for reports — Section 7.4.

Not in Section 3's schema list (which names site/audit/api_token only);
added because the reports router needs typed response shapes for /docs.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HistoryPoint(BaseModel):
    audit_id: UUID
    date: Optional[str] = None
    score: Optional[int] = None
    critical: int = 0
    warning: int = 0


class SiteHistoryOut(BaseModel):
    site_id: UUID
    site_name: str
    audits: list[HistoryPoint]
    trend: str


class CompareSide(BaseModel):
    audit_id: UUID
    date: Optional[str] = None
    scores: dict = Field(default_factory=dict)
    issues_critical: int = 0
    issues_warning: int = 0
    issues_info: int = 0


class CompareOut(BaseModel):
    site_id: Optional[UUID] = None
    a: CompareSide
    b: CompareSide
    score_delta: int


class SummarySite(BaseModel):
    name: str
    score: Optional[int] = None
    status: str
    last_audited: Optional[str] = None


class SummaryOut(BaseModel):
    sites_total: int
    sites_healthy: int
    sites_warning: int
    sites_critical: int
    avg_score_all_sites: int
    total_critical_issues: int
    total_warning_issues: int
    sites: list[SummarySite]
