"""Offline contract tests for the Phase 0 domain foundation."""

import pytest
from pydantic import ValidationError

from course_intelligence.models import (
    CourseModule,
    CoursePlan,
    CourseProfile,
    EvaluationResult,
    LearningOutcome,
    RubricScore,
)


@pytest.fixture
def course_profile() -> CourseProfile:
    """Provide a small synthetic course with one measurable outcome."""

    return CourseProfile(
        course_id="SYN-101",
        title="Synthetic Agent Systems",
        audience="Adult learners with introductory Python",
        duration_weeks=6,
        delivery_mode="online",
        learning_outcomes=[
            LearningOutcome(
                outcome_id="LO1",
                statement="Compare orchestration strategies using evidence.",
                bloom_level="evaluate",
            )
        ],
    )


def test_course_plan_accepts_known_outcome(course_profile: CourseProfile) -> None:
    """Arrange valid references, act by constructing, and assert success."""

    plan = CoursePlan(
        course=course_profile,
        modules=[
            CourseModule(
                module_id="M1",
                week=1,
                title="Controlled comparison",
                topics=["Common contracts"],
                outcome_ids=["LO1"],
            )
        ],
    )

    assert plan.modules[0].outcome_ids == ["LO1"]
    assert plan.requires_human_approval is True


def test_course_plan_rejects_unknown_outcome(course_profile: CourseProfile) -> None:
    """An adapter may not silently invent an outcome identifier."""

    with pytest.raises(ValidationError, match="Unknown learning-outcome"):
        CoursePlan(
            course=course_profile,
            modules=[
                CourseModule(
                    module_id="M1",
                    week=1,
                    title="Invalid reference",
                    topics=["Validation"],
                    outcome_ids=["LO999"],
                )
            ],
        )


def test_evaluation_calculates_weighted_total() -> None:
    """The model derives a reproducible percentage from bounded scores."""

    result = EvaluationResult(
        trace_id="trace-1",
        benchmark_case_id="case-1",
        rubric_scores=[
            RubricScore(
                dimension="Correctness",
                score=4,
                weight_percent=60,
                rationale="Most requirements were met.",
            ),
            RubricScore(
                dimension="Security",
                score=5,
                weight_percent=40,
                rationale="All tested boundaries were preserved.",
            ),
        ],
    )

    assert result.weighted_total_percent == pytest.approx(88)
