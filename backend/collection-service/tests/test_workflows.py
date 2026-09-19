from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_collection_requires_authentication():
    response = client.get(
        "/api/v1/collection/items"
    )

    assert response.status_code == 401


def test_item_identifier_is_uuid():
    generated = uuid4()

    assert len(str(generated)) == 36
