# Discrete.ai

Discrete Art Studio runs on the embedded CyGlobs Python framework and CyGlobsGL, with real image generation through a configured provider.

## Architecture

- `cyglobs_app.py` provides the standard-library HTTP and JSON runtime.
- `cyglobs_framework/` provides protocol envelopes, comparison, operation routing, retry, and fallback behavior.
- `graphics_runtime.py` and `cyglobsgl.js` provide directive packets, MVP rendering, and local framebuffer fallback.
- `ai_generation.py` provides real image-provider requests, response normalization, image persistence, and feature reporting.
- `vendor/` contains the replicated upstream framework and CyGlobsGL source snapshots.

The application does not use Flask, FastAPI, Uvicorn, Pydantic, SQLAlchemy, or container tooling.

## Configure real generation

Set either an `openai` or `generic` provider in the environment. The full configuration, accepted response shapes, generation controls, and endpoints are documented in `FEATURE_REQUIREMENTS.md`.

The browser calls the CyGlobs RPC `generate_image` operation. Base64 provider output is saved under `storage/`; remote image URLs are displayed directly. Provider failures automatically retain the CyGlobsGL canvas result.

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
ruff check ai_generation.py cyglobs_app.py graphics_runtime.py cyglobs_framework tests
pytest --cov=ai_generation --cov=cyglobs_app --cov=cyglobs_framework --cov=graphics_runtime
python -m build
```

## Capabilities

- Real AI image generation
- PNG, WebP, and JPEG output
- Square, landscape, and portrait sizes
- CyGlobs directive validation
- Automatic CyGlobsGL fallback
- SQLite users, creations, likes, and credits
- Local uploads and generated-image downloads
