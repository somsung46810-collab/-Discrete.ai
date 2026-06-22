from typing import Any, Literal
from pydantic import BaseModel, Field


class RequestEnvelope(BaseModel):
    protocol_version: str = "1.0"
    operation: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ResponseEnvelope(BaseModel):
    protocol_version: str = "1.0"
    status: Literal["ok", "error", "fallback"]
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
