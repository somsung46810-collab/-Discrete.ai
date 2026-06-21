from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cyglobs_framework.comparators import ProtocolComparator
from cyglobs_framework.config import ServerConfig
from cyglobs_framework.contingency import FallbackPlanner
from cyglobs_framework.inverse_ops import InverseOperatorRegistry
from cyglobs_framework.protocol import RequestEnvelope, ResponseEnvelope
from cyglobs_framework.services import compare_service, echo_service, health_service
from graphics_runtime import DEFAULT_RADIUS, Directive, DirectivePacket, Opcode

ROOT = Path(__file__).resolve().parent
config = ServerConfig()
app = FastAPI(title="Discrete.ai CyGlobs")
comparator = ProtocolComparator(config.protocol_version)
fallbacks = FallbackPlanner()
operations = InverseOperatorRegistry()
operations.register("echo", echo_service)
operations.register("compare", compare_service)
operations.register("health", health_service)


def render_manifest(payload):
    prompt = str(payload.get("prompt", "")).strip()
    if len(prompt) < 3:
        raise ValueError("prompt is too short")
    mode = str(payload.get("mode", "Wireframe"))
    if mode not in {"Wireframe", "Triangles", "Contingency"}:
        raise ValueError("unknown render mode")
    packet = DirectivePacket(Directive(Opcode.ROTATE, 7, 0.0, DEFAULT_RADIUS, 0.0))
    return {
        "renderer": "CyGlobsGL",
        "prompt": prompt,
        "mode": mode,
        "radius": DEFAULT_RADIUS,
        "directive_packet": packet.to_hex(),
    }


operations.register("render_manifest", render_manifest)


@app.post("/rpc", response_model=ResponseEnvelope)
def rpc(request: RequestEnvelope):
    try:
        check = comparator.compare_version(request.protocol_version)
        if not check.passed:
            return ResponseEnvelope(status="error", error=check.reason)
        return ResponseEnvelope(status="ok", result=operations.execute(request.operation, request.payload))
    except Exception as error:
        result = fallbacks.fallback_response(error)
        return ResponseEnvelope(status=result["status"], result=result["result"], error=result["error"])


@app.get("/api/status")
def status():
    return {"status": "ok", "framework": "CyGlobs Python", "renderer": "CyGlobsGL"}


app.mount("/", StaticFiles(directory=ROOT, html=True), name="site")
