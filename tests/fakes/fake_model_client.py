"""Deterministic model double used to keep unit tests offline and repeatable."""

from collections import deque

from course_intelligence.protocols.model_client import ModelRequest, ModelResponse


class FakeModelClient:
    """Return scripted responses and retain requests for test assertions.

    Unlike a mock tied to a provider SDK, this fake exercises the project's own
    protocol. It therefore remains useful when provider libraries change.
    """

    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = deque(responses)
        self.requests: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Record the request and return the next prearranged response."""

        self.requests.append(request)
        if not self._responses:
            raise RuntimeError("FakeModelClient has no scripted response remaining")
        return self._responses.popleft()
