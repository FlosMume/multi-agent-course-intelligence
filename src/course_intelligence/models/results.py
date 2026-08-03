"""Structured review findings returned by quality checks."""

from enum import StrEnum

from pydantic import Field

from course_intelligence.models.base import StrictModel


class FindingSeverity(StrEnum):
    """Severity levels ordered conceptually from information to blocker."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ReviewFinding(StrictModel):
    """One review observation with an actionable recommendation."""

    finding_id: str = Field(min_length=1)
    severity: FindingSeverity
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)
