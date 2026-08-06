"""Native Python reference workflow for the course-intelligence use case."""

from __future__ import annotations

import ast
import json
import re
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from course_intelligence.models.course import CoursePlan
from course_intelligence.models.evaluation import RunTrace, TraceStep
from course_intelligence.models.results import FindingSeverity, ReviewFinding
from course_intelligence.models.tasks import CourseIntelligenceTask
from course_intelligence.protocols.model_client import ModelRequest
from course_intelligence.protocols.orchestrator import OrchestrationResult


class StructuredOutputRepairError(ValueError):
    """Raised when a model response cannot be converted into valid JSON."""


def repair_structured_output(raw_output: str) -> dict[str, Any]:
    """Normalize fenced or slightly malformed JSON into a Python dictionary."""

    if not isinstance(raw_output, str):
        raise TypeError("Structured output must be a string.")

    candidate = raw_output.strip()
    if not candidate:
        raise StructuredOutputRepairError("Model returned empty structured output.")

    for cleaned in _candidate_strings(candidate):
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError):
                continue
        if isinstance(parsed, dict):
            return parsed
        raise StructuredOutputRepairError("Structured output was not a JSON object.")

    raise StructuredOutputRepairError("Unable to repair model output into valid JSON.")


def _candidate_strings(raw_output: str) -> list[str]:
    """Generate plausible JSON payloads from a model response."""

    cleaned = raw_output.strip()
    candidates: list[str] = []

    fence_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
    match = fence_pattern.search(cleaned)
    if match:
        candidates.append(match.group(1).strip())

    if cleaned.startswith("```") and cleaned.endswith("```"):
        without_fence = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        candidates.append(without_fence.strip())

    candidates.append(cleaned)

    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(cleaned[first_brace : last_brace + 1])

    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        candidates.append(cleaned[first_bracket : last_bracket + 1])

    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item and item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


@dataclass(frozen=True)
class SafeTool:
    """A minimal, allowlisted tool that can be invoked with keyword arguments."""

    name: str
    description: str
    func: Callable[..., Any]
    allowed_args: set[str] | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Tool name must not be empty.")
        if not self.description.strip():
            raise ValueError("Tool description must not be empty.")

    def invoke(self, **kwargs: Any) -> Any:
        """Execute the tool with a validated argument set."""

        if self.allowed_args is not None:
            unexpected = set(kwargs) - self.allowed_args
            if unexpected:
                allowed = ", ".join(sorted(self.allowed_args)) or "none"
                raise ValueError(
                    f"Tool '{self.name}' received unexpected arguments: {sorted(unexpected)}; allowed: {allowed}"
                )
        return self.func(**kwargs)

    def __call__(self, **kwargs: Any) -> Any:
        return self.invoke(**kwargs)


class NativeWorkflow:
    """Reference orchestration used in the native Python baseline."""

    ROLE_SEQUENCE = [
        "coordinator",
        "researcher",
        "analyst",
        "curriculum_designer",
        "writer",
        "reviewer",
    ]

    def __init__(
        self,
        model_client: Any,
        tools: Sequence[SafeTool] | None = None,
        model_name: str = "qwen2:7b-instruct",
        max_steps: int = 12,
        max_revisions: int = 2,
        enabled_role_pipeline: bool = True,
    ) -> None:
        self.model_client = model_client
        self.tools = list(tools or [])
        self.model_name = model_name
        self.max_steps = max_steps
        self.max_revisions = max_revisions
        self.enabled_role_pipeline = enabled_role_pipeline

    def run(self, task: CourseIntelligenceTask) -> OrchestrationResult:
        """Execute a bounded workflow using the six logical roles or a single draft path."""

        started = datetime.now(UTC)
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        steps: list[TraceStep] = [
            TraceStep(
                sequence=1,
                actor="native_workflow",
                action="prepare_task",
                status="started",
                detail=f"Task {task.task_id} received for {task.task_type.value}.",
            )
        ]

        if not self.enabled_role_pipeline:
            return self._run_single_pass(task, started, trace_id, steps)
        return self._run_role_pipeline(task, started, trace_id, steps)

    def _run_single_pass(
        self,
        task: CourseIntelligenceTask,
        started: datetime,
        trace_id: str,
        steps: list[TraceStep],
    ) -> OrchestrationResult:
        """Backward-compatible single-call path used by the deterministic test double."""

        tool_calls = 0
        try:
            prompt = self._build_prompt(task)
            request = ModelRequest(
                messages=[
                    {"role": "system", "content": self._system_message()},
                    {"role": "user", "content": prompt},
                ],
                response_schema={"type": "object"},
                temperature=0.1,
                timeout_seconds=120,
            )
            response = self.model_client.complete(request)
            payload = repair_structured_output(response.content)
            course_plan = CoursePlan.model_validate(payload)
            tool_calls = self._execute_tools(task)
            completed_at = datetime.now(UTC)
            steps.append(
                TraceStep(
                    sequence=2,
                    actor="model",
                    action="draft_course_plan",
                    status="completed",
                    duration_ms=max(1, int((completed_at - started).total_seconds() * 1000)),
                    detail="Course plan validated against the common plan schema.",
                )
            )
            trace = RunTrace(
                trace_id=trace_id,
                framework="native",
                model_provider="ollama",
                model_name=self.model_name,
                started_at=started,
                completed_at=completed_at,
                steps=steps,
                model_calls=1,
                tool_calls=tool_calls,
            )
            return OrchestrationResult(status="completed", course_plan=course_plan, trace=trace)
        except Exception as exc:  # noqa: BLE001 - preserve workflow failure visibility
            completed_at = datetime.now(UTC)
            steps.append(
                TraceStep(
                    sequence=2,
                    actor="native_workflow",
                    action="fail_task",
                    status="failed",
                    duration_ms=max(1, int((completed_at - started).total_seconds() * 1000)),
                    detail=str(exc),
                )
            )
            trace = RunTrace(
                trace_id=trace_id,
                framework="native",
                model_provider="ollama",
                model_name=self.model_name,
                started_at=started,
                completed_at=completed_at,
                steps=steps,
                model_calls=1,
                tool_calls=tool_calls,
            )
            return OrchestrationResult(
                status="failed",
                findings=[
                    ReviewFinding(
                        finding_id=f"finding-{uuid.uuid4().hex[:8]}",
                        severity=FindingSeverity.ERROR,
                        category="workflow",
                        description="The native workflow failed to convert the model output into a valid course plan.",
                        evidence_ids=[],
                        recommendation="Inspect the model output and validate the structured repair path.",
                    )
                ],
                trace=trace,
            )

    def _run_role_pipeline(
        self,
        task: CourseIntelligenceTask,
        started: datetime,
        trace_id: str,
        steps: list[TraceStep],
    ) -> OrchestrationResult:
        """Run the explicit six-role pipeline with a bounded reviewer loop."""

        outputs: dict[str, Any] = {}
        revision_count = 0
        step_count = 1
        latest_error: str | None = None
        current_pipeline = list(self.ROLE_SEQUENCE)

        while step_count <= self.max_steps:
            for role in current_pipeline:
                if step_count > self.max_steps:
                    break
                role_payload = self._invoke_role(task, role, outputs, revision_count)
                outputs[role] = role_payload
                step_count += 1
                steps.append(
                    TraceStep(
                        sequence=len(steps) + 1,
                        actor=role,
                        action="role_turn",
                        status="completed",
                        duration_ms=1,
                        detail=f"{role} produced structured output.",
                    )
                )

                if role == "reviewer":
                    decision = str(role_payload.get("decision", "reject")).lower()
                    if decision == "approve":
                        return self._finalize_success(task, started, trace_id, steps, outputs)
                    if revision_count >= self.max_revisions:
                        latest_error = "Reviewer rejected the draft after the revision limit was reached."
                        return self._finalize_failure(task, started, trace_id, steps, latest_error)
                    revision_count += 1
                    outputs["revision_note"] = role_payload.get(
                        "revision_note", "Please revise the draft with the required corrections."
                    )
                    current_pipeline = ["coordinator", "writer", "reviewer"]
                    break

            if current_pipeline == ["coordinator", "writer", "reviewer"]:
                continue
            break

        latest_error = "Workflow reached the maximum step budget before approval."
        return self._finalize_failure(task, started, trace_id, steps, latest_error)

    def _invoke_role(
        self,
        task: CourseIntelligenceTask,
        role: str,
        outputs: dict[str, Any],
        revision_count: int,
    ) -> dict[str, Any]:
        """Call the dependency-injected model client once per role and repair the structure."""

        request = ModelRequest(
            messages=[
                {
                    "role": "system",
                    "content": self._role_system_message(role),
                },
                {
                    "role": "user",
                    "content": self._role_user_prompt(task, role, outputs, revision_count),
                },
            ],
            response_schema={"type": "object"},
            temperature=0.1,
            timeout_seconds=120,
        )
        response = self.model_client.complete(request)
        return repair_structured_output(response.content)

    def _role_system_message(self, role: str) -> str:
        role_map = {
            "coordinator": "You coordinate the workflow and keep the task focused on the course brief.",
            "researcher": "Extract relevant facts from the approved source material and identify key themes.",
            "analyst": "Identify the central concepts, relationships, instructional implications, and open uncertainties.",
            "curriculum_designer": "Propose measurable learning outcomes and a coherent teaching sequence.",
            "writer": "Draft a clear course briefing in the expected structured format.",
            "reviewer": "Approve only if the result is complete, safe, and consistent with the brief; otherwise reject with a revision request.",
        }
        return role_map.get(role, "Follow the task instructions carefully.")

    def _role_user_prompt(
        self,
        task: CourseIntelligenceTask,
        role: str,
        outputs: dict[str, Any],
        revision_count: int,
    ) -> str:
        learning_outcomes = ", ".join(
            f"{item.outcome_id}: {item.statement}" for item in task.course.learning_outcomes
        )
        prior = json.dumps(outputs, default=str)
        return (
            f"Role: {role}. "
            f"Task ID: {task.task_id}. "
            f"Course title: {task.course.title}. "
            f"Audience: {task.course.audience}. "
            f"Duration weeks: {task.course.duration_weeks}. "
            f"Learning outcomes: {learning_outcomes}. "
            f"Acceptance criteria: {'; '.join(task.acceptance_criteria)}. "
            f"Revision count: {revision_count}. "
            f"Prior role outputs: {prior}. "
            "Respond with a valid JSON object that contains the role-specific result and a concise rationale."
        )

    def _finalize_success(
        self,
        task: CourseIntelligenceTask,
        started: datetime,
        trace_id: str,
        steps: list[TraceStep],
        outputs: dict[str, Any],
    ) -> OrchestrationResult:
        completed_at = datetime.now(UTC)
        writer_payload = outputs.get("writer") or outputs.get("curriculum_designer") or {}
        if not isinstance(writer_payload, dict):
            raise TypeError("Writer output was not a dictionary payload.")
        try:
            plan_payload = writer_payload if "schema_version" in writer_payload else {
                "schema_version": "1.0",
                "course": task.course.model_dump(),
                "modules": writer_payload.get("modules", []),
                "assessments": writer_payload.get("assessments", []),
                "assumptions": writer_payload.get("assumptions", ["No additional assumptions."]),
                "requires_human_approval": True,
            }
            course_plan = CoursePlan.model_validate(plan_payload)
        except Exception as exc:  # noqa: BLE001 - preserve workflow failure visibility
            return self._finalize_failure(task, started, trace_id, steps, str(exc))

        trace = RunTrace(
            trace_id=trace_id,
            framework="native",
            model_provider="ollama",
            model_name=self.model_name,
            started_at=started,
            completed_at=completed_at,
            steps=steps,
            model_calls=len(steps),
            tool_calls=self._execute_tools(task),
        )
        return OrchestrationResult(status="completed", course_plan=course_plan, trace=trace)

    def _finalize_failure(
        self,
        task: CourseIntelligenceTask,
        started: datetime,
        trace_id: str,
        steps: list[TraceStep],
        detail: str,
    ) -> OrchestrationResult:
        completed_at = datetime.now(UTC)
        trace = RunTrace(
            trace_id=trace_id,
            framework="native",
            model_provider="ollama",
            model_name=self.model_name,
            started_at=started,
            completed_at=completed_at,
            steps=steps,
            model_calls=len(steps),
            tool_calls=0,
        )
        return OrchestrationResult(
            status="failed",
            findings=[
                ReviewFinding(
                    finding_id=f"finding-{uuid.uuid4().hex[:8]}",
                    severity=FindingSeverity.ERROR,
                    category="workflow",
                    description=detail,
                    evidence_ids=[],
                    recommendation="Inspect the role outputs and fix the rejected draft within the revision budget.",
                )
            ],
            trace=trace,
        )

    def _build_prompt(self, task: CourseIntelligenceTask) -> str:
        outcomes = ", ".join(
            f"{item.outcome_id}: {item.statement}" for item in task.course.learning_outcomes
        )
        return (
            "Return a valid JSON object that matches the CoursePlan schema. "
            "The JSON must include schema_version, course, modules, assessments, assumptions, and requires_human_approval. "
            f"Course: {task.course.title} ({task.course.course_id}). Audience: {task.course.audience}. "
            f"Duration: {task.course.duration_weeks} weeks. Learning outcomes: {outcomes}. "
            f"Acceptance criteria: {'; '.join(task.acceptance_criteria)}. "
            f"Prohibited actions: {'; '.join(task.prohibited_actions) if task.prohibited_actions else 'none'}"
        )

    def _system_message(self) -> str:
        tool_names = ", ".join(tool.name for tool in self.tools) if self.tools else "no tools"
        return (
            "You are a careful course-planning assistant. Produce only valid JSON and use the exact CoursePlan schema. "
            f"Allowed tool names: {tool_names}."
        )

    def _execute_tools(self, task: CourseIntelligenceTask) -> int:
        executed = 0
        for tool in self.tools:
            try:
                tool.invoke(task_id=task.task_id, course_id=task.course.course_id)
                executed += 1
            except TypeError:
                continue
            except ValueError:
                continue
        return executed
