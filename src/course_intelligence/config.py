"""Validated, local-first project configuration.

The settings object contains no provider SDK logic. Keeping configuration
separate lets every future framework adapter receive the same execution limits
and model selection rules.
"""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings with safe defaults for teaching use."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model_provider: Literal["ollama", "cloud"] = "ollama"
    model_name: str = "qwen2:7b-instruct"
    ollama_base_url: str = "http://localhost:11434/v1"

    cloud_model_enabled: bool = False
    cloud_model_provider: str = ""
    cloud_model_name: str = ""
    cloud_model_api_key: str = Field(default="", repr=False)

    max_agent_turns: int = Field(default=8, ge=1, le=50)
    model_timeout_seconds: int = Field(default=60, ge=1, le=600)
    max_output_characters: int = Field(default=20_000, ge=100, le=1_000_000)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @model_validator(mode="after")
    def cloud_provider_requires_explicit_opt_in(self) -> "Settings":
        """Reject an accidental cloud selection before any client is created."""

        if self.model_provider == "cloud" and not self.cloud_model_enabled:
            raise ValueError("Cloud provider selected while cloud access is disabled")
        if self.model_provider == "cloud" and not self.cloud_model_name:
            raise ValueError("A cloud model name is required for cloud inference")
        return self
