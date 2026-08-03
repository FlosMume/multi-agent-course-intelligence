"""A minimal model boundary shared by local, cloud, and fake clients."""

from typing import Any, Protocol

from pydantic import Field

from course_intelligence.models.base import StrictModel


class ModelRequest(StrictModel):
    """Provider-neutral request used by tests and future gateways."""

    messages: list[dict[str, str]] = Field(min_length=1)
    response_schema: dict[str, Any] | None = None
    temperature: float = Field(default=0, ge=0, le=2)
    timeout_seconds: int = Field(default=60, ge=1, le=600)


class ModelResponse(StrictModel):
    """Normalized response that keeps raw provider objects out of the core."""

    content: str
    finish_reason: str = "stop"
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class ModelClient(Protocol):
    """Structural interface; implementations need not inherit from it."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return one bounded model response or raise a documented client error."""
        ...
