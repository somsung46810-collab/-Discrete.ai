# Discrete.ai

Discrete Art Studio runs on the embedded CyGlobs Python framework and CyGlobsGL.

## Architecture

- `cyglobs_app.py` provides the HTTP and JSON runtime using Python's standard library.
- `cyglobs_framework/` provides protocol envelopes, comparison, operation routing, configuration, retry, and fallback behavior.
- `graphics_runtime.py` provides CyGlobsGL directive packets and the default radius constraint.
- `cyglobsgl.js` provides the live browser Model-View-Projection renderer and canvas framebuffer.
- `sqlite3`, `hashlib`, `hmac`, `urllib`, and `http.server` provide persistence, authentication, provider access, payments, and static serving.

The application does not use Flask, FastAPI, Uvicorn, Pydantic, SQLAlchemy, or container tooling.

## Install

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m pip check
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
python -m pip check
```

## Configuration

`.env.example` documents the supported variable names. Export the variables you need before starting the server. The defaults use a local SQLite file and `storage/` directory, so no configuration is required for local use.

## Run

```bash
python -m cyglobs_app
```

Or use the installed command:

```bash
discrete-art-studio
```

Open `http://127.0.0.1:8000`.

## Validate

```bash
ruff check cyglobs_app.py graphics_runtime.py cyglobs_framework tests
pytest --cov=cyglobs_app --cov=cyglobs_framework --cov=graphics_runtime
python -m build
```

## Runtime capabilities

- Static website serving
- CyGlobs RPC at `/rpc`
- SQLite users, creations, likes, and credits
- PBKDF2 password hashing
- HMAC-signed expiring access tokens
- Base64 image uploads with type and size restrictions
- External image-provider requests through `urllib`
- Optional Stripe Checkout through direct HTTPS requests
- Local CyGlobsGL rendering when external generation is unavailable
