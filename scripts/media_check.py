from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from media_diagnostics import media_health

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Discrete.ai audio/video diagnostics")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--storage", type=Path, default=ROOT / "storage")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = media_health(args.root.resolve(), args.storage.resolve())
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 1 if report["status"] == "degraded" else 0


if __name__ == "__main__":
    sys.exit(main())
