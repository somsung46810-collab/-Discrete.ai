import time
from typing import Callable, TypeVar


T = TypeVar("T")


class RetryPolicy:
    def __init__(self, max_retries: int = 3, delay_seconds: float = 0.25):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds

    def run(self, fn: Callable[[], T]) -> T:
        last_error: Exception | None = None

        for _ in range(self.max_retries):
            try:
                return fn()
            except Exception as error:
                last_error = error
                time.sleep(self.delay_seconds)

        raise RuntimeError(
            f"Retry policy failed after {self.max_retries} attempts"
        ) from last_error


class FallbackPlanner:
    def fallback_response(self, error: Exception) -> dict:
        return {
            "status": "fallback",
            "result": {
                "message": "Fallback response activated",
                "safe_mode": True,
            },
            "error": str(error),
        }
