"""Real image generation adapters for Discrete Art Studio.

The Image API path posts JSON to `/v1/images/generations`, decodes the first
`data[0].b64_json` result, saves it locally, and wraps the saved asset with
CyGlobsGL runtime metadata.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request
from uuid import uuid4

from graphics_runtime import generated_image_asset


OPENAI_IMAGE_ENDPOINT = "https://api.openai.com/v1/images/generations"
SUPPORTED_FORMATS = {"png", "jpeg", "webp"}


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    prompt: str
    style: str = "Cinematic"
    mode: str = "Wireframe"
    aspect_ratio: str = "1:1"
    quality: str = "medium"
    output_format: str = "png"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "GenerationRequest":
        prompt = str(payload.get("prompt", "")).strip()
        if len(prompt) < 3:
            raise ValueError("prompt must contain at least 3 characters")
        aspect_ratio = str(payload.get("aspect_ratio", "1:1")).split()[0]
        if aspect_ratio not in {"1:1", "16:9", "9:16"}:
            raise ValueError("aspect_ratio must be 1:1, 16:9, or 9:16")
        output_format = str(payload.get("output_format", "png")).lower()
        if output_format not in SUPPORTED_FORMATS:
            raise ValueError("output_format must be png, jpeg, or webp")
        quality = str(payload.get("quality", "medium")).lower()
        if quality not in {"low", "medium", "high", "auto"}:
            raise ValueError("quality must be low, medium, high, or auto")
        return cls(
            prompt=prompt,
            style=str(payload.get("style", "Cinematic")),
            mode=str(payload.get("mode", "Wireframe")),
            aspect_ratio=aspect_ratio,
            quality=quality,
            output_format=output_format,
        )

    @property
    def size(self) -> str:
        return {
            "1:1": "1024x1024",
            "16:9": "1536x1024",
            "9:16": "1024x1536",
        }[self.aspect_ratio]

    @property
    def final_prompt(self) -> str:
        return (
            f"{self.prompt}\n"
            f"Art direction: {self.style}. "
            f"Composition guidance: {self.mode}. "
            "Create a finished standalone artwork without interface elements, borders, or watermarks."
        )


@dataclass(frozen=True, slots=True)
class GenerationResult:
    image_url: str
    provider: str
    model: str
    width: int
    height: int
    output_format: str
    revised_prompt: str = ""
    cyglobsgl: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dimensions(size: str) -> tuple[int, int]:
    width, height = size.split("x", 1)
    return int(width), int(height)


def _decode_provider_response(data: dict[str, Any]) -> tuple[bytes | None, str, str]:
    revised_prompt = str(data.get("revised_prompt", ""))
    direct_url = str(data.get("image_url", data.get("url", "")))
    encoded = data.get("b64_json", data.get("image_base64", ""))

    items = data.get("data")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        item = items[0]
        direct_url = str(item.get("url", direct_url))
        encoded = item.get("b64_json", encoded)
        revised_prompt = str(item.get("revised_prompt", revised_prompt))

    if encoded:
        return base64.b64decode(str(encoded), validate=True), "", revised_prompt
    if direct_url:
        return None, direct_url, revised_prompt
    raise ValueError("image provider returned neither image bytes nor an image URL")


def _post_json(url: str, token: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    outgoing = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(outgoing, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"image provider request failed with HTTP {exc.code}: {detail}") from exc


def _save_image(storage: Path, content: bytes, output_format: str) -> str:
    storage.mkdir(parents=True, exist_ok=True)
    suffix = "jpg" if output_format == "jpeg" else output_format
    filename = f"ai-{uuid4().hex}.{suffix}"
    (storage / filename).write_bytes(content)
    return f"/storage/{filename}"


def generate_image(payload: dict[str, Any], storage: Path) -> GenerationResult:
    spec = GenerationRequest.from_payload(payload)
    provider = str(os.getenv("DISCRETE_IMAGE_PROVIDER", "")).strip().lower()
    openai_key = os.getenv("OPENAI_API_KEY", "")
    generic_url = os.getenv("DISCRETE_IMAGE_PROVIDER_URL", "")
    generic_token = os.getenv("DISCRETE_IMAGE_PROVIDER_TOKEN", "")

    if not provider:
        provider = "openai" if openai_key else "generic" if generic_url else ""
    if not provider:
        raise RuntimeError(
            "real AI generation is not configured; set DISCRETE_IMAGE_PROVIDER and provider credentials"
        )

    if provider == "openai":
        if not openai_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI image provider")
        model = os.getenv("DISCRETE_IMAGE_MODEL", "gpt-image-2")
        response = _post_json(
            os.getenv("DISCRETE_IMAGE_PROVIDER_URL", "") or OPENAI_IMAGE_ENDPOINT,
            openai_key,
            {
                "model": model,
                "prompt": spec.final_prompt,
                "size": spec.size,
                "quality": spec.quality,
                "output_format": spec.output_format,
            },
        )
    elif provider == "generic":
        if not generic_url:
            raise RuntimeError("DISCRETE_IMAGE_PROVIDER_URL is required for the generic provider")
        model = os.getenv("DISCRETE_IMAGE_MODEL", "provider-default")
        response = _post_json(
            generic_url,
            generic_token,
            {
                "model": model,
                "prompt": spec.final_prompt,
                "style": spec.style,
                "mode": spec.mode,
                "aspect_ratio": spec.aspect_ratio,
                "size": spec.size,
                "quality": spec.quality,
                "output_format": spec.output_format,
            },
        )
    else:
        raise ValueError(f"unsupported image provider: {provider}")

    content, remote_url, revised_prompt = _decode_provider_response(response)
    image_url = remote_url
    if content is not None:
        image_url = _save_image(storage, content, spec.output_format)

    width, height = _dimensions(spec.size)
    cyglobsgl = generated_image_asset(
        image_url=image_url,
        provider=provider,
        model=model,
        width=width,
        height=height,
        output_format=spec.output_format,
        image_bytes=content,
    ).to_dict()
    return GenerationResult(
        image_url=image_url,
        provider=provider,
        model=model,
        width=width,
        height=height,
        output_format=spec.output_format,
        revised_prompt=revised_prompt,
        cyglobsgl=cyglobsgl,
    )


def provider_features() -> dict[str, Any]:
    provider = str(os.getenv("DISCRETE_IMAGE_PROVIDER", "")).strip().lower()
    configured = bool(
        (provider == "openai" and os.getenv("OPENAI_API_KEY"))
        or (provider == "generic" and os.getenv("DISCRETE_IMAGE_PROVIDER_URL"))
        or (not provider and (os.getenv("OPENAI_API_KEY") or os.getenv("DISCRETE_IMAGE_PROVIDER_URL")))
    )
    return {
        "real_ai_generation": configured,
        "provider": provider or ("openai" if os.getenv("OPENAI_API_KEY") else "generic" if os.getenv("DISCRETE_IMAGE_PROVIDER_URL") else "none"),
        "endpoint": OPENAI_IMAGE_ENDPOINT if provider == "openai" else os.getenv("DISCRETE_IMAGE_PROVIDER_URL", ""),
        "response_field": "data[0].b64_json" if provider == "openai" else "provider-defined",
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "supported_formats": sorted(SUPPORTED_FORMATS),
        "cyglobsgl_runtime": True,
        "cyglobsgl_fallback": True,
    }
