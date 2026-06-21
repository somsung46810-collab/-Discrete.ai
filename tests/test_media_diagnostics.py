from __future__ import annotations

from pathlib import Path
import wave

from media_diagnostics import media_health


def write_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as media:
        media.setnchannels(1)
        media.setsampwidth(2)
        media.setframerate(8000)
        media.writeframes(b"\x00\x00" * 800)


def test_media_health_reports_no_media(tmp_path):
    report = media_health(tmp_path)
    assert report["status"] == "ready-no-media"
    assert report["files_scanned"] == 0
    assert report["release_handlers"]["wave_handles_closed"] is True


def test_media_health_validates_wav(tmp_path):
    wav_path = tmp_path / "tone.wav"
    write_wav(wav_path)

    report = media_health(tmp_path)

    assert report["status"] == "ok"
    assert report["audio_files"] == 1
    assert report["video_files"] == 0
    assert report["invalid_files"] == 0
    assert report["findings"][0]["valid"] is True
    assert report["findings"][0]["duration_seconds"] == 0.1


def test_media_health_rejects_invalid_mp4(tmp_path):
    (tmp_path / "broken.mp4").write_bytes(b"not an mp4")

    report = media_health(tmp_path)

    assert report["status"] == "degraded"
    assert report["invalid_files"] == 1
    assert report["findings"][0]["valid"] is False
