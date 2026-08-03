"""Structural interfaces implemented in later phases."""

from course_intelligence.protocols.model_client import (
    ModelClient,
    ModelRequest,
    ModelResponse,
)
from course_intelligence.protocols.orchestrator import OrchestrationResult, Orchestrator

__all__ = [
    "ModelClient",
    "ModelRequest",
    "ModelResponse",
    "OrchestrationResult",
    "Orchestrator",
]
