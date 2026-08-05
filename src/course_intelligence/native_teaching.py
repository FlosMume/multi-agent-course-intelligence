"""A teaching-oriented native Python reference workflow for Phase 1.

This file is intentionally written to be easy to read for learners. It keeps the
same functional ideas as a production workflow, but it explains the moving parts
step by step instead of hiding them in clever abstractions.

What this module demonstrates:
- the six logical roles required by the Phase 1 prompt;
- dependency injection for the model client;
- allowlisted tool usage;
- bounded revision loops;
- validation of model output before it becomes a course plan;
- clear separation between the core domain model and orchestration logic.

This file is meant for education and portfolio purposes. It is not a framework
implementation and does not depend on LangChain, LangGraph, CrewAI, AutoGen, or
any other orchestration library.
"""

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
    """Raised when a model output cannot be converted into a usable dictionary.

    Large language models often return output wrapped in markdown fences or with
    minor formatting issues. This error is the explicit signal that the workflow
    has reached a point where it cannot safely convert the output into the
    expected structure.
    """


def repair_structured_output(raw_output: str) -> dict[str, Any]:
    """Convert a model response into a Python dictionary.

    The workflow expects model messages to produce a JSON object. In practice,
    models may return fenced markdown, missing commas, or slightly malformed
    Python-literal output. This function tries several common repair paths in
    order and stops when it finds a valid dictionary.
    """

    if not isinstance(raw_output, str):
        raise TypeError("Structured output must be a string.")

    candidate = raw_output.strip()
    if not candidate:
        raise StructuredOutputRepairError("Model returned empty structured output.")

    # Try a few likely variants. The JSON path is the cleanest and preferred
    # option, but many models produce fenced markdown or Python-like literal
    # strings during early teaching prototypes.
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

        raise StructuredOutputRepairError(
            "Structured output was not a JSON object."
        )

    raise StructuredOutputRepairError(
        "Unable to repair model output into valid JSON."
    )


def _candidate_strings(raw_output: str) -> list[str]:
    """Generate common candidate strings from a raw model response.

    A model may produce one of these shapes:
    - pure JSON
    - fenced JSON inside triple backticks
    - extra text around the JSON object
    - a Python dictionary literal

    We keep the search simple and deterministic rather than trying to be too
    clever; the goal is to help educational readers follow the repair strategy.
    """

    cleaned = raw_output.strip()
    candidates: list[str] = []

    # First: extract fenced JSON if it exists.
    fence_pattern = re.compile(
        r"```(?:json)?\s*(.*?)\s*```",
        re.IGNORECASE | re.DOTALL,
    )
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

    # Second: try the original text directly.
    candidates.append(cleaned)

    # Third: trim to the JSON object itself, if the response contains extra text.
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(cleaned[first_brace : last_brace + 1])

    # We also keep the bracket-based fallback for list payloads, though the
    # workflow specifically expects a dictionary object.
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        candidates.append(cleaned[first_bracket : last_bracket + 1])

    # Remove duplicates while preserving order.
    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item and item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


@dataclass(frozen=True)
class SafeTool:
    """A minimal tool that can be invoked only with explicit allowed arguments.

    This is intentionally conservative. It does not allow arbitrary shell access,
    filesystem traversal, or other unsafe actions. The workflow chooses a small
    allowlist and executes only those tools.
    """

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
        """Execute the tool only when all arguments are approved."""

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
    """Reference orchestration used in the Phase 1 native Python baseline.

    The workflow follows a teaching-friendly structure:
    1. validate the incoming task;
    2. call the model through a provider-neutral interface;
    3. repair the structured output when the model returns imperfect JSON;
    4. validate the result with the shared Pydantic model;
    5. run the reviewer loop with an explicit limit.

    This is intentionally independent of any framework or SDK.
    """

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
        """Store the injected dependencies and the workflow limits.

        Dependency injection matters here because the same workflow should work
        with a fake model client in tests and a real Ollama client in demos.
        """

        self.model_client = model_client
        self.tools = list(tools or [])
        self.model_name = model_name
        self.max_steps = max_steps
        self.max_revisions = max_revisions
        self.enabled_role_pipeline = enabled_role_pipeline

    def run(self, task: CourseIntelligenceTask) -> OrchestrationResult:
        """Run the workflow and always return a validated orchestration result."""

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

        # The project supports a simpler single-pass path for compatibility, but
        # the intended Phase 1 behaviour is the explicit six-role pipeline.
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
        """A simplified compatibility path for testing and quick demos."""

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
        """Run the six-role pipeline and enforce the review loop.

        The workflow starts with the normal six-role ordering, but if the reviewer
        rejects the draft, the loop narrows to a smaller revision cycle:
        coordinator -> writer -> reviewer.

        This keeps the logic readable and ensures the system does not endlessly
        repeat the same long flow.
        """

        outputs: dict[str, Any] = {}
        revision_count = 0
        step_count = 1
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
                        return self._finalize_failure(
                            task,
                            started,
                            trace_id,
                            steps,
                            "Reviewer rejected the draft after the revision limit was reached.",
                        )

                    revision_count += 1
                    outputs["revision_note"] = role_payload.get(
                        "revision_note",
                        "Please revise the draft with the required corrections.",
                    )
                    current_pipeline = ["coordinator", "writer", "reviewer"]
                    break

            # A revision loop can keep returning to coordinator/writer/reviewer.
            # Once that narrow pipeline is active, the while-loop continues until
            # the maximum revision count or step limit is reached.
            if current_pipeline == ["coordinator", "writer", "reviewer"]:
                continue
            break

        return self._finalize_failure(
            task,
            started,
            trace_id,
            steps,
            "Workflow reached the maximum step budget before approval.",
        )

    def _invoke_role(
        self,
        task: CourseIntelligenceTask,
        role: str,
        outputs: dict[str, Any],
        revision_count: int,
    ) -> dict[str, Any]:
        """Call the model for one role and repair the result before it is used."""

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
        """Explain the role instructions in simple, bounded language."""

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
        """Provide every role with the same baseline context and the current state."""

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
        """Validate the final writer output against the common CoursePlan model."""

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
        """Return a clear failure envelope with review findings and trace data."""

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
        """Build the single-pass prompt used in the compatibility path."""

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
        """Explain the model’s task to the one-shot path."""

        tool_names = ", ".join(tool.name for tool in self.tools) if self.tools else "no tools"
        return (
            "You are a careful course-planning assistant. Produce only valid JSON and use the exact CoursePlan schema. "
            f"Allowed tool names: {tool_names}."
        )

    def _execute_tools(self, task: CourseIntelligenceTask) -> int:
        """Execute tiny, allowlisted tools for the workflow demonstration."""

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
