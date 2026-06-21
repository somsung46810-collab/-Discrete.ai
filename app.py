"""Discrete.ai API scaffold powered by the CyGlobs Python integration layer."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).parent
app = Flask(__name__, static_folder=str(ROOT), static_url_path="")

@dataclass
class GenerationRequest:
    prompt: str
    engine: Literal["discrete-fusion", "cyglobsgl", "cyglobs-python"] = "discrete-fusion"
    aspect_ratio: str = "1:1"
    style: str = "cinematic"
    count: int = 1

class CyGlobsAdapter:
    """Replace this deterministic placeholder with the real CyGlobs pipeline."""
    def generate(self, job: GenerationRequest) -> dict:
        return {
            "status": "queued",
            "engine": job.engine,
            "request": asdict(job),
            "outputs": [f"/generated/demo-{i + 1}.png" for i in range(job.count)],
        }

renderer = CyGlobsAdapter()

@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")

@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get("prompt", "")).strip()
    if len(prompt) < 3:
        return jsonify({"error": "Prompt must contain at least 3 characters."}), 400
    count = max(1, min(int(payload.get("count", 1)), 4))
    job = GenerationRequest(
        prompt=prompt,
        engine=payload.get("engine", "discrete-fusion"),
        aspect_ratio=payload.get("aspect_ratio", "1:1"),
        style=payload.get("style", "cinematic"),
        count=count,
    )
    return jsonify(renderer.generate(job)), 202

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "discrete-art-studio"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
