"""Discrete.ai server powered by CyGlobs-Python-Framework-For-Full-Stack-Developers.

This replaces the removed Flask scaffold with the CyGlobs FastAPI/RPC architecture
while keeping CyGlobsGL rendering in the browser.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
DEFAULT_FRAMEWORK = ROOT.parent / "CyGlobs-Python-Framework-For-Full-Stack-Developers"
FRAMEWORK_ROOT = Path(os.getenv("CYGLOBS_FRAMEWORK_PATH", DEFAULT_FRAMEWORK)).resolve()

if FRAMEWORK_ROOT.exists() and str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_ROOT))

try:
    from framework.comparators import ProtocolComparator
    from framework.config import ServerConfig
    from framework.contingency import FallbackPlanner
    from framework.inverse_ops import InverseOperatorRegistry
    from framework.protocol import RequestEnvelope, ResponseEnvelope
    from framework.services import compare_service, echo_service, health_service
except ImportError as error:  # pragma: no cover - startup configuration guard
    raise RuntimeError(
        "CyGlobs Python Framework was not found. Clone it beside Discrete.ai or "
        "set CYGLOBS_FRAMEWORK_PATH to its repository directory."
    ) from error

config = ServerConfig()
app = FastAPI(title="Discrete.ai + CyGlobs Framework", version="1.0.0")
protocol_comparator = ProtocolComparator(config.protocol_version)
fallback_planner = FallbackPlanner()
operators = InverseOperatorRegistry()

operators.register("echo", echo_service)
operators.register("compare", compare_service)
operators.register("health", health_service)


def render_manifest_service(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a deterministic CyGlobsGL render manifest."""
    prompt = str(payload.get("prompt", "")).strip()
    if len(prompt) < 3:
        raise ValueError("prompt must contain at least 3 characters")

    mode = str(payload.get("mode", "Wireframe"))
    if mode not in {"Wireframe", "Triangles", "Contingency"}:
        raise ValueError("unsupported render mode")

    style = str(payload.get("style", "Cinematic"))
    return {
        "renderer": "CyGlobsGL Browser MVP",
        "prompt": prompt,
        "style": style,
        "mode": mode,
        "radius": 0.62,
        "pipeline": [
            "Sort/Jecht",
            "Translate/Daq",
            "Rotate/MVP",
            "Scale/Cap",
            "Clip Space",
            "Framebuffer",
        ],
    }


operators.register("render_manifest", render_manifest_service)


@app.get("/api/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "Discrete.ai",
        "framework": "CyGlobs-Python-Framework-For-Full-Stack-Developers",
        "renderer": "CyGlobsGL browser framebuffer",
        "protocol_version": config.protocol_version,
    }


@app.post("/rpc", response_model=ResponseEnvelope)
def rpc(request: RequestEnvelope) -> ResponseEnvelope:
    try:
        comparison = protocol_comparator.compare_version(request.protocol_version)
        if not comparison.passed:
            return ResponseEnvelope(
                protocol_version=config.protocol_version,
                status="error",
                error=comparison.reason,
            )

        result = operators.execute(request.operation, request.payload)
        return ResponseEnvelope(
            protocol_version=config.protocol_version,
            status="ok",
            result=result,
        )
    except Exception as error:  # noqa: BLE001 - delegated to framework contingency layer
        fallback = fallback_planner.fallback_response(error)
        return ResponseEnvelope(
            protocol_version=config.protocol_version,
            status=fallback["status"],
            result=fallback["result"],
            error=fallback["error"],
        )


app.mount("/", StaticFiles(directory=ROOT, html=True), name="discrete-art-studio")
