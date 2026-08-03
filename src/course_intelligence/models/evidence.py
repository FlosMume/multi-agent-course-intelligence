"""Evidence contracts that keep sourced claims separate from proposals."""

from typing import Literal

from pydantic import Field

from course_intelligence.models.base import StrictModel


class SourceDocument(StrictModel):
    """Safe metadata for an approved input document."""

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: Literal["public", "synthetic", "private_approved"]
    content_reference: str = Field(min_length=1)
    license_note: str = ""


class EvidenceItem(StrictModel):
    """A claim-to-source link suitable for automated resolution checks."""

    evidence_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    location: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
