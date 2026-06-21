# Discrete.ai

`Commit -> Compile(Clone, File) { R.E.P.L. }`

Discrete.ai is a safe, repository-relative source analysis pipeline. It reads a selected file, validates Python syntax, calculates a SHA-256 digest, renders each byte as hexadecimal plus high/low bit fields, and produces a reviewed commit manifest.

## Art Studio website

This repository now also includes an original AI-art creation and discovery interface inspired by the broad workflow of modern generative-art platforms, without copying OpenArt branding or proprietary assets.

### Website stack

- **Discrete.ai**: product shell, discovery gallery, and creator workflow
- **CyGlobsGL**: intended real-time preview/render integration
- **CyGlobs Python Framework**: intended backend orchestration and generation API
- Vanilla HTML, CSS, and JavaScript for the zero-build frontend
- Flask API scaffold

### Run the website

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000`.

Replace `CyGlobsAdapter.generate()` in `app.py` with the concrete CyGlobs-Python-Framework job runner and connect CyGlobsGL in `app.js` for interactive shader and 3D previews.

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
- `tests/test_discrete_ai.py` — automated test suite
- `pyproject.toml` — package and development configuration
- `.github/workflows/python-ci.yml` — lint, test, and build workflow
- `.github/workflows/project-progress.yml` — weighted completion report
- `SPEC.md` — technical specification
- `STATUS.md` — milestone state
- `index.html`, `styles.css`, `app.js` — Art Studio frontend
- `app.py` — Flask API and CyGlobs adapter scaffold

## Safety model

- Repository-relative paths only
- No shell invocation
- No arbitrary expression evaluation
- Explicit commit manifest rather than automatic repository mutation
