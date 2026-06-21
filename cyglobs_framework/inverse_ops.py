from typing import Any, Callable


class InverseOperatorRegistry:
    """Map operation names to normalized service handlers."""

    def __init__(self):
        self._operators: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._operators[name] = handler

    def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._operators:
            raise ValueError("Unknown operation: {}".format(name))
        return self._operators[name](payload)
