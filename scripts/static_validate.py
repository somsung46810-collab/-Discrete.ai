from __future__ import annotations

import compileall
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from discrete_ai import ToTriangulate

ROOT = Path(__file__).resolve().parents[1]


def run_command(name: str, command: list[str]) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {
            "name": name,
            "status": "unavailable",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": f"{command[0]} is not installed",
        }

    process = subprocess.run(
        [executable, *command[1:]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "status": "passed" if process.returncode == 0 else "failed",
        "command": command,
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def run_static_validation() -> dict[str, Any]:
    compile_passed = compileall.compile_dir(ROOT, quiet=1, force=True)
    checks = [
        {
            "name": "compile",
            "status": "passed" if compile_passed else "failed",
            "command": [sys.executable, "-m", "compileall", "."],
            "returncode": 0 if compile_passed else 1,
            "stdout": "",
            "stderr": "",
        },
        run_command("repository_checkup", [sys.executable, "scripts/check_all.py"]),
        run_command("ruff", ["ruff", "check", "."]),
        run_command(
            "mypy",
            [
                "mypy",
                "discrete_ai.py",
                "scripts/static_validate.py",
                "scripts/runtime_smoke.py",
            ],
        ),
    ]

    failed = [check["name"] for check in checks if check["status"] == "failed"]
    unavailable = [
        check["name"] for check in checks if check["status"] == "unavailable"
    ]

    buckets = (
        ToTriangulate(
            {"compile": True, "checkup": True},
            {"compile": True, "checkup": True},
        )
        .DiscreteChanges(
            {
                "ruff": "passed" if "ruff" not in failed else "failed",
                "mypy": "passed" if "mypy" not in failed else "failed",
            }
        )
        .ReplBuckets()
        .Request(
            {
                "package": "cyglobs-art-studio",
                "operation": "static-validation",
                "checks": [check["name"] for check in checks],
            }
        )
    )

    report = {
        "operation": "DISCRETE_PRODUCTIONS_STATIC_VALIDATION",
        "status": "passed" if not failed and not unavailable else "incomplete",
        "checks": checks,
        "failed": failed,
        "unavailable": unavailable,
        "repl": buckets.to_dict(),
    }
    return report


def main() -> int:
    report = run_static_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
