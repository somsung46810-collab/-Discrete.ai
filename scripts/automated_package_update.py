from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import venv

from discrete_ai import ToTriangulate

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "artifacts" / "package-update-report.json"
RECEIPT_PATH = ROOT / "artifacts" / "package-update-success.json"


def run(command: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": process.returncode,
        "status": "passed" if process.returncode == 0 else "failed",
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def current_commit() -> str:
    result = run(["git", "rev-parse", "HEAD"])
    if result["returncode"] == 0 and result["stdout"]:
        return str(result["stdout"])
    return "unavailable"


def environment_python(directory: Path) -> Path:
    if sys.platform == "win32":
        return directory / "Scripts" / "python.exe"
    return directory / "bin" / "python"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def automate_package_updates(
    *,
    report_path: Path = REPORT_PATH,
    receipt_path: Path = RECEIPT_PATH,
) -> dict[str, Any]:
    commit = current_commit()

    with tempfile.TemporaryDirectory(prefix="discrete-package-update-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = environment_python(environment)

        steps = [
            run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "pip",
                    "setuptools",
                    "wheel",
                ]
            ),
            run([str(python), "-m", "pip", "install", "--upgrade", "-e", ".[dev]"]),
            run([str(python), "-m", "ruff", "check", ".", "--fix"]),
            run([str(python), "scripts/static_validate.py"]),
            run([str(python), "-m", "pytest"]),
            run([str(python), "-m", "build"]),
            run([str(python), "scripts/runtime_smoke.py"]),
            run([str(python), "-m", "pip", "freeze", "--all"]),
        ]

    failed = [step for step in steps if step["status"] == "failed"]
    freeze_output = steps[-1]["stdout"].splitlines() if steps[-1]["returncode"] == 0 else []

    buckets = (
        ToTriangulate(
            {"declared_packages": "pyproject.toml"},
            {"validated_packages": freeze_output},
        )
        .DiscreteChanges(
            {
                "operation": "automated-package-update",
                "validation": "passed" if not failed else "failed",
                "commit": commit,
            }
        )
        .ReplBuckets()
        .Request(
            {
                "scope": "all-declared-python-packages",
                "strategy": "upgrade-in-isolated-environment",
                "automated_changes": ["ruff --fix"],
                "tests": ["static", "pytest", "build", "runtime-smoke"],
                "verification": "repository-internal",
            }
        )
    )

    report = {
        "operation": "DISCRETE_PRODUCTIONS_AUTOMATED_PACKAGE_UPDATE",
        "status": "passed" if not failed else "failed",
        "verification": "repository-internal",
        "commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "resolved_packages": freeze_output,
        "repl": buckets.to_dict(),
    }
    write_json(report_path, report)

    if not failed:
        receipt = {
            "operation": report["operation"],
            "status": "passed",
            "verification": "repository-internal",
            "commit": commit,
            "generated_at": report["generated_at"],
            "checks": [step["command"] for step in steps],
            "report": str(report_path.relative_to(ROOT)),
        }
        write_json(receipt_path, receipt)
    elif receipt_path.exists():
        receipt_path.unlink()

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade and internally validate all declared packages with Discrete Productions."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help="JSON report output path",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=RECEIPT_PATH,
        help="Success receipt output path",
    )
    args = parser.parse_args()

    report = automate_package_updates(
        report_path=args.report,
        receipt_path=args.receipt,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
