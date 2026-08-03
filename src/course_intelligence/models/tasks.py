"""Shared task, role, and message contracts."""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import Field

from course_intelligence.models.base import StrictModel
from course_intelligence.models.course import CourseProfile
from course_intelligence.models.evidence import SourceDocument


class TaskType(StrEnum):
    """Baseline capabilities that every framework variant must support."""

    ANALYZE_REQUIREMENTS = "analyze_requirements"
    DESIGN_COURSE = "design_course"
    ALIGN_ASSESSMENTS = "align_assessments"
    REVIEW_QUALITY = "review_quality"


class CourseIntelligenceTask(StrictModel):
    """The identical validated work request given to each orchestrator."""

    task_id: str = Field(min_length=1)
    task_type: TaskType
    course: CourseProfile
    sources: list[SourceDocument] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(min_length=1)
    prohibited_actions: list[str] = Field(default_factory=list)


class AgentRole(StrictModel):
    """A responsibility boundary independent of framework terminology."""

    role_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    responsibility: str = Field(min_length=1)
    permitted_tools: list[str] = Field(default_factory=list)


class AgentMessage(StrictModel):
    """A traceable message exchanged during future orchestration."""

    message_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    sender_role_id: str = Field(min_length=1)
    recipient_role_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
