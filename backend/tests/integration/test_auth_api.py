"""
Integration tests for Auth API endpoints.
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_register_user(client: TestClient):
    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"


def test_register_duplicate_user(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "strongpassword123",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_login_user(client: TestClient):
    # Register first
    reg_payload = {
        "email": "logintest@example.com",
        "password": "correctpassword",
    }
    client.post("/api/auth/register", json=reg_payload)

    # Valid login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "logintest@example.com", "password": "correctpassword"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Invalid login
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "logintest@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401


def test_get_current_user(client: TestClient, auth_headers: dict[str, str]):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"


def test_protected_route_without_token(client: TestClient):
    response = client.get("/api/documents")
    assert response.status_code == 401
