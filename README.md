# Discrete.ai

Discrete Art Studio runs entirely on the embedded CyGlobsGL Python framework. Artwork generation is local, deterministic, and does not require an external image provider or model API.

## Architecture

- `cyglobs_app.py` provides the standard-library HTTP and JSON runtime.
- `cyglobs_framework/` provides protocol envelopes, comparison, operation routing, retry, and contingency behavior.
- `cyglobsgl_generation.py` creates deterministic procedural SVG artwork locally.
- `graphics_runtime.py` and `cyglobsgl.js` provide directive packets, MVP rendering, metadata, and browser framebuffer rendering.
- `ai_generation.py` is a compatibility export only; it contains no external provider implementation.
- `vendor/` contains replicated CyGlobs framework and CyGlobsGL source snapshots.

The application uses the Python standard library and the repository's CyGlobsGL runtime rather than an external web framework or image service.

## Local generation

The browser calls the CyGlobs RPC `generate_image` operation. The Python runtime derives a deterministic seed from the prompt, style, mode, aspect ratio, and complexity setting, then writes a local SVG under `storage/`.

Supported modes:

- Wireframe
- Triangles
- Contingency

Supported aspects:

- 1:1
- 16:9
- 9:16

Output format:

- SVG

No provider credential or outbound network request is required.

## Install

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Run

```bash
python -m cyglobs_app
```

Open `http://127.0.0.1:8000`.

## Validate

```bash
python scripts/check_all.py
python scripts/media_check.py
ruff check ai_generation.py cyglobsgl_generation.py cyglobs_app.py graphics_runtime.py media_diagnostics.py cyglobs_framework scripts tests
pytest --cov=cyglobsgl_generation --cov=media_diagnostics --cov=cyglobs_app --cov=cyglobs_framework --cov=graphics_runtime
python -m build
```

## Continuous deployment

`.github/workflows/deploy.yml` provides native staging and production deployment over SSH. It builds release artifacts, injects only application and optional payment secrets, runs versioned SQLite migrations, restarts `cyglobs_app`, checks `/api/health`, and restores the previous release when a health check fails.

Successful pushes to `main` can deploy to staging after CI. Production is promoted manually or with a version tag. No external image-provider secrets are needed.

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
- Native CI/CD with staging, production, migrations, health checks, releases, DUPE, and rollback
