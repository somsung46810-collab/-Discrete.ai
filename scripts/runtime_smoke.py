from __future__ import annotations

import json
from typing import Any

from discrete_ai import ToTriangulate, bits_to_hexadecimal, hexadecimal_to_bits


def run_smoke_test() -> dict[str, Any]:
    buckets = (
        ToTriangulate(
            {"mode": "dupe", "shared": 1},
            {"mode": "dedupe", "shared": 1},
        )
        .DiscreteChanges({"mode": "production"})
        .ReplBuckets()
        .Pool("11110000")
        .Pool("f0", encoding="hexadecimal->bits")
    )

    result = buckets.to_dict()
    status = buckets.status()

    checks = {
        "bits_to_hexadecimal": bits_to_hexadecimal("11110000") == "f0",
        "hexadecimal_to_bits": hexadecimal_to_bits("f0") == "11110000",
        "legacy_pool": result["pools"][0].get("hexadecimal") == "f0",
        "repl_pool": result["pools"][1].get("bits") == "11110000",
        "completion_percentage": bool(status) and status[-1]["percentage"] == 100,
        "completion_stage": bool(status) and status[-1]["stage"] == "pool",
        "no_forced_endif": bool(status) and status[-1]["condition"] == "continue",
    }

    failed = [name for name, passed in checks.items() if not passed]
    report = {
        "status": "passed" if not failed else "failed",
        "checks": checks,
        "failed": failed,
    }
    if failed:
        raise RuntimeError(json.dumps(report, indent=2))
    return report


def main() -> int:
    print(json.dumps(run_smoke_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
