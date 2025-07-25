import logging
import warnings
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.openapi.models import OAuthFlow as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.middleware.cors import CORSMiddleware

from typing import List

from backend.app import crud
from backend.app.database import get_db
from backend.app.models import ProductionOrder, JobLog, ScheduledTask
from backend.app.scheduler import(
    load_and_prepare_data_for_ortools,
    schedule_with_ortools,
    save_scheduled_tasks_to_db)
from backend.app.schemas import (ScheduleRequest, 
                                 ScheduledTaskResponse, 
                                 ScheduleOutputResponse,
                                 ProductionOrderOut,
                                 JobLogOut,
                                 ProductionOrderStatusUpdate,
                                 JobLogStatusUpdate)
from backend.app.routes import router as crud_router
from backend.app.utils import ensure_utc_aware
from backend.app.routes import operator_router, task_action_router

# Configure logging for the main API file
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Use a logger specific to this module

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Initialize the FastAPI application
app = FastAPI(
    title= "Digiflow Scheduler API",
    description= "API for managing and optimizing production schedules.",
    version= "0.1.0"
)

app.include_router(crud_router)
app.include_router(operator_router)
app.include_router(task_action_router)

# Define the list of origins that are allowed to make requests.
origins = [
    'http://localhost:5173',
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    'http://localhost:5173/login',
    'http://localhost:5173/dashboard'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Define a simple root endpoint
@app.get("/")
async def read_root():
    # A simple root endpoint to confirm the API is running.
    return {"message": "Welcome to Digiflow Scheduler API! It's running."}


# Database dependency function
def get_db_session(db: Session = Depends(get_db)):
    # Dependency that provides a SQLAlchemy SessionLocal to API routes. Ensures the session is properly closed after the request.
    try:
        yield db
    finally:
        db.close()

# Healthcheck 
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# TEMPORARY PROTECTED ROUTE FOR TESTING
from backend.app.dependencies import get_current_user
from backend.app.models import User

@app.get("/api/protected", response_model=str)
def protected_route(current_user: User= Depends(get_current_user)):
    return f"Hello, {current_user.email}. You are authenticated."

# --- Creating Scheduling API Endpoint, Call Scheduler Logic, Handle Output ---
@app.post(
    "/api/schedule",
    response_model=ScheduleOutputResponse,
    summary="Trigger a new production schedule calculation",
    description="Loads data from the database, runs the OR-Tools scheduler, and saves the optimal schedule back to the database. Returns to scheduling result."
)
async def run_scheduler_endpoint(
    request_data: ScheduleRequest,
    db: Session = Depends(get_db_session)
):
    logger.info(f"Received scheduling request (Run ID: {request_data.run_id if request_data.run_id else 'N/A'})...")
    current_real_time_anchor = request_data.start_time_anchor if request_data.start_time_anchor else datetime.now(timezone.utc)
    logger.info(f"Scheduling anchor time set to : {current_real_time_anchor.isoformat()}")

    try:
        logger.info("Loading and preparing data for OR-Tools scheduler...")
        all_tasks, job_to_tasks, machines_orm, downtime_events = \
            load_and_prepare_data_for_ortools(db, current_real_time_anchor)
        
        if not all_tasks:
            logger.warning("No tasks found to schedule. Returning early.")
            return ScheduleOutputResponse(
                status = "NO_TASKS",
                message="No tasks found in the database to schedule based on current criteria.",
                scheduled_tasks=[]
            )
        
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
        if status_str.upper() in ["INFEASIBLE", "ERROR"]:
            logger.error(f"Scheduling failed: status = {status_str}")
        
    except Exception as e:
        logger.exception(f"An unexpected error occurred during scheduling API call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"An internal server error occured: {e}"
        )
    
    if optimal_schedule_raw:
        logger.info(f"Scheduler completed with status '{status_str}', Makespan: {makespan_mins / 60:.2f} hours.")
        try:
            # Capture the list of persisted ORM objects returned by save_scheduled_tasks_to_db
            persisted_scheduled_tasks: List[ScheduledTask] = save_scheduled_tasks_to_db(db, optimal_schedule_raw)
        except ValueError as ve:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(ve))
        logger.info("Optimal schedule saved to database.")

        # Construct ScheduledTaskResponse directly from the persisted ORM objects
        # Pydantic's from_attributes=True will handle the mapping, including the 'id'.
        scheduled_tasks_response = [
            ScheduledTaskResponse.model_validate(task_obj) # Use model_validate for ORM objects
            for task_obj in persisted_scheduled_tasks
            if not task_obj.archived
        ]

        if not scheduled_tasks_response:
            logger.warning("Scheduler completed but all tasks were archived or filtered. Returning empty result.")
            return ScheduleOutputResponse(
                status="NO_VISIBLE_TASKS",
                scheduled_tasks=[],
                message="Scheduler completed but no visible scheduled tasks (archived or invalid)."
            )
        
        for task_obj in persisted_scheduled_tasks:
            try: 
                validated = ScheduledTaskResponse.model_validate(task_obj)
            except Exception as e: 
                print("Validation failed for task_obj: ",task_obj)
                raise


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

