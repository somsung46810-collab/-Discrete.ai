from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class RequestEnvelope:
    operation: str
    protocol_version: str = "1.0"
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RequestEnvelope":
        operation = str(value.get("operation", "")).strip()
        if not operation:
            raise ValueError("operation is required")
        payload = value.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return cls(
            operation=operation,
            protocol_version=str(value.get("protocol_version", "1.0")),
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResponseEnvelope:
    status: Literal["ok", "error", "fallback"]
    protocol_version: str = "1.0"
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
