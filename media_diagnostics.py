"""Local audio/video health diagnostics for Discrete Art Studio."""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
import json
import mimetypes
from pathlib import Path
import shutil
import subprocess
from typing import Any
import wave

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
MEDIA_SUFFIXES = AUDIO_SUFFIXES | VIDEO_SUFFIXES


@dataclass(frozen=True, slots=True)
class MediaFinding:
    path: str
    kind: str
    mime_type: str
    bytes: int
    valid: bool
    detail: str
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _kind(path: Path) -> str:
    return "audio" if path.suffix.lower() in AUDIO_SUFFIXES else "video"


def _signature_check(path: Path) -> tuple[bool, str]:
    suffix = path.suffix.lower()
    with path.open("rb") as stream:
        header = stream.read(32)
    if suffix == ".wav":
        return (header[:4] == b"RIFF" and header[8:12] == b"WAVE", "RIFF/WAVE signature")
    if suffix == ".mp3":
        valid = header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)
        return valid, "ID3 or MPEG frame signature"
    if suffix in {".mp4", ".m4a", ".mov"}:
        return (b"ftyp" in header, "ISO base media ftyp signature")
    if suffix == ".webm" or suffix == ".mkv":
        return (header.startswith(b"\x1aE\xdf\xa3"), "EBML signature")
    if suffix == ".ogg":
        return (header.startswith(b"OggS"), "Ogg signature")
    if suffix == ".flac":
        return (header.startswith(b"fLaC"), "FLAC signature")
    if suffix == ".avi":
        return (header[:4] == b"RIFF" and header[8:12] == b"AVI ", "RIFF/AVI signature")
    return (bool(header), "non-empty media file")


def _wav_duration(path: Path) -> float | None:
    try:
        with closing(wave.open(str(path), "rb")) as media:
            rate = media.getframerate()
            return media.getnframes() / rate if rate else None
    except (wave.Error, EOFError):
        return None


def _ffprobe(path: Path) -> tuple[float | None, str | None]:
    executable = shutil.which("ffprobe")
    if not executable:
        return None, None
    process = subprocess.run(
        [
            executable,
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if process.returncode:
        return None, process.stderr.strip() or "ffprobe rejected the file"
    try:
        payload = json.loads(process.stdout)
        duration = float(payload.get("format", {}).get("duration", 0.0))
        format_name = str(payload.get("format", {}).get("format_name", ""))
        return duration or None, format_name or None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None, "ffprobe returned invalid JSON"


def inspect_media(path: Path, root: Path) -> MediaFinding:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    valid, detail = _signature_check(path)
    duration = _wav_duration(path) if path.suffix.lower() == ".wav" else None
    probed_duration, probe_detail = _ffprobe(path)
    if probed_duration is not None:
        duration = probed_duration
    if probe_detail:
        detail = f"{detail}; ffprobe: {probe_detail}"
    return MediaFinding(
        path=path.relative_to(root).as_posix(),
        kind=_kind(path),
        mime_type=mime_type,
        bytes=path.stat().st_size,
        valid=valid,
        detail=detail,
        duration_seconds=round(duration, 3) if duration is not None else None,
    )


def media_health(root: Path, storage: Path | None = None) -> dict[str, Any]:
    roots = [root]
    if storage and storage.resolve() != root.resolve():
        roots.append(storage)

    paths: list[tuple[Path, Path]] = []
    seen: set[Path] = set()
    for scan_root in roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in MEDIA_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append((path, scan_root))

    findings = [inspect_media(path, scan_root) for path, scan_root in paths]
    invalid = [item for item in findings if not item.valid]
    audio_count = sum(item.kind == "audio" for item in findings)
    video_count = sum(item.kind == "video" for item in findings)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if invalid:
        status = "degraded"
    elif findings:
        status = "ok"
    else:
        status = "ready-no-media"

    return {
        "status": status,
        "runtime": "CyGlobsGL Python",
        "media_processing": "diagnostic-only",
        "files_scanned": len(findings),
        "audio_files": audio_count,
        "video_files": video_count,
        "invalid_files": len(invalid),
        "ffmpeg_available": bool(ffmpeg),
        "ffprobe_available": bool(ffprobe),
        "supported_audio_extensions": sorted(AUDIO_SUFFIXES),
        "supported_video_extensions": sorted(VIDEO_SUFFIXES),
        "browser_playback": {
            "audio_element": True,
            "video_element": True,
            "project_controls_present": False,
        },
        "release_handlers": {
            "files_closed_with_context_managers": True,
            "wave_handles_closed": True,
            "subprocess_timeout_seconds": 20,
        },
        "findings": [item.to_dict() for item in findings],
    }
