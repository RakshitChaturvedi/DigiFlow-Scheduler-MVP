import pytest
from time import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_order(order_id_code=None, current_status="pending"):
    if order_id_code is None:
        order_id_code = f"ORD-STATUS-{int(time()*1000)}"
    payload = {
        "order_id_code": order_id_code,
        "product_name": "Test Product",
        "product_route_id": f"ROUTE-{order_id_code}",
        "quantity_to_produce": 10,
        "priority": 1,
        "arrival_time": "2025-07-01T08:00:00Z",
        "due_date": "2025-07-05T08:00:00Z",
        "current_status": current_status
    }

    response = client.post("/api/orders/", json=payload)
    assert response.status_code in (200, 201)
    return response.json()["id"]

def test_valid_status_transition():
    order_id = create_order(current_status="pending")

    response = client.patch(
        f"/api/orders/{order_id}/status",
        json={"new_status": "scheduled"}
    )

    assert response.status_code == 200
    assert response.json()["current_status"] == "scheduled"

def test_invalid_status_transition():
    order_id = create_order(current_status="pending")

    response = client.patch(
        f"/api/orders/{order_id}/status",
        json={"new_status": "completed"}
    )

    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["detail"]

def test_status_transition_nonexistent_order():
    response = client.patch(
        "/api/orders/999999/status",
        json={"new_status": "scheduled"}
    )

    assert response.status_code in (404,422)
    assert response.json()["detail"] == "Production order not found"

def test_multiple_status_transitions():
    order_id = create_order(current_status="pending")

    transitions = ["scheduled", "in_progress", "completed"]
    for status in transitions:
        resp = client.patch(f"/api/orders/{order_id}/status", json={"new_status": status})
        assert resp.status_code == 200
        assert resp.json()["current_status"] == status

