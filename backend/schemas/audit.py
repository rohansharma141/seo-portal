"""Pydantic schemas for Audit — Section 7.3."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

TriggeredBy = Literal["manual", "scheduled", "api", "deploy_hook"]
Severity = Literal["critical", "warning", "info"]


class AuditCreate(BaseModel):
    site_id: UUID
    triggered_by: TriggeredBy = "manual"


class AuditCreatedOut(BaseModel):
    audit_id: UUID
    status: str
    site_id: UUID
    message: str
    estimated_seconds: int


class AuditScores(BaseModel):
    overall: Optional[int] = None
    technical: Optional[int] = None
    content: Optional[int] = None
    eeeat: Optional[int] = None
    performance: Optional[int] = None
    structure: Optional[int] = None


class IssueCounts(BaseModel):
    critical: int = 0
    warning: int = 0
    info: int = 0


class AuditAnalysis(BaseModel):
    summary: Optional[str] = None
    quick_wins: list = Field(default_factory=list)
    priority_actions: list = Field(default_factory=list)
    positive_signals: list = Field(default_factory=list)


class AuditOut(BaseModel):
    id: UUID
    site_id: UUID
    status: str
    scores: AuditScores
    pages_crawled: int = 0
    issues: IssueCounts
    analysis: AuditAnalysis
    gsc_snapshot: dict = Field(default_factory=dict)
    backlinks: dict = Field(default_factory=dict)  # Addendum v1.1
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AuditListItem(BaseModel):
    id: UUID
    site_id: UUID
    status: str
    score_overall: Optional[int] = None
    triggered_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class AuditListOut(BaseModel):
    audits: list[AuditListItem]
    total: int
    limit: int
    offset: int


class AuditStatusOut(BaseModel):
    audit_id: UUID
    status: str
    progress_message: str
    pages_crawled: int = 0
    started_at: Optional[datetime] = None


class AuditIssueOut(BaseModel):
    id: UUID
    page_url: Optional[str] = None
    category: str
    severity: str
    rule_id: str
    rule_name: str
    description: str
    fix_suggestion: str
    affected_value: Optional[str] = None
    expected_value: Optional[str] = None


class AuditIssuesFilters(BaseModel):
    severity: Optional[str] = None
    category: Optional[str] = None


class AuditIssuesOut(BaseModel):
    issues: list[AuditIssueOut]
    total: int
    filters: AuditIssuesFilters
