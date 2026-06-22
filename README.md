# CyGlobs Art Studio

CyGlobs Art Studio runs on the embedded CyGlobs Python Framework For Full Stack Developers and CyGlobsGL. Artwork generation is local, deterministic, and independent of external AI providers.

## Architecture

- `cyglobs_app.py` provides the standard-library HTTP and JSON runtime.
- `cyglobs_framework/` provides protocol envelopes, comparison, routing, retry, inverse operations, and contingency behavior.
- `cyglobsgl_generation.py` creates deterministic procedural SVG artwork locally.
- `graphics_runtime.py` and `cyglobsgl.js` provide directives, MVP rendering, metadata, and browser framebuffer output.
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

## Run

```bash
python -m cyglobs_app
```

Open `http://127.0.0.1:8000`.

## Validate locally

```bash
python scripts/check_all.py
python scripts/media_check.py
ruff check ai_generation.py cyglobsgl_generation.py cyglobs_app.py graphics_runtime.py media_diagnostics.py cyglobs_framework scripts tests
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
- rejects incomplete targets,
- removes partial duplicates after failure,
- writes `DUPE_MANIFEST.json`,
- records a single canonical active framework package as the DEDUPE strategy.

No GitHub Actions workflows, CI pipeline, or automatic deployment trigger are required.

## Capabilities

- Local CyGlobsGL Python artwork generation
- Deterministic SVG output
- Square, landscape, and portrait compositions
- Wireframe, triangle, and contingency rendering modes
- CyGlobs directive validation and metadata
- Browser framebuffer rendering
- Audio/video repository diagnostics
- SQLite users, creations, likes, and credits
- Local uploads and generated-image downloads
- Manual DUPE, DEDUPE, health verification, and rollback operations
