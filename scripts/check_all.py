from __future__ import annotations

import compileall
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "dist", "build", "production-dist", "__pycache__"}
TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".css",
    ".html",
    ".md",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".sh",
    ".txt",
}
REQUIRED_FILES = {
    "README.md",
    "STATUS.md",
    "DEPLOYMENT.md",
    "FEATURE_REQUIREMENTS.md",
    "pyproject.toml",
    "index.html",
    "app-ai.js",
    "styles.css",
    "cyglobsgl.js",
    "cyglobs_app.py",
    "ai_generation.py",
    "graphics_runtime.py",
    "scripts/migrate.py",
    "scripts/deploy_remote.sh",
    "scripts/dupe_release.sh",
    ".github/workflows/python-ci.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/dupe-deploy.yml",
}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "Stripe live key": re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
}
PLACEHOLDER_ALLOWLIST = {
    ".env.example",
    "README.md",
    "DEPLOYMENT.md",
    "FEATURE_REQUIREMENTS.md",
}


@dataclass
class Finding:
    level: str
    path: str
    message: str


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.assets.append(values["src"] or "")
        if tag == "link" and values.get("href"):
            self.assets.append(values["href"] or "")


def tracked_files() -> list[Path]:
    git = shutil.which("git")
    if git:
        result = subprocess.run(
            [git, "ls-files", "-z"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in SKIP_PARTS for part in path.parts)
    ]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path, findings: list[Finding]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        findings.append(Finding("error", relative(path), "text file is not valid UTF-8"))
        return None


def check_required(files: set[str], findings: list[Finding]) -> None:
    for required in sorted(REQUIRED_FILES - files):
        findings.append(Finding("error", required, "required production file is missing"))


def check_text_files(paths: Iterable[Path], findings: list[Finding]) -> None:
    for path in paths:
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        text = read_text(path, findings)
        if text is None:
            continue
        name = relative(path)
        if "\x00" in text:
            findings.append(Finding("error", name, "text file contains a NUL byte"))
        if path.stat().st_size > 2_000_000:
            findings.append(Finding("warning", name, "source file exceeds 2 MB"))
        for number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip(" \t") != line:
                findings.append(Finding("warning", name, f"trailing whitespace on line {number}"))
                break
        if name not in PLACEHOLDER_ALLOWLIST:
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    findings.append(Finding("error", name, f"possible committed {label}"))


def check_python(findings: list[Finding]) -> None:
    if not compileall.compile_dir(ROOT, quiet=1, force=True):
        findings.append(Finding("error", "*.py", "Python byte-code compilation failed"))


def check_json(paths: Iterable[Path], findings: list[Finding]) -> None:
    for path in paths:
        if path.suffix.lower() != ".json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("error", relative(path), f"invalid JSON: {exc}"))


def check_toml(paths: Iterable[Path], findings: list[Finding]) -> None:
    for path in paths:
        if path.suffix.lower() != ".toml":
            continue
        try:
            with path.open("rb") as stream:
                tomllib.load(stream)
        except Exception as exc:
            findings.append(Finding("error", relative(path), f"invalid TOML: {exc}"))


def check_html(findings: list[Finding]) -> None:
    index = ROOT / "index.html"
    if not index.exists():
        return
    parser = AssetParser()
    parser.feed(index.read_text(encoding="utf-8"))
    for asset in parser.assets:
        if not asset or asset.startswith(("http://", "https://", "//", "data:")):
            continue
        clean = asset.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        if clean and not (ROOT / clean).is_file():
            findings.append(Finding("error", "index.html", f"referenced asset is missing: {asset}"))


def check_shell(paths: Iterable[Path], findings: list[Finding]) -> None:
    bash = shutil.which("bash")
    if not bash:
        findings.append(Finding("warning", "*.sh", "bash is unavailable; shell syntax was not checked"))
        return
    for path in paths:
        if path.suffix.lower() != ".sh":
            continue
        result = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
        if result.returncode:
            findings.append(
                Finding("error", relative(path), f"shell syntax error: {result.stderr.strip()}")
            )


def check_javascript(paths: Iterable[Path], findings: list[Finding]) -> None:
    node = shutil.which("node")
    if not node:
        findings.append(Finding("warning", "*.js", "Node.js is unavailable; JavaScript syntax was not checked"))
        return
    for path in paths:
        if path.suffix.lower() != ".js":
            continue
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            findings.append(
                Finding("error", relative(path), f"JavaScript syntax error: {result.stderr.strip()}")
            )


def check_workflows(paths: Iterable[Path], findings: list[Finding]) -> None:
    workflow_paths = [
        path for path in paths if relative(path).startswith(".github/workflows/")
    ]
    for path in workflow_paths:
        text = read_text(path, findings)
        if text is None:
            continue
        name = relative(path)
        for required in ("name:", "on:", "jobs:"):
            if required not in text:
                findings.append(Finding("error", name, f"workflow is missing `{required}`"))
        if "uses: actions/checkout@" in text and "permissions:" not in text:
            findings.append(Finding("warning", name, "workflow does not declare explicit permissions"))


def check_package_metadata(findings: list[Finding]) -> None:
    path = ROOT / "pyproject.toml"
    if not path.exists():
        return
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    project = data.get("project", {})
    for key in ("name", "version", "requires-python"):
        if not project.get(key):
            findings.append(Finding("error", "pyproject.toml", f"project.{key} is missing"))
    scripts = project.get("scripts", {})
    if "discrete-art-studio" not in scripts:
        findings.append(Finding("error", "pyproject.toml", "application CLI entrypoint is missing"))


def print_report(paths: list[Path], findings: list[Finding]) -> int:
    errors = [item for item in findings if item.level == "error"]
    warnings = [item for item in findings if item.level == "warning"]
    print("Discrete.ai repository checkup")
    print(f"Files checked: {len(paths)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    for item in findings:
        print(f"[{item.level.upper()}] {item.path}: {item.message}")
    if errors:
        print("CHECKUP RESULT: FAILED")
        return 1
    print("CHECKUP RESULT: PASSED")
    return 0


def main() -> int:
    paths = tracked_files()
    file_names = {relative(path) for path in paths}
    findings: list[Finding] = []
    check_required(file_names, findings)
    check_text_files(paths, findings)
    check_python(findings)
    check_json(paths, findings)
    check_toml(paths, findings)
    check_html(findings)
    check_shell(paths, findings)
    check_javascript(paths, findings)
    check_workflows(paths, findings)
    check_package_metadata(findings)
    return print_report(paths, findings)


if __name__ == "__main__":
    sys.exit(main())
