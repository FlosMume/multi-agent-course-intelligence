"""Comparable tracing and rubric records."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, model_validator

from course_intelligence.models.base import StrictModel


class TraceStep(StrictModel):
    """One observable unit of a future orchestration run."""

    sequence: int = Field(ge=1)
    actor: str = Field(min_length=1)
    action: str = Field(min_length=1)
    status: Literal["started", "completed", "failed", "denied"]
    duration_ms: float | None = Field(default=None, ge=0)
    detail: str = ""


class RunTrace(StrictModel):
    """Execution evidence used to compare reliability and efficiency."""

    trace_id: str = Field(min_length=1)
    framework: Literal["native", "langchain", "langgraph", "crewai", "autogen"]
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    steps: list[TraceStep] = Field(default_factory=list)
    model_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    estimated_input_tokens: int | None = Field(default=None, ge=0)
    estimated_output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class RubricScore(StrictModel):
    """A zero-to-five score paired with its fixed percentage weight."""

    dimension: str = Field(min_length=1)
    score: float = Field(ge=0, le=5)
    weight_percent: float = Field(gt=0, le=100)
    rationale: str = Field(min_length=1)


class EvaluationResult(StrictModel):
    """Validated result that calculates, rather than invents, its total."""

    trace_id: str = Field(min_length=1)
    benchmark_case_id: str = Field(min_length=1)
    rubric_scores: list[RubricScore] = Field(min_length=1)
    weighted_total_percent: float | None = Field(default=None, ge=0, le=100)
    automated_failures: list[str] = Field(default_factory=list)
    reviewer_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def calculate_weighted_total(self) -> "EvaluationResult":
        """Ensure the reported total always matches its component scores."""

        weight_total = sum(item.weight_percent for item in self.rubric_scores)
        if abs(weight_total - 100) > 0.001:
            raise ValueError("Rubric weights must total 100 percent")
        self.weighted_total_percent = sum(
            (item.score / 5) * item.weight_percent for item in self.rubric_scores
        )
        return self
