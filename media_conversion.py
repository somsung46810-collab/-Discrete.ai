from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_ffmpeg(args: list[str]) -> None:
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("ffmpeg is required")
    process = subprocess.run(
        [executable, "-y", *args],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or "media conversion failed")


def convert(audio: Path, output: Path) -> dict[str, object]:
    audio = audio.resolve()
    output = output.resolve()
    if not audio.is_file():
        raise FileNotFoundError(audio)
    output.mkdir(parents=True, exist_ok=True)
    video = output / f"{audio.stem}-waveform.mp4"
    image = output / f"{audio.stem}-frame.png"

    run_ffmpeg([
        "-i", str(audio),
        "-filter_complex", "showwaves=s=1280x720:mode=cline:colors=white,format=yuv420p",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video),
    ])
    run_ffmpeg(["-ss", "1", "-i", str(video), "-frames:v", "1", str(image)])

    index_path = output / "media-dedupe-index.json"
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    result: dict[str, object] = {
        "operation": "AUDIO_TO_VIDEO_TO_IMAGE",
        "runtime": "CyGlobs Python Framework For Full Stack Developers",
        "renderer": "CyGlobsGL",
        "audio": str(audio),
        "video": str(video),
        "image": str(image),
        "audio_sha256": sha256(audio),
        "video_sha256": sha256(video),
        "image_sha256": sha256(image),
    }
    for key, path in (("video", video), ("image", image)):
        digest = str(result[f"{key}_sha256"])
        existing = index.get(digest)
        if existing and existing != path.name:
            path.unlink()
            result[key] = str(output / existing)
            result[f"{key}_deduped"] = True
        else:
            index[digest] = path.name
            result[f"{key}_deduped"] = False
    index_path.write_text(json.dumps(index, indent=2) + "\n")
    (output / f"{audio.stem}-conversion.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
