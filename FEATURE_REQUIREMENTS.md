# Featured Requirements

## Real AI generation

Discrete Art Studio supports two real image-generation provider modes without adding production packages outside the repository runtime.

### OpenAI image provider

Required environment variables:

```text
DISCRETE_IMAGE_PROVIDER=openai
OPENAI_API_KEY=your-key
DISCRETE_IMAGE_MODEL=gpt-image-2
```

Optional override:

```text
DISCRETE_IMAGE_PROVIDER_URL=https://api.openai.com/v1/images/generations
```

The provider returns base64 image data, which Discrete.ai writes to the configured storage directory and serves through `/storage/`.

### Generic JSON provider

Required environment variables:

```text
DISCRETE_IMAGE_PROVIDER=generic
DISCRETE_IMAGE_PROVIDER_URL=https://provider.example/generate
DISCRETE_IMAGE_PROVIDER_TOKEN=your-token
DISCRETE_IMAGE_MODEL=provider-model
```

Accepted response shapes include:

```json
{"image_url":"https://provider.example/image.png"}
```

```json
{"b64_json":"BASE64_IMAGE_DATA"}
```

```json
{"data":[{"url":"https://provider.example/image.png"}]}
```

```json
{"data":[{"b64_json":"BASE64_IMAGE_DATA"}]}
```

## Repository-provided packages

The active stack uses:

- `cyglobs_framework/` for request envelopes, protocol comparison, operation routing, retry, and fallback behavior.
- `graphics_runtime.py` for CyGlobsGL directive packets and render-manifest metadata.
- `cyglobsgl.js` for browser MVP and framebuffer fallback rendering.
- `ai_generation.py` for provider requests, response normalization, output persistence, and feature reporting.
- Python standard-library `urllib`, `json`, `base64`, `pathlib`, and `uuid` for provider transport and file output.

Vendored reference snapshots are available under `vendor/` and are checked against the active directive-packet implementation by `tests/test_vendor_sync.py`.

## Generation controls

The browser studio provides:

- Real AI or CyGlobsGL-only engine selection
- Square, landscape, and portrait aspect ratios
- Low, medium, high, or automatic quality
- PNG, WebP, or JPEG output
- Downloadable provider output
- Automatic CyGlobsGL fallback when the provider is unconfigured or unavailable

## Runtime endpoints

- `POST /rpc` with operation `generate_image`
- `POST /api/generate`
- `GET /api/features`
- `GET /api/health`

## Operational requirements

- Python 3.11 or newer
- Writable `DISCRETE_STORAGE_DIR`
- Provider credentials for real AI generation
- Network access to the configured provider
- No Flask, FastAPI, Uvicorn, Pydantic, SQLAlchemy, or container runtime
