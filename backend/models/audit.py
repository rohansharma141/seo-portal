"""Audit + AuditIssue models — Sections 4.2 and 4.3."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.site import Site


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    # "pending" | "crawling" | "analysing" | "scoring" | "complete" | "failed"
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'pending'")
    )
    # "manual" | "scheduled" | "api" | "deploy_hook"
    triggered_by: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'manual'")
    )
    score_overall: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_technical: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_content: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_eeeat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_performance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_structure: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pages_crawled: Mapped[int] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    issues_critical: Mapped[int] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    issues_warning: Mapped[int] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    issues_info: Mapped[int] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    crawl_data: Mapped[list] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    gsc_data: Mapped[dict] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    quick_wins: Mapped[list] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    site: Mapped["Site"] = relationship(back_populates="audits")
    issues: Mapped[list["AuditIssue"]] = relationship(
        back_populates="audit",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Audit {self.id} status={self.status!r}>"


class AuditIssue(Base):
    __tablename__ = "audit_issues"
    __table_args__ = (
        Index("idx_audit_issues_audit_id", "audit_id"),
        Index("idx_audit_issues_severity", "severity"),
        Index("idx_audit_issues_category", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )  # NULL = site-wide issue
    # "technical" | "content" | "eeeat" | "performance" | "structure" | "schema"
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # "critical" | "warning" | "info"
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    fix_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    affected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    audit: Mapped["Audit"] = relationship(back_populates="issues")

    def __repr__(self) -> str:
        return f"<AuditIssue {self.rule_id!r} {self.severity!r}>"
