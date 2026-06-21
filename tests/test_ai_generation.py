import hashlib

from cyglobsgl_generation import GenerationRequest, engine_features, generate_image


def test_generation_request_maps_aspect_and_mode():
    spec = GenerationRequest.from_payload(
        {
            "prompt": "a luminous city",
            "style": "Cinematic",
            "mode": "Triangles",
            "aspect_ratio": "16:9",
            "quality": "high",
            "output_format": "png",
        }
    )
    assert spec.dimensions == (1536, 864)
    assert spec.output_format == "svg"
    assert spec.mode == "Triangles"


def test_cyglobsgl_generation_saves_deterministic_svg(tmp_path):
    payload = {
        "prompt": "a crystal garden",
        "style": "Fantasy",
        "mode": "Wireframe",
        "aspect_ratio": "1:1",
        "quality": "medium",
    }
    first = generate_image(payload, tmp_path)
    second = generate_image(payload, tmp_path)

    first_path = tmp_path / first.image_url.removeprefix("/storage/")
    second_path = tmp_path / second.image_url.removeprefix("/storage/")
    first_bytes = first_path.read_bytes()
    second_bytes = second_path.read_bytes()

    assert first.engine == "cyglobsgl-python"
    assert first.model == "cyglobsgl-procedural-1"
    assert first.output_format == "svg"
    assert first.width == 1024
    assert first.height == 1024
    assert first_bytes == second_bytes
    assert first_bytes.startswith(b"<svg")
    assert first.cyglobsgl["radius"] == 0.62
    assert len(first.cyglobsgl["directive_packet"]) == 16
    assert first.cyglobsgl["byte_length"] == len(first_bytes)
    assert first.cyglobsgl["sha256"] == hashlib.sha256(first_bytes).hexdigest()
    assert "Framebuffer" in first.cyglobsgl["pipeline"]


def test_engine_features_are_local_only():
    features = engine_features()
    assert features["external_provider"] is False
    assert features["network_required"] is False
    assert features["local_generation"] is True
    assert features["cyglobsgl_runtime"] is True
    assert features["supported_formats"] == ["svg"]
