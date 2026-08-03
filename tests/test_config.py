"""Configuration tests prove that cloud access cannot be selected accidentally."""

import pytest
from pydantic import ValidationError

from course_intelligence.config import Settings


def test_local_inference_is_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.model_provider == "ollama"
    assert settings.cloud_model_enabled is False


def test_cloud_provider_requires_explicit_opt_in() -> None:
    with pytest.raises(ValidationError, match="cloud access is disabled"):
        Settings(model_provider="cloud", cloud_model_name="example", _env_file=None)
