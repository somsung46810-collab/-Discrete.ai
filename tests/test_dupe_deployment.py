from __future__ import annotations

import json
from pathlib import Path
import subprocess


def run_dupe(root: Path, source: str, target: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "dupe_release.sh"
    return subprocess.run(
        ["bash", str(script), str(root), source, target],
        text=True,
        capture_output=True,
        check=False,
    )


def add_cyglobs_runtime(source: Path) -> None:
    for name in (
        "cyglobsgl_generation.py",
        "graphics_runtime.py",
        "cyglobsgl.js",
        "cyglobsgl.css",
        "cyglobs_app.py",
    ):
        (source / name).write_text("runtime", encoding="utf-8")
    package = source / "cyglobs_framework"
    package.mkdir()
    for name in (
        "__init__.py",
        "comparators.py",
        "config.py",
        "contingency.py",
        "inverse_ops.py",
        "protocol.py",
        "services.py",
    ):
        (package / name).write_text("framework", encoding="utf-8")


def test_dupe_release_copies_full_framework_and_preserves_shared_storage(tmp_path):
    root = tmp_path / "deploy"
    source = root / "releases" / "release-a"
    shared_storage = root / "shared" / "storage"
    source.mkdir(parents=True)
    shared_storage.mkdir(parents=True)
    add_cyglobs_runtime(source)
    (source / "app.txt").write_text("immutable release", encoding="utf-8")
    (source / "storage").symlink_to(shared_storage, target_is_directory=True)

    result = run_dupe(root, "release-a", "release-b")

    assert result.returncode == 0, result.stderr
    target = root / "releases" / "release-b"
    assert (target / "app.txt").read_text(encoding="utf-8") == "immutable release"
    assert (target / "storage").resolve() == shared_storage.resolve()
    assert (target / "cyglobs_framework" / "services.py").is_file()
    manifest = json.loads((target / "DUPE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["operation"] == "DUPE_AND_DEDUPE"
    assert manifest["runtime"] == "CyGlobs Python Framework For Full Stack Developers"
    assert manifest["renderer"] == "CyGlobsGL"
    assert manifest["framework_injected"] is True
    assert manifest["cyglobsgl_injected"] is True
    assert manifest["external_provider"] is False
    assert manifest["dedupe_strategy"] == "single canonical active framework package"


def test_dupe_release_rejects_incomplete_framework(tmp_path):
    root = tmp_path / "deploy"
    source = root / "releases" / "release-a"
    source.mkdir(parents=True)
    add_cyglobs_runtime(source)
    (source / "cyglobs_framework" / "services.py").unlink()

    result = run_dupe(root, "release-a", "release-b")

    assert result.returncode == 5
    assert "CyGlobs full-stack runtime missing" in result.stderr
    assert not (root / "releases" / "release-b").exists()


def test_dupe_release_rejects_path_traversal(tmp_path):
    result = run_dupe(tmp_path, "../release-a", "release-b")
    assert result.returncode == 2
    assert "Invalid release id" in result.stderr


def test_dupe_release_does_not_overwrite_existing_target(tmp_path):
    root = tmp_path / "deploy"
    (root / "releases" / "release-a").mkdir(parents=True)
    (root / "releases" / "release-b").mkdir(parents=True)

    result = run_dupe(root, "release-a", "release-b")

    assert result.returncode == 4
    assert "already exists" in result.stderr
