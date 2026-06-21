from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class ServerConfig:
    host: str = field(default_factory=lambda: os.getenv("DISCRETE_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("DISCRETE_PORT", "8000")))
    protocol_version: str = field(
        default_factory=lambda: os.getenv("DISCRETE_PROTOCOL_VERSION", "1.0")
    )


@dataclass(frozen=True)
class ClientConfig:
    base_url: str = field(
        default_factory=lambda: os.getenv("DISCRETE_BASE_URL", "http://127.0.0.1:8000")
    )
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("DISCRETE_TIMEOUT_SECONDS", "5.0"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("DISCRETE_MAX_RETRIES", "3"))
    )
