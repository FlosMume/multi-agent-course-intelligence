"""Shared validation behaviour for all serialized domain records."""

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Reject unknown fields so adapter mistakes cannot pass silently."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
