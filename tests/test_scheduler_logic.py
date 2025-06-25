import pytest
from datetime import datetime, timezone
from collections import defaultdict

from backend.app.database import SessionLocal
from backend.app.scheduler import schedule_with_ortools, load_and_prepare_data_for_ortools

def check_sequence_validity(scheduled_tasks):
    errors = []
    po_steps = defaultdict(list)

    for task in scheduled_tasks:
        po_steps[task["production_order_id"]].append(task)

    for po_id, steps in po_steps.items():
        sorted_steps = sorted(steps, key = lambda x: x["step_number"])
        for i in range(1, len(sorted_steps)):
            prev, curr = sorted_steps[i-1], sorted_steps[i]
            if curr["start_time"] < prev["start_time"]:
                errors.append(
                    f"[SEQUENCE ERROR] PO {po_id}: Step {curr['step_number']} starts at {curr['start_time']} before previous step ends at {prev['end_time']}"
                )
    return errors


def check_machine_conflicts(scheduled_tasks):
    errors= []
    machine_tasks = defaultdict(list)

    for task in scheduled_tasks:
        machine_tasks[task["assigned_machine_id"]].append(task)

    for machine_id, tasks in machine_tasks.items():
        sorted_tasks = sorted(tasks, key=lambda x: x["start_time"])
        for i in range(1, len(sorted_tasks)):
            prev, curr = sorted_tasks[i-1], sorted_tasks[i]
            if curr["start_time"] < prev["end_time"]:
                errors.append(
                    f"[MACHINE CONFLICT] Machine {machine_id}: Task at {curr['start_time']} overlaps with previous ending at {prev['end_time']}"
                )
    return errors

@pytest.fixture(scope="module")
def scheduler_output():
    db = SessionLocal()
    anchor = datetime.now(timezone.utc)
    tasks, job_map, machines, downtimes = load_and_prepare_data_for_ortools(db, anchor)
    scheduled, makespan, status = schedule_with_ortools(tasks, job_map, machines, downtimes, anchor, db)
    db.close()
    return scheduled, status

def test_scheduler_sequence_respected(scheduler_output):
    scheduled, status = scheduler_output
    assert scheduled, "Scheduler did not return any scheduled tasks."
    sequence_errors = check_sequence_validity(scheduled)
    assert not sequence_errors, f"Sequence validation failed: {sequence_errors}"

def test_scheduler_no_machine_overlap(scheduler_output):
    scheduled, status = scheduler_output
    assert scheduled, "Scheduler did not return any scheduled tasks."
    overlap_errors = check_machine_conflicts(scheduled)
    assert not overlap_errors, f"Machine conflict validation failed: {overlap_errors}"