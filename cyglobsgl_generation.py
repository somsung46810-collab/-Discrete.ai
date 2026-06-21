"""CyGlobsGL-only procedural artwork generation for Discrete Art Studio."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import html
import math
from pathlib import Path
import random
from typing import Any
from uuid import uuid4

from graphics_runtime import generated_image_asset

SUPPORTED_FORMATS = {"svg"}


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    prompt: str
    style: str = "Cinematic"
    mode: str = "Wireframe"
    aspect_ratio: str = "1:1"
    quality: str = "medium"
    output_format: str = "svg"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "GenerationRequest":
        prompt = str(payload.get("prompt", "")).strip()
        if len(prompt) < 3:
            raise ValueError("prompt must contain at least 3 characters")
        aspect_ratio = str(payload.get("aspect_ratio", "1:1")).split()[0]
        if aspect_ratio not in {"1:1", "16:9", "9:16"}:
            raise ValueError("aspect_ratio must be 1:1, 16:9, or 9:16")
        mode = str(payload.get("mode", "Wireframe"))
        if mode not in {"Wireframe", "Triangles", "Contingency"}:
            raise ValueError("unsupported CyGlobsGL mode")
        return cls(
            prompt=prompt,
            style=str(payload.get("style", "Cinematic")),
            mode=mode,
            aspect_ratio=aspect_ratio,
            quality=str(payload.get("quality", "medium")),
            output_format="svg",
        )

    @property
    def dimensions(self) -> tuple[int, int]:
        return {
            "1:1": (1024, 1024),
            "16:9": (1536, 864),
            "9:16": (864, 1536),
        }[self.aspect_ratio]


@dataclass(frozen=True, slots=True)
class GenerationResult:
    image_url: str
    engine: str
    model: str
    width: int
    height: int
    output_format: str
    cyglobsgl: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _palette(seed: int) -> tuple[str, str, str, str]:
    palettes = (
        ("#09031f", "#5b2cff", "#36d9ff", "#ff5bc8"),
        ("#071a19", "#00a884", "#8effd4", "#ffc857"),
        ("#1a0810", "#ff5a5f", "#ffca3a", "#8ac926"),
        ("#07111f", "#1b6ca8", "#5ce1e6", "#d6f6ff"),
    )
    return palettes[seed % len(palettes)]


def _points(rng: random.Random, width: int, height: int, count: int) -> list[tuple[float, float]]:
    margin = min(width, height) * 0.08
    return [
        (rng.uniform(margin, width - margin), rng.uniform(margin, height - margin))
        for _ in range(count)
    ]


def _wireframe(points: list[tuple[float, float]], stroke: str) -> str:
    items: list[str] = []
    for index, (x1, y1) in enumerate(points):
        for offset in (1, 3, 7):
            x2, y2 = points[(index + offset) % len(points)]
            items.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{stroke}" stroke-opacity="0.28" stroke-width="2"/>'
            )
    return "".join(items)


def _triangles(points: list[tuple[float, float]], colors: tuple[str, ...]) -> str:
    items: list[str] = []
    for index in range(0, len(points) - 2, 3):
        triangle = points[index : index + 3]
        coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in triangle)
        color = colors[index % len(colors)]
        items.append(
            f'<polygon points="{coords}" fill="{color}" fill-opacity="0.22" '
            f'stroke="{color}" stroke-opacity="0.75" stroke-width="2"/>'
        )
    return "".join(items)


def _contingency(points: list[tuple[float, float]], color: str) -> str:
    items: list[str] = []
    for index, (x, y) in enumerate(points):
        radius = 10 + (index % 5) * 5
        dash = "8 8" if index % 2 else "3 7"
        items.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-dasharray="{dash}" opacity="0.7"/>'
        )
    return "".join(items)


def _render_svg(spec: GenerationRequest) -> bytes:
    width, height = spec.dimensions
    digest = hashlib.sha256(
        f"{spec.prompt}|{spec.style}|{spec.mode}|{spec.aspect_ratio}|{spec.quality}".encode()
    ).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = random.Random(seed)
    background, primary, secondary, accent = _palette(seed)
    count = {"low": 18, "medium": 30, "high": 48, "auto": 30}.get(spec.quality, 30)
    points = _points(rng, width, height, count)
    if spec.mode == "Triangles":
        geometry = _triangles(points, (primary, secondary, accent))
    elif spec.mode == "Contingency":
        geometry = _contingency(points, accent) + _wireframe(points, secondary)
    else:
        geometry = _wireframe(points, secondary)

    rings = []
    cx, cy = width / 2, height / 2
    for index in range(9):
        radius = min(width, height) * (0.08 + index * 0.055)
        rotation = (seed % 360) + index * 17
        rings.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{radius:.1f}" ry="{radius * 0.62:.1f}" '
            f'transform="rotate({rotation} {cx:.1f} {cy:.1f})" fill="none" '
            f'stroke="{primary if index % 2 == 0 else accent}" stroke-opacity="{0.5 - index * 0.035:.3f}" '
            f'stroke-width="{max(1, 5 - index * 0.35):.2f}"/>'
        )

    title = html.escape(spec.prompt[:96])
    subtitle = html.escape(f"CyGlobsGL Python Framework • {spec.style} • {spec.mode}")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
  <radialGradient id="bg"><stop offset="0" stop-color="{primary}" stop-opacity="0.35"/><stop offset="1" stop-color="{background}"/></radialGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="100%" height="100%" fill="url(#bg)"/>
<g opacity="0.95">{geometry}</g>
<g filter="url(#glow)">{''.join(rings)}</g>
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{min(width, height) * 0.055:.1f}" fill="{secondary}" fill-opacity="0.9"/>
<text x="{width * 0.06:.1f}" y="{height * 0.89:.1f}" fill="#ffffff" font-family="Inter,Arial,sans-serif" font-size="{max(24, width * 0.027):.1f}" font-weight="700">{title}</text>
<text x="{width * 0.06:.1f}" y="{height * 0.935:.1f}" fill="#ffffff" fill-opacity="0.72" font-family="Inter,Arial,sans-serif" font-size="{max(14, width * 0.014):.1f}">{subtitle}</text>
</svg>'''
    return svg.encode("utf-8")


def generate_image(payload: dict[str, Any], storage: Path) -> GenerationResult:
    spec = GenerationRequest.from_payload(payload)
    content = _render_svg(spec)
    storage.mkdir(parents=True, exist_ok=True)
    filename = f"cyglobsgl-{uuid4().hex}.svg"
    (storage / filename).write_bytes(content)
    image_url = f"/storage/{filename}"
    width, height = spec.dimensions
    metadata = generated_image_asset(
        image_url=image_url,
        provider="cyglobsgl-python",
        model="cyglobsgl-procedural-1",
        width=width,
        height=height,
        output_format="svg",
        image_bytes=content,
    ).to_dict()
    return GenerationResult(
        image_url=image_url,
        engine="cyglobsgl-python",
        model="cyglobsgl-procedural-1",
        width=width,
        height=height,
        output_format="svg",
        cyglobsgl=metadata,
    )


def engine_features() -> dict[str, Any]:
    return {
        "external_provider": False,
        "network_required": False,
        "engine": "cyglobsgl-python",
        "model": "cyglobsgl-procedural-1",
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "supported_formats": ["svg"],
        "cyglobsgl_runtime": True,
        "local_generation": True,
    }
