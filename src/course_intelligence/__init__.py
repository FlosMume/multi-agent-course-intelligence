"""Public package interface for the course-intelligence project.

Phase 0 provided the shared contracts. Phase 1 adds the native Python
reference workflow and minimal HTTP gateway for local Ollama use.
"""

from course_intelligence.config import Settings
from course_intelligence.native import (
    NativeWorkflow,
    SafeTool,
    StructuredOutputRepairError,
    repair_structured_output,
)

__all__ = [
    "NativeWorkflow",
    "SafeTool",
    "Settings",
    "StructuredOutputRepairError",
    "repair_structured_output",
]
