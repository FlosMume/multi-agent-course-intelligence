"""Course description and planning contracts."""

from typing import Literal

from pydantic import Field, model_validator

from course_intelligence.models.base import StrictModel


class LearningOutcome(StrictModel):
    """A measurable outcome that other records reference by identifier."""

    outcome_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    bloom_level: Literal[
        "remember", "understand", "apply", "analyze", "evaluate", "create"
    ]


class CourseProfile(StrictModel):
    """Validated teaching context supplied to every framework."""

    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    duration_weeks: int = Field(ge=1, le=52)
    delivery_mode: Literal["in_person", "online", "hybrid"]
    prerequisites: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    learning_outcomes: list[LearningOutcome] = Field(default_factory=list)


class AssessmentPlan(StrictModel):
    """An assessment and its explicit links to learning outcomes."""

    assessment_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    weight_percent: float = Field(ge=0, le=100)
    outcome_ids: list[str] = Field(min_length=1)
    description: str = Field(min_length=1)


class CourseModule(StrictModel):
    """One ordered instructional module in a proposed plan."""

    module_id: str = Field(min_length=1)
    week: int = Field(ge=1, le=52)
    title: str = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    outcome_ids: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)


class CoursePlan(StrictModel):
    """Common result contract returned by future orchestrators."""

    schema_version: Literal["1.0"] = "1.0"
    course: CourseProfile
    modules: list[CourseModule] = Field(min_length=1)
    assessments: list[AssessmentPlan] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True

    @model_validator(mode="after")
    def references_known_outcomes(self) -> "CoursePlan":
        """Catch invented outcome identifiers at the domain boundary."""

        known = {item.outcome_id for item in self.course.learning_outcomes}
        referenced = {
            outcome_id for module in self.modules for outcome_id in module.outcome_ids
        }
        referenced.update(
            outcome_id
            for assessment in self.assessments
            for outcome_id in assessment.outcome_ids
        )
        unknown = referenced - known
        if unknown:
            raise ValueError(f"Unknown learning-outcome identifiers: {sorted(unknown)}")
        return self
