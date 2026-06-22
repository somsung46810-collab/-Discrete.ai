from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_conversion import convert


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert audio to waveform video and frame image")
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.audio, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
