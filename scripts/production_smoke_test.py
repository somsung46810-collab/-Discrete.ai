from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request


def fetch_json(url: str, timeout: float = 10.0) -> dict:
    with request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"{url} did not return a JSON object")
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a deployed Discrete.ai environment")
    parser.add_argument("base_url", help="Environment URL, for example https://staging.example.com")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    checks = {
        "health": f"{base}/api/health",
        "features": f"{base}/api/features",
    }
    failures: list[str] = []
    results: dict[str, dict] = {}

    for name, url in checks.items():
        try:
            results[name] = fetch_json(url)
        except (error.URLError, ValueError, RuntimeError) as exc:
            failures.append(f"{name}: {exc}")

    health = results.get("health", {})
    if health.get("status") != "ok":
        failures.append("health: status is not ok")
    if health.get("renderer") != "CyGlobsGL":
        failures.append("health: CyGlobsGL renderer is not reported")

    features = results.get("features", {})
    if features.get("renderer") != "CyGlobsGL":
        failures.append("features: CyGlobsGL renderer is not reported")

    print(json.dumps({"base_url": base, "results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
