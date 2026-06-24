from __future__ import annotations

import argparse
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


def environment_python(directory: Path) -> Path:
    if sys.platform == "win32":
        return directory / "Scripts" / "python.exe"
    return directory / "bin" / "python"


def automate_package_updates(*, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="discrete-package-update-") as temporary:
        environment = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = environment_python(environment)

        steps = [
            run([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]),
            run([str(python), "-m", "pip", "install", "--upgrade", "-e", ".[dev]"]),
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
            }
        )
        .ReplBuckets()
        .Request(
            {
                "scope": "all-declared-python-packages",
                "strategy": "upgrade-in-isolated-environment",
                "tests": ["static", "pytest", "build", "runtime-smoke"],
            }
        )
    )

    report = {
        "operation": "DISCRETE_PRODUCTIONS_AUTOMATED_PACKAGE_UPDATE",
        "status": "passed" if not failed else "failed",
        "steps": steps,
        "resolved_packages": freeze_output,
        "repl": buckets.to_dict(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade and validate all declared packages with Discrete Productions."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help="JSON report output path",
    )
    args = parser.parse_args()

    report = automate_package_updates(report_path=args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
