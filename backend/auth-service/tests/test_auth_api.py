def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_invalid_login(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.local",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_returns_tokens(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.local",
            "password": "AdminPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_refresh_rotates_refresh_token(client, admin_user):
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.local",
            "password": "AdminPassword123!",
        },
    )

    original_refresh = login.json()["refresh_token"]

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh},
    )

    assert refresh.status_code == 200
    assert refresh.json()["refresh_token"] != original_refresh

    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh},
    )

    assert reuse.status_code == 401


def test_authenticated_me(client, admin_user):
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.local",
            "password": "AdminPassword123!",
        },
    )

    access_token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.local"
