from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    repository: str
    file: str
    sha256: str
    packed_hex: str
    evaluation: dict[str, Any]
    commit_manifest: dict[str, str]


def pack_bit_fields(data: bytes) -> str:
    return " ".join(
        f"{value:02x}[{value >> 4:04b}|{value & 0x0F:04b}]" for value in data
    )


def evaluate_source(source: str) -> dict[str, Any]:
    tree = ast.parse(source, mode="exec")
    return {
        "syntax": "valid",
        "ast_nodes": sum(1 for _ in ast.walk(tree)),
    }


def commit_compile(clone: str | Path, file: str | Path) -> PipelineResult:
    repository = Path(clone).expanduser().resolve()
    source_file = (repository / file).resolve()

    if not repository.is_dir():
        raise FileNotFoundError(f"Repository does not exist: {repository}")
    if not source_file.is_relative_to(repository):
        raise ValueError("File must remain inside the repository root")
    if not source_file.is_file():
        raise FileNotFoundError(source_file)

    source_bytes = source_file.read_bytes()
    source_text = source_bytes.decode("utf-8")
    digest = hashlib.sha256(source_bytes).hexdigest()

    return PipelineResult(
        repository=str(repository),
        file=str(source_file.relative_to(repository)),
        sha256=digest,
        packed_hex=pack_bit_fields(source_bytes),
        evaluation=evaluate_source(source_text),
        commit_manifest={
            "path": str(source_file.relative_to(repository)),
            "sha256": digest,
            "message": f"Compile and validate {source_file.name}",
        },
    )


def render_result(result: PipelineResult) -> str:
    payload = asdict(result)
    payload["packed_hex"] = result.packed_hex[:256]
    return json.dumps(payload, indent=2, sort_keys=True)


__all__ = [
    "PipelineResult",
    "commit_compile",
    "evaluate_source",
    "pack_bit_fields",
    "render_result",
]
