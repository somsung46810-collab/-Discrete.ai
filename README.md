# Discrete.ai

`Commit -> Compile(Clone, File) { R.E.P.L. }`

Discrete.ai is a safe, repository-relative source analysis pipeline. It reads a selected file, validates Python syntax, calculates a SHA-256 digest, renders each byte as hexadecimal plus high/low bit fields, and produces a reviewed commit manifest.

## Install

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

## Safety model

- Repository-relative paths only
- No shell invocation
- No arbitrary expression evaluation
- Explicit commit manifest rather than automatic repository mutation
