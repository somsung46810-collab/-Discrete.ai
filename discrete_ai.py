from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


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


@dataclass(frozen=True)
class StatusUpdate:
    percentage: int
    stage: str
    message: str
    condition: str = "continue"


StatusCallback = Callable[[StatusUpdate], None]


def bits_to_hexadecimal(bits: str) -> str:
    normalized = "".join(bits.split())
    if not normalized:
        raise ValueError("bits must not be empty")
    if any(bit not in "01" for bit in normalized):
        raise ValueError("bits must contain only 0 and 1")
    width = (len(normalized) + 3) // 4
    return f"{int(normalized, 2):0{width}x}"


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
    status_updates: list[StatusUpdate] = field(default_factory=list)
    pools: list[dict[str, str]] = field(default_factory=list)
    package_update_requests: list[dict[str, Any]] = field(default_factory=list)

    def add(self, entry: TriangulatedEntry) -> None:
        bucket = {
            "match": "matched",
            "changed": "changed",
            "dupe_only": "dupe_only",
            "dedupe_only": "dedupe_only",
            "conflict": "conflicts",
        }[entry.state]
        self.buckets[bucket].append(asdict(entry))

    def Pool(self, bits: str) -> "ReplBucketSet":
        self.pools.append(
            {
                "source": bits,
                "encoding": "bits->hexadecimal",
                "hexadecimal": bits_to_hexadecimal(bits),
            }
        )
        return self

    def Request(
        self,
        package_updates: dict[str, Any] | list[str] | str,
    ) -> "ReplBucketSet":
        self.package_update_requests.append(
            {
                "type": "package_updates",
                "request": package_updates,
                "status": "requested",
            }
        )
        return self

    def replay(self) -> list[dict[str, Any]]:
        order = ("matched", "changed", "dupe_only", "dedupe_only", "conflicts")
        return [item for name in order for item in self.buckets[name]]

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.buckets,
            "pools": list(self.pools),
            "package_update_requests": list(self.package_update_requests),
        }

    def status(self) -> list[dict[str, Any]]:
        return [asdict(update) for update in self.status_updates]


class TriangulationPipeline:
    def __init__(
        self,
        dupe: dict[str, Any],
        dedupe: dict[str, Any],
        status_callback: StatusCallback | None = None,
    ) -> None:
        self.dupe = dict(dupe)
        self.dedupe = dict(dedupe)
        self.entries: list[TriangulatedEntry] = []
        self.changes: dict[str, Any] = {}
        self.status_updates: list[StatusUpdate] = []
        self.status_callback = status_callback

    def _status(
        self,
        percentage: int,
        stage: str,
        message: str,
        condition: str = "continue",
    ) -> None:
        update = StatusUpdate(
            percentage=max(0, min(100, percentage)),
            stage=stage,
            message=message,
            condition=condition,
        )
        self.status_updates.append(update)
        if self.status_callback is not None:
            self.status_callback(update)

    def DiscreteChanges(
        self, changes: dict[str, Any] | None = None
    ) -> "TriangulationPipeline":
        self.changes = dict(changes or {})
        self.entries = []
        self.status_updates = []
        keys = sorted(set(self.dupe) | set(self.dedupe) | set(self.changes))
        self._status(0, "read", "Read DUPE, DEDUPE, and explicit change inputs")

        if not keys:
            self._status(80, "evaluate", "No values required triangulation")
            return self

        for index, key in enumerate(keys, start=1):
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
            percentage = round(index / len(keys) * 80)
            self._status(
                percentage,
                "evaluate",
                f"Evaluated {index} of {len(keys)} triangulation keys",
            )
        return self

    def ReplBuckets(self) -> ReplBucketSet:
        if not self.entries:
            self.DiscreteChanges()
        result = ReplBucketSet()
        total = len(self.entries)

        if total == 0:
            self._status(100, "print", "REPL buckets complete")
        else:
            for index, entry in enumerate(self.entries, start=1):
                result.add(entry)
                percentage = 80 + round(index / total * 20)
                self._status(
                    percentage,
                    "print",
                    f"Printed {index} of {total} entries into REPL buckets",
                )

        result.status_updates = list(self.status_updates)
        return result

    def status(self) -> list[dict[str, Any]]:
        return [asdict(update) for update in self.status_updates]


class ToTriangulate:
    def __init__(
        self,
        dupe: dict[str, Any],
        dedupe: dict[str, Any],
        status_callback: StatusCallback | None = None,
    ) -> None:
        self.pipeline = TriangulationPipeline(dupe, dedupe, status_callback)

    def DiscreteChanges(
        self, changes: dict[str, Any] | None = None
    ) -> TriangulationPipeline:
        return self.pipeline.DiscreteChanges(changes)


def triangulate(
    dupe: dict[str, Any],
    dedupe: dict[str, Any],
    status_callback: StatusCallback | None = None,
) -> ToTriangulate:
    return ToTriangulate(dupe, dedupe, status_callback)


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
    "StatusCallback",
    "StatusUpdate",
    "ToTriangulate",
    "TriangulatedEntry",
    "TriangulationPipeline",
    "bits_to_hexadecimal",
    "commit_compile",
    "evaluate_source",
    "pack_bit_fields",
    "render_result",
    "triangulate",
]
