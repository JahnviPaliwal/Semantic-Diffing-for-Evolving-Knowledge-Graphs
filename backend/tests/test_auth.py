"""Tests for user registration, authentication, and token refresh."""


def test_user_registration_and_login(client):
    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "securepassword123"},
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == "alice@example.com"

    # 2. Login
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "securepassword123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Access protected /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"


def test_duplicate_registration_rejected(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["error"]["message"]


def test_invalid_login_credentials(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_token_refresh(client):
    reg = client.post(
        "/api/auth/register",
        json={"email": "refresh@example.com", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
