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


def add_cyglobsgl_runtime(source: Path) -> None:
    for name in (
        "cyglobsgl_generation.py",
        "graphics_runtime.py",
        "cyglobsgl.js",
        "cyglobsgl.css",
        "cyglobs_app.py",
    ):
        (source / name).write_text("runtime", encoding="utf-8")
    (source / "cyglobs_framework").mkdir()


def test_dupe_release_copies_code_and_preserves_shared_storage(tmp_path):
    root = tmp_path / "deploy"
    source = root / "releases" / "release-a"
    shared_storage = root / "shared" / "storage"
    source.mkdir(parents=True)
    shared_storage.mkdir(parents=True)
    add_cyglobsgl_runtime(source)
    (source / "app.txt").write_text("immutable release", encoding="utf-8")
    (shared_storage / "generated.png").write_bytes(b"shared-image")
    (source / "storage").symlink_to(shared_storage, target_is_directory=True)

    result = run_dupe(root, "release-a", "release-b")

    assert result.returncode == 0, result.stderr
    target = root / "releases" / "release-b"
    assert (target / "app.txt").read_text(encoding="utf-8") == "immutable release"
    assert (target / "storage").is_symlink()
    assert (target / "storage").resolve() == shared_storage.resolve()
    manifest = json.loads((target / "DUPE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["operation"] == "DUPE"
    assert manifest["source_release"] == "release-a"
    assert manifest["target_release"] == "release-b"
    assert manifest["runtime"] == "CyGlobsGL Python"
    assert manifest["cyglobsgl_injected"] is True
    assert manifest["external_provider"] is False


def test_dupe_release_rejects_missing_cyglobsgl_runtime(tmp_path):
    root = tmp_path / "deploy"
    source = root / "releases" / "release-a"
    source.mkdir(parents=True)

    result = run_dupe(root, "release-a", "release-b")

    assert result.returncode == 5
    assert "CyGlobsGL runtime missing" in result.stderr
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
