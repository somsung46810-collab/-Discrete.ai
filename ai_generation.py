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
    """Backward-compatible alias for the local CyGlobsGL feature report."""
    return engine_features()


__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "engine_features",
    "generate_image",
    "provider_features",
]
