"""Job models for job apply plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class JobStatus(StrEnum):
    """Status of job in pipeline."""

    DISCOVERED = "discovered"
    EXTRACTED = "extracted"
    MATCHING = "matching"
    MATCHED = "matched"
    REJECTED = "rejected"
    QUEUED = "queued"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobSource(StrEnum):
    """Source platform for job posting."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY_SITE = "company_site"
    OTHER = "other"


class SalaryInfo(BaseModel):
    """Salary information."""

    min_amount: int | None = None
    max_amount: int | None = None
    currency: str = "USD"
    period: str = "yearly"

    def __str__(self) -> str:
        """Return human-readable salary string."""
        if self.min_amount and self.max_amount:
            return f"{self.currency} {self.min_amount:,}-{self.max_amount:,}/{self.period}"
        if self.min_amount:
            return f"{self.currency} {self.min_amount:,}+/{self.period}"
        return "Not specified"


class Job(BaseModel):
    """Job posting information."""

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    external_id: str | None = None
    url: str
    title: str
    company: str
    location: str | None = None
    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    job_type: str | None = None
    experience_level: str | None = None
    industry: str | None = None
    salary: SalaryInfo | None = None
    source: JobSource = JobSource.OTHER
    posted_date: datetime | None = None
    application_deadline: datetime | None = None
    status: JobStatus = JobStatus.DISCOVERED
    match_score: float | None = None
    match_reasons: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    applied_at: datetime | None = None
    application_method: str | None = None
    confirmation_received: bool = False
    discovered_at: datetime = Field(default_factory=_utc_now)
    last_updated: datetime = Field(default_factory=_utc_now)
    raw_data: dict[str, Any] = Field(default_factory=dict)

    def mark_applied(self, method: str = "auto") -> None:
        """Mark job as applied with given method."""
        self.status = JobStatus.APPLIED
        self.applied_at = _utc_now()
        self.application_method = method
        self.last_updated = _utc_now()

    def mark_failed(self, reason: str) -> None:
        """Mark job application as failed."""
        self.status = JobStatus.FAILED
        self.rejection_reasons.append(reason)
        self.last_updated = _utc_now()

    def update_match(self, score: float, reasons: list[str], min_score: float = 70) -> None:
        """Update match score and status."""
        self.match_score = score
        self.match_reasons = reasons
        self.status = JobStatus.MATCHED if score >= min_score else JobStatus.REJECTED
        self.last_updated = _utc_now()


class ApplicationResult(BaseModel):
    """Result of job application attempt."""

    job_id: str
    success: bool
    method: str
    confirmation_number: str | None = None
    error: str | None = None
    screenshot_ref: str | None = None
    timestamp: datetime = Field(default_factory=_utc_now)
