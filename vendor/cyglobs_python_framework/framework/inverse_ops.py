from typing import Any, Callable


class InverseOperatorRegistry:
    """
    Maps operation names to server-side functions.

    Client sends an operation and payload. The server resolves the operation
    through this registry and returns a normalized response envelope.
    """

    def __init__(self):
        self._operators: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._operators[name] = handler

    def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._operators:
            raise ValueError(f"Unknown operation: {name}")

        return self._operators[name](payload)
