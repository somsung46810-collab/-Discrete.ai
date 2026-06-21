from pathlib import Path

import pytest

from discrete_ai import commit_compile, evaluate_source, pack_bit_fields, render_result


def test_pack_bit_fields() -> None:
    assert pack_bit_fields(bytes([0xAF])) == "af[1010|1111]"


def test_evaluate_source_reports_valid_syntax() -> None:
    result = evaluate_source("value = 7\n")
    assert result["syntax"] == "valid"
    assert result["ast_nodes"] > 0


def test_commit_compile_builds_manifest(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("value = 7\n", encoding="utf-8")

    result = commit_compile(tmp_path, "sample.py")

    assert result.file == "sample.py"
    assert len(result.sha256) == 64
    assert result.commit_manifest["path"] == "sample.py"
    assert "Compile and validate" in result.commit_manifest["message"]
    assert '"syntax": "valid"' in render_result(result)


def test_commit_compile_rejects_escape_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        commit_compile(tmp_path, "../outside.py")


def test_invalid_python_raises_syntax_error() -> None:
    with pytest.raises(SyntaxError):
        evaluate_source("def broken(:\n")
