from pathlib import Path

import media_conversion


def test_convert_creates_video_image_and_manifest(tmp_path, monkeypatch):
    audio = tmp_path / "tone.wav"
    audio.write_bytes(b"RIFF0000WAVEdata")
    output = tmp_path / "out"

    def fake_run(args):
        target = Path(args[-1])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"video" if target.suffix == ".mp4" else b"image")

    monkeypatch.setattr(media_conversion, "run_ffmpeg", fake_run)
    result = media_conversion.convert(audio, output)

    assert result["operation"] == "AUDIO_TO_VIDEO_TO_IMAGE"
    assert result["runtime"] == "CyGlobs Python Framework For Full Stack Developers"
    assert Path(result["video"]).is_file()
    assert Path(result["image"]).is_file()
    assert (output / "tone-conversion.json").is_file()
    assert (output / "media-dedupe-index.json").is_file()


def test_convert_dedupes_matching_outputs(tmp_path, monkeypatch):
    output = tmp_path / "out"
    audio_a = tmp_path / "a.wav"
    audio_b = tmp_path / "b.wav"
    audio_a.write_bytes(b"audio-a")
    audio_b.write_bytes(b"audio-b")

    def fake_run(args):
        target = Path(args[-1])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"same-video" if target.suffix == ".mp4" else b"same-image")

    monkeypatch.setattr(media_conversion, "run_ffmpeg", fake_run)
    media_conversion.convert(audio_a, output)
    second = media_conversion.convert(audio_b, output)

    assert second["video_deduped"] is True
    assert second["image_deduped"] is True
    assert Path(second["video"]).name == "a-waveform.mp4"
    assert Path(second["image"]).name == "a-frame.png"
