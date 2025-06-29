import pytest
from datetime import timedelta

from backend.app.utils import create_access_token
from backend.app.models import User
from backend.app.crud import create_user
from backend.app.schemas import UserCreate
from uuid import uuid4

MACHINE_URL = "/api/machines"

# IMPORTANT FIXTURES
@pytest.fixture
def expired_token():
    return create_access_token("expired@example.com", role="user", expires_delta=timedelta(seconds=-1))

@pytest.fixture
def admin_token(db_session):
    user_data = UserCreate(
        username="adminuser",
        email = "admin@example.com",
        password="adminpassword",
        full_name="Admin User",
        is_superuser= True,
        is_active= True,
        role = "admin"
    )
    user = create_user(db_session, user_data)
    return create_access_token(subject=user.email, role= user.role)

@pytest.fixture
def user_token(db_session):
    user_data = UserCreate(
        username="regularuser",
        email="user@example.com",
        password="userpassword",
        full_name="Regular User",
        is_superuser=False,
        is_active=True,
        role="user"
    )
    user = create_user(db_session, user_data)
    return create_access_token(subject= user.email, role= user.role)

@pytest.fixture
def sample_machine_payload():
    return{
        "machine_id_code": "M016",
        "machine_type": "Manual Lathe",
        "default_setup_time_mins": 35,
        "is_active": True
    }

# --- TOKEN AUTHORIZATION TESTS ---


def test_access_with_valid_token(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(MACHINE_URL, headers=headers)

    assert response.status_code == 200

def test_access_without_token(client):
    response = client.get(MACHINE_URL)
    assert response.status_code == 401

def test_access_with_invalid_token(client):
    headers = {"Authorization": "Bearer faketoken123"}
    response = client.get(MACHINE_URL, headers= headers)
    assert response.status_code == 403

def test_access_with_expired_token(client, expired_token):
    headers= {"Authorization": f"Bearer {expired_token}"}
    response = client.get(MACHINE_URL, headers= headers)
    assert response.status_code == 401

# --- ROLE ACCESS TEST ---
def test_admin_can_create_machine(client, admin_token, sample_machine_payload):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(MACHINE_URL, json=sample_machine_payload, headers=headers)
    assert response.status_code == 201

def test_user_cannot_create_machine(client, user_token, sample_machine_payload):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post(MACHINE_URL, json = sample_machine_payload, headers= headers)
    assert response.status_code == 403

def test_user_can_read_machines(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get(MACHINE_URL, headers=headers)
    assert response.status_code == 200

def test_user_cannot_update_machine(client, user_token, sample_machine_payload):
    headers_admin = {"Authorization": f"Bearer {user_token}"}
    response = client.put(f"{MACHINE_URL}/some-id", json={"name": "UpdateName"}, headers=headers_admin)
    assert response.status_code == 403