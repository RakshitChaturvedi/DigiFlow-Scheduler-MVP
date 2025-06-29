import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from uuid import UUID

REGISTER_URL = "/api/user/register"
LOGING_URL = "/api/user/login"

# --- VALID USER REGISTRATION ---
def test_register_valid_user(client: TestClient):
    payload = {
        "username": "registration_test_1",
        "email": "registration1@example.com",
        "password": "password",
        "full_name": "registration_test_1"
    }

    response = client.post(REGISTER_URL, json=payload)

    assert response.status_code == 201, response.text

    data = response.json()

    assert "id" in data
    assert UUID(data["id"])
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "user"
    assert data["is_active"] is True

# --- DUPLICATE USER REGISTRATION ---
def test_register_existing_user(client: TestClient):
    payload = {
        "username": "registration_test_2",
        "email": "registration2@example.com",
        "password": "password",
        "full_name": "registration_test_2"
    }

    # First attempt
    res1 = client.post(REGISTER_URL, json=payload)
    assert res1.status_code == 201

    # Duplicate attempt
    res2 = client.post(REGISTER_URL, json=payload)
    assert res2.status_code in (400, 409)
    assert "detail" in res2.json()

# --- INVALID PAYLOADS REGISTRATION ---
@pytest.mark.parametrize("payload", [
    {},
    {"username": "registration_test_3"},
    {"email": "bad-email", "password": "12345678"},
    {"username": "abc", "email": "registration_test_4", "password": "short"},
])
def test_register_invalid_payloads(client: TestClient, payload):
    response = client.post(REGISTER_URL, json=payload)
    if response.status_code != 422:
        print("Payload:", payload)
        print("Status:", response.status_code)
        print("Response:", response.json())
    assert response.status_code == 422

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# --- VALID LOGIN TEST --- 
def test_login_valid_user(client: TestClient):
    # First Register a user
    payload = {
        "username": "login_test_1",
        "email": "login1@example.com",
        "password": "password",
        "full_name": "login_test_1"
    }

    res = client.post(REGISTER_URL, json=payload)

    assert res.status_code == 201

    # New Login
    login_payload = {
        "email": payload["email"],
        "password": payload["password"]
    }
    login_res = client.post(LOGING_URL, json=login_payload)

    assert login_res.status_code == 200

    data = login_res.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

# --- INVALID LOGIN TEST ---
@pytest.mark.parametrize("login_payload, exprected_status", [
    ({"email": "login2@example.com", "password": "somepass"}, 401),
    ({"email": "login1@example.com", "password": "wrongpass"}, 401),
    ({"email": "", "password": "pass"}, 422),
    ({"email": "badmail", "password": "pass"}, 422),
    ({"password": "pass"}, 422),
    ({"email": "login1@example.com"}, 422),
])
def test_login_invalid_cases(client: TestClient, login_payload, exprected_status):
    response = client.post(LOGING_URL, json=login_payload)
    assert response.status_code == exprected_status
    