import json
import threading
from urllib import request

from cyglobs_app import (
    create_server,
    decode_token,
    issue_token,
    password_digest,
    render_manifest,
    verify_password,
)
from cyglobs_framework.protocol import RequestEnvelope, ResponseEnvelope


def test_protocol_envelopes_round_trip():
    request_envelope = RequestEnvelope.from_dict(
        {"protocol_version": "1.0", "operation": "health", "payload": {}}
    )
    assert request_envelope.operation == "health"
    response = ResponseEnvelope(status="ok", result={"healthy": True})
    assert response.to_dict()["result"]["healthy"] is True


def test_password_hash_and_token_round_trip():
    encoded = password_digest("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", encoded)
    assert not verify_password("wrong-password", encoded)
    token = issue_token(42)
    assert decode_token(token) == 42


def test_render_manifest_contains_cyglobs_packet():
    result = render_manifest(
        {"prompt": "neon city", "style": "Cinematic", "mode": "Wireframe"}
    )
    assert result["renderer"] == "CyGlobsGL"
    assert result["radius"] == 0.62
    assert len(result["directive_packet"]) == 16


def test_health_endpoint_uses_cyglobs_runtime():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with request.urlopen(f"http://{host}:{port}/api/health", timeout=5) as response:
            body = json.loads(response.read().decode())
        assert body["status"] == "ok"
        assert body["renderer"] == "CyGlobsGL"
        assert "CyGlobs" in body["runtime"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
