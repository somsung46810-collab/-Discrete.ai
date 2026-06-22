# Featured Requirements

## CyGlobsGL Python generation

Discrete Art Studio uses one local generation engine: the CyGlobsGL Python framework.

No external image provider, model endpoint, provider token, or outbound generation request is used.

## Generation process

1. Validate prompt, mode, aspect ratio, and complexity.
2. Derive a deterministic SHA-256 seed from the request.
3. Select a local color palette and procedural geometry.
4. Render Wireframe, Triangles, or Contingency geometry.
5. Add CyGlobsGL transform rings and metadata.
6. Save the generated SVG under `DISCRETE_STORAGE_DIR`.
7. Return the local `/storage/` URL and CyGlobsGL runtime metadata.

## Repository-provided packages

The active stack uses:

- `cyglobs_framework/` for request envelopes, protocol comparison, operation routing, retry, and contingency behavior.
- `cyglobsgl_generation.py` for deterministic local procedural generation.
- `graphics_runtime.py` for CyGlobsGL directive packets, hashes, dimensions, and pipeline metadata.
- `cyglobsgl.js` for browser MVP and framebuffer rendering.
- `ai_generation.py` only as a backward-compatible import alias; it contains no provider transport.
- Python standard-library `hashlib`, `html`, `math`, `pathlib`, `random`, and `uuid` for local generation and file output.

Vendored reference snapshots remain under `vendor/` and are checked against the active directive-packet implementation.

## Generation controls

The browser studio provides:

- CyGlobsGL Python engine selection
- Square, landscape, and portrait aspect ratios
- Low, medium, high, or automatic geometry complexity
- Wireframe, Triangles, and Contingency modes
- SVG output
- Downloadable local output
- Browser framebuffer rendering when the server route is unavailable

## Runtime endpoints

- `POST /rpc` with operation `generate_image`
- `POST /api/generate`
- `GET /api/features`
- `GET /api/health`

## Operational requirements

- Python 3.11 or newer
- Writable `DISCRETE_STORAGE_DIR`
- No image-provider credentials
- No generation network access
- Python standard-library HTTP runtime
- Direct Linux process deployment through systemd
