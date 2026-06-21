"""Compatibility exports for the CyGlobsGL-only generation engine.

External AI providers were removed. New code should import from
`cyglobsgl_generation` directly.
"""
from cyglobsgl_generation import (
    GenerationRequest,
    GenerationResult,
    engine_features,
    generate_image,
)


def provider_features():
    """Backward-compatible local engine report used by existing HTTP routes."""
    features = engine_features()
    return {
        **features,
        "real_ai_generation": False,
        "provider": "cyglobsgl-python",
        "endpoint": "local",
        "response_field": "local-svg",
        "cyglobsgl_fallback": False,
    }


__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "engine_features",
    "generate_image",
    "provider_features",
]
