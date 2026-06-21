from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "production-dist"
STAGE = OUTPUT / "discrete-art-studio"

INCLUDE_FILES = [
    ".env.example",
    "DEPLOYMENT.md",
    "FEATURE_REQUIREMENTS.md",
    "README.md",
    "STATUS.md",
    "THIRD_PARTY_NOTICES.md",
    "ai_generation.py",
    "app-ai.js",
    "cyglobs_app.py",
    "cyglobsgl.css",
    "cyglobsgl.js",
    "discrete_ai.py",
    "graphics_runtime.py",
    "index.html",
    "pyproject.toml",
    "requirements.txt",
    "studio_api.py",
    "styles.css",
]

INCLUDE_DIRS = [
    "cyglobs_framework",
    "scripts",
    "vendor",
]


def copy_source() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    STAGE.mkdir(parents=True)

    for relative in INCLUDE_FILES:
        source = ROOT / relative
        if source.exists():
            destination = STAGE / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    for relative in INCLUDE_DIRS:
        source = ROOT / relative
        if source.exists():
            shutil.copytree(
                source,
                STAGE / relative,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )


def build_python_distributions() -> None:
    subprocess.run(
        ["python", "-m", "build", "--outdir", str(OUTPUT / "python")],
        cwd=ROOT,
        check=True,
    )


def write_manifest() -> None:
    files = []
    for path in sorted(STAGE.rglob("*")):
        if not path.is_file():
            continue
        content = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(STAGE).as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = {
        "name": "Discrete Art Studio",
        "package": "discrete-ai",
        "entrypoint": "python -m cyglobs_app",
        "health_endpoint": "/api/health",
        "python": ">=3.11",
        "files": files,
    }
    (STAGE / "production-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def create_archives() -> None:
    zip_path = OUTPUT / "discrete-art-studio-production.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(STAGE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OUTPUT))

    tar_path = OUTPUT / "discrete-art-studio-production.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(STAGE, arcname=STAGE.name)

    checksum_lines = []
    for path in sorted(OUTPUT.glob("*")):
        if path.is_file():
            checksum_lines.append(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
            )
    (OUTPUT / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n")


def main() -> None:
    copy_source()
    write_manifest()
    build_python_distributions()
    create_archives()
    print(f"Production package created in {OUTPUT}")


if __name__ == "__main__":
    main()
