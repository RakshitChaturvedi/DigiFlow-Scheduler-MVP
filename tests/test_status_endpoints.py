import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_order(order_id_code="ORD-STATUS-TEST", current_status="Pending"):
    payload = {
        "order_id_code": order_id_code,
        "product_name": "Test Product",
        "product_route_id": "123",
        "quantity_to_produce": 10,
        "priority": 1,
        "arrival_time": "2025-07-01T08:00:00Z",
        "due_date": "2025-07-05T08:00:00Z",
        "current_status": current_status
    }
    response = client.post("/api/orders/", json=payload)
    assert response.status_code == 201 or response.status_code == 200
    return response.json()["id"]

def test_valid_status_transition():
    order_id = create_order("ORD-VALID-TEST", current_status="Pending")

    response = client.patch(
        f"/api/orders/{order_id}/status",
        json={"new_status": "Scheduled"}
    )

    assert response.status_code == 200
    assert response.json()["current_status"] == "Scheduled"

def test_invalid_status_transition():
    order_id = create_order("ORD-INVALID-TEST", current_status="Pending")

    response = client.patch(
        f"/api/orders/{order_id}/status",
        json={"new_status": "Completed"}
    )

    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["detail"]

def test_status_transition_nonexistent_order():
    response = client.patch(
        "/api/orders/999999/status",
        json={"new_status": "Scheduled"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Production order not found"

def test_multiple_status_transitions():
    order_id = create_order("ORD-CHAIN-TEST", current_status="Pending")

    transitions = ["Scheduled", "In Progress", "Completed"]
    for status in transitions:
        resp = client.patch(f"/api/orders/{order_id}/status", json={"new_status": status})
        assert resp.status_code == 200
        assert resp.json()["current_status"] == status

