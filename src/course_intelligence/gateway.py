"""Model gateway helpers for the native Python workflow."""

from __future__ import annotations

import json
from urllib import error, request

from course_intelligence.protocols.model_client import ModelRequest, ModelResponse


class OllamaModelClient:
    """Minimal OpenAI-compatible Ollama client used in the native reference workflow."""

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434/v1", timeout_seconds: int = 60) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete(self, request_obj: ModelRequest) -> ModelResponse:
        """Send a chat completion to Ollama's OpenAI-compatible API."""

        payload = {
            "model": self.model_name,
            "messages": request_obj.messages,
            "stream": False,
            "temperature": request_obj.temperature,
        }
        if request_obj.response_schema is not None:
            payload["response_format"] = {"type": "json_object"}

        target_url = self.base_url + "/chat/completions"
        encoded = json.dumps(payload).encode("utf-8")
        req = request.Request(
            target_url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with __import__("urllib.request").request.urlopen(req, timeout=request_obj.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:  # pragma: no cover - depends on local runtime
            raise RuntimeError(f"Ollama model call failed: {exc}") from exc

        try:
            message = body["choices"][0]["message"]["content"]
            finish_reason = body["choices"][0].get("finish_reason", "stop")
            usage = body.get("usage", {})
            return ModelResponse(
                content=message,
                finish_reason=finish_reason,
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Unexpected Ollama response format") from exc
