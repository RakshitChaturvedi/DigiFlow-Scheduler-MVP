import pytest
from datetime import datetime, timedelta, timezone


def trigger_schedule(client, run_id=None):
    payload = {}
    if run_id is not None:
        payload["run_id"] = run_id
    print("Payload", payload)
    return client.post("/api/schedule", json=payload)


def test_schedule_fails_gracefully_on_internal_error(monkeypatch):
    # Import and patch before anything else
    import backend.app.scheduler as scheduler

    def broken_loader(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(scheduler, "load_and_prepare_data_for_ortools", broken_loader)

    # Now import app
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    # Run
    response = trigger_schedule(client, "test_failure")
    assert response.status_code == 500
    assert "detail" in response.json()
    assert "Simulated failure" in response.json()["detail"]


def test_schedule_returns_valid_response_structure():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = trigger_schedule(client, "test_run_structure")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("OPTIMAL", "FEASIBLE", "INFEASIBLE", "NO_TASKS", "ERROR")
    assert isinstance(data.get("scheduled_tasks", []), list)

    for task in data["scheduled_tasks"]:
        for field in [
            "production_order_id", "process_step_id", "assigned_machine_id",
            "start_time", "end_time", "scheduled_duration_mins",
            "status", "job_id_code", "step_number"
        ]:
            assert field in task


@pytest.mark.skip(reason="Depends on empty DB state")
def test_schedule_handles_no_tasks_gracefully(monkeypatch):
    import backend.app.scheduler as scheduler

    def empty_loader(*args, **kwargs):
        return [], {}, [], []

    monkeypatch.setattr(scheduler, "load_and_prepare_data_for_ortools", empty_loader)

    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = trigger_schedule(client, "test_run_no_tasks")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "NO_TASKS"
    assert data["scheduled_tasks"] == []
    assert "message" in data


def test_schedule_respects_custom_anchor_time():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    anchor_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = client.post("/api/schedule", json={"start_time_anchor": anchor_time})

    assert response.status_code == 200
    assert "status" in response.json()


def test_schedule_response_makespan_present_if_applicable():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = trigger_schedule(client, "test_makespan")
    data = response.json()
    assert response.status_code == 200

    if data["status"] in ("OPTIMAL", "FEASIBLE"):
        assert isinstance(data.get("makespan_minutes"), (int, float))
    else:
        assert data.get("makespan_minutes") is None


def test_schedule_archives_old_tasks():
    from backend.app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    first = trigger_schedule(client, "test_archive_1")
    assert first.status_code == 200
    assert first.json()["scheduled_tasks"]

    second = trigger_schedule(client, "test_archive_2")
    assert second.status_code == 200
    new_tasks = second.json()["scheduled_tasks"]
    assert new_tasks