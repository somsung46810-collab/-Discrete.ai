# Discrete.ai

`Commit -> Compile(Clone, File) { R.E.P.L. }`

Discrete.ai is a safe, repository-relative source analysis pipeline. It reads a selected file, validates Python syntax, calculates a SHA-256 digest, renders each byte as hexadecimal plus high/low bit fields, and produces a reviewed commit manifest.

## Art Studio website

This repository also includes an original procedural-art creation and discovery interface inspired by the broad workflow of modern generative-art platforms, without copying OpenArt branding or proprietary assets.

### Website stack

- **Discrete.ai**: product shell, discovery gallery, and creator workflow
- **CyGlobsGL browser renderer**: local MVP transforms, procedural wireframes, triangle fills, contingency rendering, directive packets, and canvas framebuffer output
- Vanilla HTML, CSS, and JavaScript
- No Flask API, server-side generation endpoint, or Python web dependency

The browser renderer is a JavaScript adaptation of CyGlobsGL concepts. The upstream CyGlobsGL project remains a pure-Python educational software renderer and is not presented as an OpenGL-conformant or GPU-driver-compatible implementation.

### Run the website

Open `index.html` directly, or serve the directory with any static server:

```bash
python -m http.server 5500
```

Then open `http://localhost:5500`.

### Art Studio features

- Browser-local animated Model–View–Projection rendering
- Prompt-seeded deterministic palettes
- Wireframe, filled-triangle, and contingency modes
- Eight-byte hexadecimal directive packets
- Radius constraint of `0.62`
- PNG framebuffer download
- No API calls or backend process

## Install the source-analysis package

```bash
python -m pip install -e '.[dev]'
```

## Use

```python
from discrete_ai import commit_compile, render_result

result = commit_compile(".", "example.py")
print(render_result(result))
```

## Test and validate

```bash
ruff check discrete_ai.py tests
pytest
python -m build
```

## Package contents

- `discrete_ai.py` — runtime implementation
- `tests/test_discrete_ai.py` — automated tests
- `pyproject.toml` — package and development configuration
- `.github/workflows/python-ci.yml` — lint, test, and build automation
- `.github/workflows/project-progress.yml` — weighted completion report
- `SPEC.md` — technical specification
- `STATUS.md` — milestone state
- `index.html`, `styles.css`, `cyglobsgl.css` — Art Studio interface
- `app.js` — studio controls and gallery behavior
- `cyglobsgl.js` — browser-native CyGlobsGL MVP and framebuffer renderer

## Safety model

- Repository-relative paths only
- No shell invocation
- No arbitrary expression evaluation
- Explicit commit manifest rather than automatic repository mutation
- Browser renderer operates locally without uploading prompts or images
