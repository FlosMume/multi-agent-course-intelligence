"""Phase 1 contract tests for the native Python reference workflow."""

from course_intelligence import NativeWorkflow, SafeTool, repair_structured_output
from course_intelligence.models import (
    CourseIntelligenceTask,
    CoursePlan,
    CourseProfile,
    LearningOutcome,
    TaskType,
)
from course_intelligence.protocols import ModelResponse
from tests.fakes.fake_model_client import FakeModelClient


def test_repair_structured_output_recovers_json() -> None:
    """The repair helper should recover a valid JSON object from a fenced model answer."""

    payload = repair_structured_output(
        "```json\n{\n  \"schema_version\": \"1.0\",\n  \"course\": {\n    \"course_id\": \"CS-100\"\n  },\n  \"modules\": []\n}\n```"
    )

    assert payload["schema_version"] == "1.0"
    assert payload["course"]["course_id"] == "CS-100"


def test_native_workflow_role_pipeline_runs_with_fake_client() -> None:
    """The native workflow should exercise the six logical roles and the reviewer approval gate."""

    course = CourseProfile(
        course_id="CS-100",
        title="Introduction to Applied AI",
        audience="Technical learners",
        duration_weeks=6,
        delivery_mode="online",
        learning_outcomes=[
            LearningOutcome(
                outcome_id="LO1",
                statement="Explain safe orchestration patterns.",
                bloom_level="understand",
            )
        ],
    )
    task = CourseIntelligenceTask(
        task_id="case-1",
        task_type=TaskType.DESIGN_COURSE,
        course=course,
        acceptance_criteria=["Produce a plausible six-week course plan."],
    )
    plan_payload = {
        "schema_version": "1.0",
        "course": course.model_dump(),
        "modules": [
            {
                "module_id": "M1",
                "week": 1,
                "title": "Workflow foundations",
                "topics": ["Protocol design", "Safety rules"],
                "outcome_ids": ["LO1"],
            }
        ],
        "assessments": [],
        "assumptions": ["Single instructor context."],
        "requires_human_approval": True,
    }

    responses = [
        ModelResponse(content='{"status": "assigned", "next": "researcher"}'),
        ModelResponse(content='{"summary": "Need a safe, structured course plan."}'),
        ModelResponse(content='{"concepts": ["workflow safety"], "uncertainties": []}'),
        ModelResponse(content='{"learning_outcomes": ["LO1"], "sequence": ["module 1"]}'),
        ModelResponse(content=str(plan_payload).replace("'", '"')),
        ModelResponse(content='{"decision": "approve", "revision_note": "Approved."}'),
    ]

    client = FakeModelClient(responses)
    workflow = NativeWorkflow(
        model_client=client,
        tools=[SafeTool("echo", "Return a value.", lambda **kwargs: {"ok": True, **kwargs})],
    )

    result = workflow.run(task)

    assert result.status == "completed"
    assert isinstance(result.course_plan, CoursePlan)
    assert result.course_plan.course.course_id == "CS-100"
    assert len(result.trace.steps) >= 6
    assert result.trace.model_calls >= 6


def test_native_workflow_rejects_after_revision_limit() -> None:
    """The reviewer should enforce the configured revision limit without endless retries."""

    course = CourseProfile(
        course_id="CS-101",
        title="Course design basics",
        audience="Instructors",
        duration_weeks=4,
        delivery_mode="hybrid",
        learning_outcomes=[
            LearningOutcome(
                outcome_id="LO1",
                statement="Describe a bounded review loop.",
                bloom_level="analyze",
            )
        ],
    )
    task = CourseIntelligenceTask(
        task_id="case-reject",
        task_type=TaskType.REVIEW_QUALITY,
        course=course,
        acceptance_criteria=["Reject until corrected."],
    )

    responses = [
        ModelResponse(content='{"status": "assigned", "next": "researcher"}'),
        ModelResponse(content='{"summary": "Need context."}'),
        ModelResponse(content='{"concepts": ["review"], "uncertainties": []}'),
        ModelResponse(content='{"learning_outcomes": ["LO1"], "sequence": ["module 1"]}'),
        ModelResponse(content='{"module_id": "M1", "week": 1, "title": "Foundations", "topics": ["review"], "outcome_ids": ["LO1"]}'),
        ModelResponse(content='{"decision": "reject", "revision_note": "Need more detail."}'),
        ModelResponse(content='{"status": "revising", "next": "writer"}'),
        ModelResponse(content='{"module_id": "M1", "week": 1, "title": "Foundations", "topics": ["review"], "outcome_ids": ["LO1"]}'),
        ModelResponse(content='{"decision": "reject", "revision_note": "Still incomplete."}'),
    ]

    workflow = NativeWorkflow(
        model_client=FakeModelClient(responses),
        max_revisions=1,
        enabled_role_pipeline=True,
    )

    result = workflow.run(task)

    assert result.status == "failed"
    assert result.findings[0].category == "workflow"
