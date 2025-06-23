from app.database import SessionLocal
from app.scheduler import (
    load_and_prepare_data_for_ortools,
    schedule_with_ortools,
    save_scheduled_tasks_to_db
)
from datetime import datetime

def run_scheduler_on_real_db():
    db = SessionLocal()
    anchor_time = datetime.now()

    try:
        all_tasks, job_map, machines, downtimes = load_and_prepare_data_for_ortools(
            db=db,
            scheduling_anchor_time=anchor_time
        )

        if not all_tasks:
            print("No tasks to schedule.")
            return
        
        print(f"Loaded {len(all_tasks)} tasks for scheduling.")
        scheduled_tasks, makespan, status = schedule_with_ortools(
            tasks=all_tasks,
            jobs_map=job_map,
            machines_orm=machines,
            downtime_events=downtimes,
            scheduling_anchor_time=anchor_time,
            db_session=db,
            horizon=10080
        )

        print(f"Solver status: {status}, Makespan: {makespan / 60:.2f} hrs")

        if scheduled_tasks:
            save_scheduled_tasks_to_db(db, scheduled_tasks)
            print(f"Saved {len(scheduled_tasks)} tasks to DB.")
        else:
            print("No feasible schedule found.")

    finally:
        db.close()

if __name__ == "__main__":
    run_scheduler_on_real_db()
