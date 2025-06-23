from fastapi import FastAPI, Depends, HTTPException, status 
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.scheduler import(
    load_and_prepare_data_for_ortools,
    schedule_with_ortools,
    save_scheduled_tasks_to_db
)
from app.schemas import ScheduleRequest, ScheduledTaskResponse, ScheduleOutputResponse

# Configure logging for the main API file
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Use a logger specific to this module

# Initialize the FastAPI application
app = FastAPI(
    title= "Digiflow Scheduler API",
    description= "API for managing and optimizing production schedules.",
    version= "0.1.0"
)

# Define a simple root endpoint
@app.get("/")
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to Digiflow Scheduler API! It's running."}

# Database dependency function
def get_db_session(db: Session = Depends(get_db)):
    """
    Dependency that provides a SQLAlchemy SessionLocal to API routes.
    Ensures the session is properly closed after the request.
    """
    try:
        yield db
    finally:
        db.close()

# Healthcheck 
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# --- Creating Scheduling API Endpoint, Call Scheduler Logic, Handle Output ---
@app.post(
    "/schedule",
    response_model=ScheduleOutputResponse,
    summary="Trigger a new production schedule calculation",
    description="Loads data from the database, runs the OR-Tools scheduler, and saved the optimal schedule back to the database. Returns to scheduling result."
)
async def run_scheduler_api(
    request_data: ScheduleRequest, # Receives the JSON request body, validated by ScheduleRequest Pydantic model
    db: Session = Depends(get_db_session) # Injects the database session
):
    """
    Endpoint to trigger the OR-Tools production scheduler.
    """
    logger.info(f"Received scheduling request (Run ID: {request_data.run_id if request_data.run_id else 'N/A'})...")

    # Determine the real time acnhor for scheduling
    # If client provides start_time_anchor, use it, else, use current UTC time
    current_real_time_anchor = request_data.start_time_anchor if request_data.start_time_anchor else datetime.now(timezone.utc)
    logger.info(f"Scheduling anchor time set to : {current_real_time_anchor.isoformat()}")

    try:
        # 2.4.2 Call Scheduler Logic - Step 1: Load data from the database
        logger.info("Loading and preparing data for OR-Tools scheduler...")
        all_tasks, job_to_tasks, machines_orm, downtime_events = \
            load_and_prepare_data_for_ortools(db, current_real_time_anchor)
        
        if not all_tasks:
            logger.warning("No tasks found to schedule. Returning early.")
            return ScheduleOutputResponse(
                status = "NO_TASKS",
                message="No tasks found in the databse to schedule based on current criteria.",
                scheduled_tasks=[]
            )
        
        # 2.4.2 Call Scheduler Logic - Step 2: Run the OR-Tools Scheduler
        logger.info(f"Running OR-Tools scheduler for {len(all_tasks)} tasks...")
        optimal_schedule_raw, makespan_mins, status_str = \
            schedule_with_ortools(
                all_tasks, 
                job_to_tasks, 
                machines_orm, 
                downtime_events,
                current_real_time_anchor,
                db
            )
        
        # 2.4.2 Call Scheduler Logic - Step 3: Save results to the database if successful
        if optimal_schedule_raw:
            logger.info(f"Scheduler completed with status '{status_str}', Makespan: {makespan_mins / 60:.2f} hours.")
            save_scheduled_tasks_to_db(db, optimal_schedule_raw)
            logger.info("Optimal schedule saved to database.")

            # 2.4.5 Handle Scheduler Output and Return Response
            # Convert raw list of dicts to Pydantic models for response
            scheduled_tasks_response = [
                ScheduledTaskResponse(
                    production_order_id = task['production_order_id'],
                    process_step_id = task['process_step_id'],
                    assigned_machine_id = task['assigned_machine_id'],
                    start_time = task['start_time'],
                    end_time = task['end_time'],
                    scheduled_duration_mins = task['scheduled_duration_mins'],
                    status = task['status'],
                    job_id_code = task['job_id_code'],
                    step_number = task['step_number']
                ) for task in optimal_schedule_raw
            ]

            return ScheduleOutputResponse(
                status=status_str,
                makespan_minutes= makespan_mins,
                scheduled_tasks = scheduled_tasks_response,
                message="Schedule generated and saved successfully."
            )
        else:
            logger.warning(f"Scheduling did not yield a usable plan. Status: {status_str}. No new schedule saved.")
            return ScheduleOutputResponse(
                status=status_str,
                makespan_minutes=makespan_mins,
                scheduled_tasks=[],
                message="Scheduling failed or yielded an infeasible plan. No new schedule saved."
            )
        
    except Exception as e:
        logger.exception(f"An unexpected error occurred during scheduling API call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"An internal server error occured during scheduling: {e}"
        )