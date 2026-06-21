from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def wait_for_health(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with request.urlopen(url, timeout=2.0) as response:
                if response.status == 200 and b'"status":"ok"' in response.read():
                    return
        except (error.URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"local health check failed: {last_error}")


def local_runtime_check(python: str) -> None:
    with tempfile.TemporaryDirectory(prefix="discrete-verify-") as directory:
        root = Path(directory)
        env = os.environ.copy()
        env.update(
            {
                "DISCRETE_HOST": "127.0.0.1",
                "DISCRETE_PORT": "8765",
                "DISCRETE_SECRET_KEY": "alternative-verification-secret",
                "DISCRETE_DATABASE_PATH": str(root / "verification.db"),
                "DISCRETE_STORAGE_DIR": str(root / "storage"),
                "DISCRETE_IMAGE_PROVIDER": "",
                "OPENAI_API_KEY": "",
            }
        )
        process = subprocess.Popen(
            [python, "-m", "cyglobs_app"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_health("http://127.0.0.1:8765/api/health")
            run(
                [python, "scripts/production_smoke_test.py", "http://127.0.0.1:8765"],
                env=env,
            )
        finally:
            process.terminate()
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate()
            if output:
                print(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Discrete.ai verification without GitHub environment gates"
    )
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    python = sys.executable
    run([python, "scripts/check_all.py"])
    if not args.skip_tests:
        run([python, "-m", "pytest"])
    if not args.skip_build:
        run([python, "-m", "build"])
        run([python, "scripts/build_production_package.py"])
    local_runtime_check(python)
    print("ALTERNATIVE VERIFICATION RESULT: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
