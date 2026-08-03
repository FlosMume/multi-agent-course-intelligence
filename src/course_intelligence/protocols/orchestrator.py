"""Framework-neutral orchestration boundary."""

from typing import Protocol

from pydantic import Field

from course_intelligence.models.base import StrictModel
from course_intelligence.models.course import CoursePlan
from course_intelligence.models.evaluation import RunTrace
from course_intelligence.models.results import ReviewFinding
from course_intelligence.models.tasks import CourseIntelligenceTask


class OrchestrationResult(StrictModel):
    """Common envelope returned by every future implementation."""

    status: str
    course_plan: CoursePlan | None = None
    findings: list[ReviewFinding] = Field(default_factory=list)
    trace: RunTrace


class Orchestrator(Protocol):
    """Run the same domain task regardless of the framework underneath."""

    def run(self, task: CourseIntelligenceTask) -> OrchestrationResult:
        """Execute a bounded workflow and return validated evidence."""
        ...
