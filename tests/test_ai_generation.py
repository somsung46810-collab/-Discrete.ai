import base64

from ai_generation import GenerationRequest, generate_image, provider_features


def test_generation_request_maps_aspect_and_prompt():
    spec = GenerationRequest.from_payload(
        {
            "prompt": "a luminous city",
            "style": "Cinematic",
            "mode": "Triangles",
            "aspect_ratio": "16:9",
            "quality": "high",
            "output_format": "webp",
        }
    )
    assert spec.size == "1536x1024"
    assert spec.output_format == "webp"
    assert "Cinematic" in spec.final_prompt


def test_generic_provider_saves_base64_image(monkeypatch, tmp_path):
    monkeypatch.setenv("DISCRETE_IMAGE_PROVIDER", "generic")
    monkeypatch.setenv("DISCRETE_IMAGE_PROVIDER_URL", "https://provider.invalid/generate")
    monkeypatch.setenv("DISCRETE_IMAGE_MODEL", "test-model")

    image_bytes = b"not-a-real-png-but-valid-provider-bytes"

    def fake_post_json(url, token, payload, timeout=180):
        assert payload["size"] == "1024x1024"
        return {"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]}

    monkeypatch.setattr("ai_generation._post_json", fake_post_json)
    result = generate_image(
        {"prompt": "a crystal garden", "output_format": "png"},
        tmp_path,
    )

    assert result.provider == "generic"
    assert result.model == "test-model"
    assert result.image_url.startswith("/storage/ai-")
    saved = tmp_path / result.image_url.removeprefix("/storage/")
    assert saved.read_bytes() == image_bytes


def test_provider_features_reports_fallback(monkeypatch):
    monkeypatch.delenv("DISCRETE_IMAGE_PROVIDER", raising=False)
    monkeypatch.delenv("DISCRETE_IMAGE_PROVIDER_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    features = provider_features()
    assert features["real_ai_generation"] is False
    assert features["cyglobsgl_fallback"] is True
