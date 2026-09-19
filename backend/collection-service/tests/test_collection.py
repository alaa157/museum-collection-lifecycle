def test_collection_health():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "collection-service"


def test_unauthenticated_collection_request():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/v1/collection/items")

    assert response.status_code == 401
