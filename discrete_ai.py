from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PipelineResult:
    repository: str
    file: str
    sha256: str
    packed_hex: str
    evaluation: dict[str, Any]
    commit_manifest: dict[str, str]


@dataclass(frozen=True)
class TriangulatedEntry:
    key: str
    dupe_value: Any
    dedupe_value: Any
    resolved_value: Any
    state: str


@dataclass
class ReplBucketSet:
    buckets: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {
            "matched": [],
            "changed": [],
            "dupe_only": [],
            "dedupe_only": [],
            "conflicts": [],
        }
    )

    def add(self, entry: TriangulatedEntry) -> None:
        bucket = {
            "match": "matched",
            "changed": "changed",
            "dupe_only": "dupe_only",
            "dedupe_only": "dedupe_only",
            "conflict": "conflicts",
        }[entry.state]
        self.buckets[bucket].append(asdict(entry))

    def replay(self) -> list[dict[str, Any]]:
        order = ("matched", "changed", "dupe_only", "dedupe_only", "conflicts")
        return [item for name in order for item in self.buckets[name]]

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return self.buckets


class TriangulationPipeline:
    def __init__(self, dupe: dict[str, Any], dedupe: dict[str, Any]) -> None:
        self.dupe = dict(dupe)
        self.dedupe = dict(dedupe)
        self.entries: list[TriangulatedEntry] = []
        self.changes: dict[str, Any] = {}

    def DiscreteChanges(self, changes: dict[str, Any] | None = None) -> "TriangulationPipeline":
        self.changes = dict(changes or {})
        self.entries = []
        for key in sorted(set(self.dupe) | set(self.dedupe) | set(self.changes)):
            dupe_value = self.dupe.get(key)
            dedupe_value = self.dedupe.get(key)
            has_dupe = key in self.dupe
            has_dedupe = key in self.dedupe

            if key in self.changes:
                resolved = self.changes[key]
                state = "changed"
            elif has_dupe and has_dedupe and dupe_value == dedupe_value:
                resolved = dupe_value
                state = "match"
            elif has_dupe and not has_dedupe:
                resolved = dupe_value
                state = "dupe_only"
            elif has_dedupe and not has_dupe:
                resolved = dedupe_value
                state = "dedupe_only"
            else:
                resolved = dedupe_value
                state = "conflict"

            self.entries.append(
                TriangulatedEntry(
                    key=key,
                    dupe_value=dupe_value,
                    dedupe_value=dedupe_value,
                    resolved_value=resolved,
                    state=state,
                )
            )
        return self

    def ReplBuckets(self) -> ReplBucketSet:
        if not self.entries:
            self.DiscreteChanges()
        result = ReplBucketSet()
        for entry in self.entries:
            result.add(entry)
        return result


class ToTriangulate:
    def __init__(self, dupe: dict[str, Any], dedupe: dict[str, Any]) -> None:
        self.pipeline = TriangulationPipeline(dupe, dedupe)

    def DiscreteChanges(self, changes: dict[str, Any] | None = None) -> TriangulationPipeline:
        return self.pipeline.DiscreteChanges(changes)


def triangulate(dupe: dict[str, Any], dedupe: dict[str, Any]) -> ToTriangulate:
    return ToTriangulate(dupe, dedupe)


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
    "ReplBucketSet",
    "ToTriangulate",
    "TriangulatedEntry",
    "TriangulationPipeline",
    "commit_compile",
    "evaluate_source",
    "pack_bit_fields",
    "render_result",
    "triangulate",
]
