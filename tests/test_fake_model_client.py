"""The model test double must be deterministic and fail when exhausted."""

import pytest

from course_intelligence.protocols import ModelRequest, ModelResponse
from tests.fakes.fake_model_client import FakeModelClient


def test_fake_client_returns_scripted_response_and_records_request() -> None:
    client = FakeModelClient([ModelResponse(content="structured result")])
    request = ModelRequest(messages=[{"role": "user", "content": "plan"}])

    response = client.complete(request)

    assert response.content == "structured result"
    assert client.requests == [request]


def test_fake_client_fails_clearly_when_exhausted() -> None:
    client = FakeModelClient([])
    request = ModelRequest(messages=[{"role": "user", "content": "plan"}])

    with pytest.raises(RuntimeError, match="no scripted response"):
        client.complete(request)
