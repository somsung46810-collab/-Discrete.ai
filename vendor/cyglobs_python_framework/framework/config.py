from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    protocol_version: str = "1.0"


@dataclass(frozen=True)
class ClientConfig:
    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: float = 5.0
    max_retries: int = 3
