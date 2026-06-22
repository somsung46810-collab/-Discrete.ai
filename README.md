# CyGlobs Art Studio

CyGlobs Art Studio runs on the embedded CyGlobs Python Framework For Full Stack Developers and CyGlobsGL. Artwork and media conversion are local, deterministic, and independent of external AI providers.

## Architecture

- `cyglobs_app.py` provides the standard-library HTTP and JSON runtime.
- `cyglobs_framework/` provides protocol envelopes, comparison, routing, retry, inverse operations, and contingency behavior.
- `cyglobsgl_generation.py` creates deterministic procedural SVG artwork locally.
- `graphics_runtime.py` and `cyglobsgl.js` provide directives, MVP rendering, metadata, and browser framebuffer output.
- `media_conversion.py` converts audio into a waveform video, extracts a representative image, and deduplicates matching outputs by SHA-256.
- `ai_generation.py` remains only as a compatibility import and does not provide an external AI service.

The runtime is treated as a normal full-stack Python application. Its operation does not depend on an AI identity, CI gate, CD system, or external image model.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

On Windows PowerShell:

```powershell
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Audio/video conversion also requires `ffmpeg` on the host.

## Run

```bash
python -m cyglobs_app
```

Open `http://127.0.0.1:8000`.

## Convert audio to video to image

```bash
cyglobs-media-convert input.wav output-media
```

Equivalent module command:

```bash
python scripts/convert_media.py input.wav output-media
```

The converter produces:

- `<name>-waveform.mp4`
- `<name>-frame.png`
- `<name>-conversion.json`
- `media-dedupe-index.json`

When a new video or image has the same SHA-256 hash as an existing output, the duplicate is removed and the manifest points to the canonical file.

## Validate locally

```bash
python scripts/check_all.py
python scripts/media_check.py
ruff check ai_generation.py cyglobsgl_generation.py cyglobs_app.py graphics_runtime.py media_conversion.py media_diagnostics.py cyglobs_framework scripts tests
pytest
python -m build
```

## DUPE and DEDUPE release model

The project uses explicit local release operations rather than CI/CD automation.

Create a source release under a release root, then duplicate it:

```bash
bash scripts/dupe_release.sh /home/cyglobs/apps/studio release-source release-target
```

The DUPE operation:

- copies the immutable application release,
- preserves shared storage through a symbolic link,
- verifies the complete CyGlobs full-stack framework,
- verifies CyGlobsGL runtime files,
- requires the audio-to-video-to-image converter,
- rejects incomplete targets,
- removes partial duplicates after failure,
- writes `DUPE_MANIFEST.json`,
- records one canonical active framework and canonical media outputs as the DEDUPE strategy.

No GitHub Actions workflows, CI pipeline, or automatic deployment trigger are required.

## Capabilities

- Local CyGlobsGL Python artwork generation
- Audio-to-waveform-video conversion
- Video-frame image extraction
- SHA-256 media-output deduplication
- Deterministic SVG output
- Square, landscape, and portrait compositions
- Wireframe, triangle, and contingency rendering modes
- CyGlobs directive validation and metadata
- Browser framebuffer rendering
- Audio/video repository diagnostics
- SQLite users, creations, likes, and credits
- Local uploads and generated-image downloads
- Manual DUPE, DEDUPE, health verification, and rollback operations
