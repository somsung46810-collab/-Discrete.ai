from fastapi.testclient import TestClient

from studio_api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_registration_rejects_short_password():
    response = client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "short", "display_name": "Short"},
    )
    assert response.status_code == 400


def test_creations_list_is_public():
    response = client.get("/api/creations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
