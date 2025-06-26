import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.enums import OrderStatus, JobLogStatus

from datetime import datetime, timezone, timedelta
from typing import Optional
import time

client = TestClient(app)

def get_unique_suffix():
    return str(int(time.time() * 1000))

def create_machine_api(machine_code_suffix: str, machine_type: str = "Lathe"):
    machine_id_code = f"MCH-COMPL-{machine_code_suffix}"
    resp = client.post("/api/machines/", json={
        "machine_id_code": machine_id_code,
        "machine_type": machine_type,
        "default_setup_time_mins": 10,
        "is_active": True
    })
    assert resp.status_code in [200, 201], f"Machine creation failed: {resp.text}"
    return resp.json()["id"]

def create_production_order_api(order_id_suffix: str, route_id_suffix: str, quantity: int = 10, current_status: str = "pending"):
    order_id_code = f"ORD-COMPL-{order_id_suffix}"
    product_route_id = f"ROUTE-{route_id_suffix}"
    resp = client.post("/api/orders/", json={
        "order_id_code": order_id_code,
        "product_name": f"Completion Test Product {order_id_suffix}",
        "product_route_id": product_route_id,
        "quantity_to_produce": quantity,
        "priority": 1,
        "arrival_time": datetime.now(timezone.utc).isoformat(),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "current_status": current_status
    })
    assert resp.status_code == 201, f"Production order creation failed: {resp.text}"
    return resp.json() # Return full dict for order_id and product_route_id

def create_process_step_api(route_id: str, step_num: int, step_name: str, required_machine_type: str):
    resp = client.post("/api/steps/", json={
        "product_route_id": route_id,
        "step_number": step_num,
        "step_name": step_name,
        "required_machine_type": required_machine_type,
        "base_duration_per_unit_mins": 30
    })
    assert resp.status_code == 201, f"Process step creation failed: {resp.text}"
    return resp.json()["id"]

def create_job_log_api(order_id: int, step_id: int, machine_id: int, status_val: JobLogStatus = JobLogStatus.PENDING, actual_start: Optional[datetime] = None, actual_end: Optional[datetime] = None, remarks: Optional[str] = None):
    payload = {
        "production_order_id": order_id,
        "process_step_id": step_id,
        "machine_id": machine_id,
        "status": status_val.value
    }
    if actual_start:
        payload["actual_start_time"] = actual_start.isoformat()
    else:
        payload["actual_start_time"] = datetime.now(timezone.utc).isoformat()
    if actual_end:
        payload["actual_end_time"] = actual_end.isoformat()
    if remarks:
        payload["remarks"] = remarks

    resp = client.post("/api/job_logs/", json=payload)
    assert resp.status_code == 201, f"JobLog creation failed: {resp.text}"
    return resp.json()["id"]

def update_job_log_status_api(job_log_id: int, new_status: JobLogStatus):
    resp = client.patch(f"/api/job_logs/{job_log_id}/status", json={"new_status": new_status.value})
    assert resp.status_code == 200, f"JobLog status update failed: {resp.text}"
    return resp.json()

def get_production_order_api(order_id: int):
    resp = client.get(f"/api/orders/{order_id}")
    assert resp.status_code == 200, f"Failed to get production order: {resp.text}"
    return resp.json()

def get_job_log_api(job_log_id: int):
    resp = client.get(f"/api/job_logs/{job_log_id}")
    assert resp.status_code == 200, f"Failed to get job log: {resp.text}"
    return resp.json()

def get_all_job_logs_for_order_api(order_id: int):
    # Assuming you might need to filter job logs by order ID from a general listing
    # If your API has a dedicated endpoint for this, use that.
    all_logs_resp = client.get("/api/job_logs/")
    assert all_logs_resp.status_code == 200
    return [log for log in all_logs_resp.json() if log["production_order_id"] == order_id]


# --- Test Cases for 3.3.3 Automatic Completion Status Updates ---

def test_job_log_completion_sets_end_time_and_checks_order():
    """
    Tests that updating a JobLog to COMPLETED status automatically sets its end_time
    and triggers a check for the parent ProductionOrder's completion.
    """
    test_suffix = get_unique_suffix()

    # Arrange: Create a single-step production order
    machine_id = create_machine_api(f"MCH-JLCOMPL-{test_suffix}", "Lathe")
    order_data = create_production_order_api(
        f"ORD-JLCOMPL-{test_suffix}",
        f"RTE-JLCOMPL-{test_suffix}",
        quantity=1
    )
    order_id = order_data["id"]
    route_id = order_data["product_route_id"]
    step_id = create_process_step_api(route_id, 1, "Step A", "Lathe")

    # Manually update the order status to 'scheduled' to allow JobLog status transitions
    patch_resp = client.patch(f"/api/orders/{order_id}/status", json={"new_status": "scheduled"})
    assert patch_resp.status_code == 200, f"Failed to schedule order: {patch_resp.text}"

    # Create a JobLog with status PENDING (default)
    job_log_id = create_job_log_api(
        order_id,
        step_id,
        machine_id,
        status_val=JobLogStatus.PENDING,
        actual_start=datetime.now(timezone.utc)
    )

    # Transition: PENDING → SCHEDULED → IN_PROGRESS → COMPLETED
    update_job_log_status_api(job_log_id, JobLogStatus.SCHEDULED)
    update_job_log_status_api(job_log_id, JobLogStatus.IN_PROGRESS)
    updated_job_log_response = update_job_log_status_api(job_log_id, JobLogStatus.COMPLETED)

    # Assert: JobLog is COMPLETED and actual_end_time is set
    assert updated_job_log_response["status"] == JobLogStatus.COMPLETED.value
    assert updated_job_log_response["actual_end_time"] is not None

    # Assert: Order should now be COMPLETED as it has one JobLog which is completed
    final_order = get_production_order_api(order_id)
    assert final_order["current_status"] == OrderStatus.COMPLETED.value


def test_production_order_completion_with_multiple_job_logs():
    """
    Tests that a ProductionOrder is marked COMPLETED only when ALL its associated
    JobLogs have reached the COMPLETED status.
    """
    test_suffix = get_unique_suffix() + "_multi"

    # Arrange: Create a production order with two steps/JobLogs
    machine_id_1 = create_machine_api(f"MCH-MULTI-1-{test_suffix}", "Lathe")
    machine_id_2 = create_machine_api(f"MCH-MULTI-2-{test_suffix}", "Milling")
    order_data = create_production_order_api(
        f"ORD-MULTI-{test_suffix}",
        f"RTE-MULTI-{test_suffix}",
        quantity=2
    )
    order_id = order_data["id"]
    route_id = order_data["product_route_id"]

    # Patch status to allow job log transitions
    patch_resp = client.patch(f"/api/orders/{order_id}/status", json={"new_status": "scheduled"})
    assert patch_resp.status_code == 200, f"Failed to schedule order: {patch_resp.text}"

    step_id_1 = create_process_step_api(route_id, 1, "Step Alpha", "Lathe")
    step_id_2 = create_process_step_api(route_id, 2, "Step Beta", "Milling")

    # Create two JobLogs, both initially PENDING
    job_log_id_1 = create_job_log_api(order_id, step_id_1, machine_id_1, status_val=JobLogStatus.PENDING)
    job_log_id_2 = create_job_log_api(order_id, step_id_2, machine_id_2, status_val=JobLogStatus.PENDING)

    # Assert order status is SCHEDULED
    initial_order = get_production_order_api(order_id)
    assert initial_order["current_status"] == OrderStatus.SCHEDULED.value

    # Act 1: Complete first JobLog
    update_job_log_status_api(job_log_id_1, JobLogStatus.SCHEDULED)
    update_job_log_status_api(job_log_id_1, JobLogStatus.IN_PROGRESS)
    update_job_log_status_api(job_log_id_1, JobLogStatus.COMPLETED)

    # Assert intermediate: Order should still be SCHEDULED
    intermediate_order = get_production_order_api(order_id)
    assert intermediate_order["current_status"] == OrderStatus.SCHEDULED.value

    # Act 2: Complete second JobLog
    update_job_log_status_api(job_log_id_2, JobLogStatus.SCHEDULED)
    update_job_log_status_api(job_log_id_2, JobLogStatus.IN_PROGRESS)
    update_job_log_status_api(job_log_id_2, JobLogStatus.COMPLETED)

    # Assert: Order should now be COMPLETED
    final_order = get_production_order_api(order_id)
    assert final_order["current_status"] == OrderStatus.COMPLETED.value



def test_no_completion_if_not_all_job_logs_are_completed():
    """
    Tests that a ProductionOrder does not automatically complete if at least one
    JobLog is not in COMPLETED status.
    """
    test_suffix = get_unique_suffix() + "_partial"

    # Arrange: Create a production order with two steps/JobLogs
    machine_id_1 = create_machine_api(f"MCH-PARTIAL-1-{test_suffix}", "Lathe")
    machine_id_2 = create_machine_api(f"MCH-PARTIAL-2-{test_suffix}", "Milling")
    order_data = create_production_order_api(f"ORD-PARTIAL-{test_suffix}", f"RTE-PARTIAL-{test_suffix}", quantity=2)
    order_id = order_data["id"]
    route_id = order_data["product_route_id"]

    step_id_1 = create_process_step_api(route_id, 1, "Step X", "Lathe")
    step_id_2 = create_process_step_api(route_id, 2, "Step Y", "Milling")

    # Create two JobLogs, one COMPLETED, one still PENDING
    job_log_id_1 = create_job_log_api(order_id, step_id_1, machine_id_1, status_val=JobLogStatus.PENDING)
    update_job_log_status_api(job_log_id_1, JobLogStatus.SCHEDULED)
    print(get_job_log_api(job_log_id_1)["status"])
    update_job_log_status_api(job_log_id_1, JobLogStatus.IN_PROGRESS)
    print(get_job_log_api(job_log_id_1)["status"])
    update_job_log_status_api(job_log_id_1, JobLogStatus.COMPLETED)
    print(get_job_log_api(job_log_id_1)["status"])
    job_log_id_2 = create_job_log_api(order_id, step_id_2, machine_id_2, status_val=JobLogStatus.PENDING)

    # Assert initial order status is PENDING
    initial_order = get_production_order_api(order_id)
    assert initial_order["current_status"] == OrderStatus.PENDING.value

    # Just re-get the order to ensure its status hasn't inadvertently changed
    final_order = get_production_order_api(order_id)
    assert final_order["current_status"] == OrderStatus.PENDING.value
    # Also verify that job_log_2 is indeed still PENDING
    job_log_2_status = get_job_log_api(job_log_id_2)["status"]
    assert job_log_2_status == JobLogStatus.PENDING.value


def test_job_log_completion_does_not_overwrite_manual_end_time():
    """
    Tests that updating a JobLog to COMPLETED status does NOT overwrite
    an already existing actual_end_time.
    """
    test_suffix = get_unique_suffix() + "_manual_end"

    # Arrange: Create a single-step production order
    machine_id = create_machine_api(f"MCH-MANUAL-{test_suffix}", "Lathe")
    order_data = create_production_order_api(
        f"ORD-MANUAL-{test_suffix}",
        f"RTE-MANUAL-{test_suffix}",
        quantity=1
    )
    order_id = order_data["id"]
    route_id = order_data["product_route_id"]
    step_id = create_process_step_api(route_id, 1, "Step Manual End", "Lathe")

    # Patch the ProductionOrder to scheduled so it can be completed later
    patch_resp = client.patch(f"/api/orders/{order_id}/status", json={"new_status": "scheduled"})
    assert patch_resp.status_code == 200, f"Failed to schedule order: {patch_resp.text}"

    # Create a JobLog with a pre-set actual_end_time
    manual_end_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    job_log_id = create_job_log_api(
        order_id,
        step_id,
        machine_id,
        status_val=JobLogStatus.SCHEDULED,  # Valid initial status
        actual_start=datetime.now(timezone.utc) - timedelta(hours=1),
        actual_end=manual_end_time
    )

    # Transition: SCHEDULED → IN_PROGRESS → COMPLETED
    update_job_log_status_api(job_log_id, JobLogStatus.IN_PROGRESS)
    updated_job_log_response = update_job_log_status_api(job_log_id, JobLogStatus.COMPLETED)

    # Assert JobLog is COMPLETED and actual_end_time is preserved
    assert updated_job_log_response["status"] == JobLogStatus.COMPLETED.value
    assert datetime.fromisoformat(updated_job_log_response["actual_end_time"]) == manual_end_time

    final_log = get_job_log_api(job_log_id)
    print("Final job log:", final_log)

    # Assert ProductionOrder is COMPLETED
    final_order = get_production_order_api(order_id)
    assert final_order["current_status"] == OrderStatus.COMPLETED.value
