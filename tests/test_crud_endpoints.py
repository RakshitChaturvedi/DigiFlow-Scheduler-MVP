import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER ---
def test_create_production_order():
    payload = {
        "order_id_code": "ORD-TEST-API",
        "product_name": "Test Product",
        "product_route_id": "1",
        "quantity_to_produce": 5,
        "priority": 2,
        "arrival_time": "2025-07-01T14:30:00Z",
        "due_date": "2025-07-03T14:30:00Z",
        "current_status": "PENDING"
    }
    response = client.post("/api/orders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["order_id_code"] == payload["order_id_code"]

def test_get_all_production_orders():
    response = client.get("/api/orders/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_production_order():
    create_resp = client.post("/api/orders/", json={
        "order_id_code": "ORD-UPDATE-TEST",
        "product_name": "Initial",
        "product_route_id": "10",
        "quantity_to_produce": 3,
        "priority": 1,
        "arrival_time": "2025-07-01T10:00:00Z",
        "due_date": "2025-07-03T10:00:00Z",
        "current_status": "PENDING"
    })
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/orders/{order_id}", json={"product_name": "UpdatedName"})
    assert update_resp.status_code == 200
    assert update_resp.json()["product_name"] == "UpdatedName"


def test_delete_production_order():
    create_resp = client.post("/api/orders/", json={
        "order_id_code": "ORD-DELETE-TEST",
        "product_name": "Temp",
        "product_route_id": "1",
        "quantity_to_produce": 1,
        "priority": 0,
        "arrival_time": "2025-07-01T00:00:00Z",
        "due_date": "2025-07-02T00:00:00Z",
        "current_status": "PENDING"
    })
    order_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/orders/{order_id}")
    assert delete_resp.status_code == 204

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PROCESS STEPS ---
def test_create_process_step():
    payload = {
        "product_route_id": "999",
        "step_number": 1,
        "step_name": "Test Step",
        "required_machine_type": "Lathe",
        "base_duration_per_unit_mins": 5
    }
    response = client.post("/api/steps/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["product_route_id"] == payload["product_route_id"]
    assert data["step_number"] == payload["step_number"]

def test_get_all_process_steps():
    response = client.get("/api/steps/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_process_step():
    create_resp = client.post("/api/steps/", json={
        "product_route_id": "999",
        "step_number": 2,
        "step_name": "Temp",
        "required_machine_type": "Milling",
        "base_duration_per_unit_mins": 10
    })
    step_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/steps/{step_id}", json={"step_name": "Updated Step"})
    assert update_resp.status_code == 200
    assert update_resp.json()["step_name"] == "Updated Step"

def test_delete_process_step():
    create_resp = client.post("/api/steps/", json={
        "product_route_id": "999",
        "step_number": 3,
        "step_name": "ToDelete",
        "required_machine_type": "Drill",
        "base_duration_per_unit_mins": 15
    })
    step_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/steps/{step_id}")
    assert delete_resp.status_code == 204

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- MACHINES ---
def test_create_machine():
    payload = {
        "machine_id_code": "MCH-TEST-001",
        "machine_type": "Drill",
        "default_setup_time_mins": 10,
        "is_active": True
    }
    response = client.post("/api/machines/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["machine_id_code"] == payload["machine_id_code"]


def test_get_all_machines():
    response = client.get("/api/machines/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_machine():
    create_resp = client.post("/api/machines/", json={
        "machine_id_code": "MCH-TEST-002",
        "machine_type": "Grinder",
        "default_setup_time_mins": 12,
        "is_active": True
    })
    machine_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/machines/{machine_id}", json={"default_setup_time_mins": 20})
    assert update_resp.status_code == 200
    assert update_resp.json()["default_setup_time_mins"] == 20


def test_delete_machine():
    create_resp = client.post("/api/machines/", json={
        "machine_id_code": "MCH-TEST-003",
        "machine_type": "Polish",
        "default_setup_time_mins": 5,
        "is_active": False
    })
    machine_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/machines/{machine_id}")
    assert delete_resp.status_code == 204

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- DOWNTIME EVENTS ---
def test_create_downtime_event():
    # Create a machine first (required foreign key)
    machine_resp = client.post("/api/machines/", json={
        "machine_id_code": "TEST-MACHINE-DT",
        "machine_type": "CNC",
        "default_setup_time_mins": 5,
        "is_active": True
    })
    assert machine_resp.status_code == 201
    machine_id = machine_resp.json()["id"]

    payload = {
        "machine_id": machine_id,
        "start_time": "2025-07-01T08:00:00Z",
        "end_time": "2025-07-01T10:00:00Z",
        "reason": "Test Downtime"
    }
    response = client.post("/api/downtimes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["machine_id"] == payload["machine_id"]
    assert data["reason"] == payload["reason"]


def test_get_all_downtime_events():
    response = client.get("/api/downtimes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_downtime_event():
    # Create a downtime first
    machine_resp = client.post("/api/machines/", json={
        "machine_id_code": "TEMP-MACHINE-UPD",
        "machine_type": "Lathe",
        "default_setup_time_mins": 10,
        "is_active": True
    })
    machine_id = machine_resp.json()["id"]

    create_resp = client.post("/api/downtimes/", json={
        "machine_id": machine_id,
        "start_time": "2025-07-01T12:00:00Z",
        "end_time": "2025-07-01T13:00:00Z",
        "reason": "Initial Reason"
    })
    event_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/downtimes/{event_id}", json={"reason": "Updated Reason"})
    assert update_resp.status_code == 200
    assert update_resp.json()["reason"] == "Updated Reason"


def test_delete_downtime_event():
    machine_resp = client.post("/api/machines/", json={
        "machine_id_code": "MACHINE-DEL-DT",
        "machine_type": "Grinder",
        "default_setup_time_mins": 8,
        "is_active": True
    })
    machine_id = machine_resp.json()["id"]

    create_resp = client.post("/api/downtimes/", json={
        "machine_id": machine_id,
        "start_time": "2025-07-01T14:00:00Z",
        "end_time": "2025-07-01T16:00:00Z",
        "reason": "Temp Delete"
    })
    event_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/downtimes/{event_id}")
    assert delete_resp.status_code == 204
