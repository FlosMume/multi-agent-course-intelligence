"""Framework-neutral contracts for the Course Intelligence System.

Phase 0 intentionally exports data and interfaces only. Executable workflows
and framework integrations belong to later, separately approved phases.
"""

from course_intelligence.config import Settings

__all__ = ["Settings"]
