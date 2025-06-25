from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- 2.3.2 Define ScheduleRequest Schema ---
class ScheduleRequest(BaseModel):
    """
    Pydantic model for the requst body when triggreing a schedule.
    """
    run_id: Optional[str] = None # A client-provided label for the scheduling run (for logging/tracking)
    start_time_anchor: Optional[datetime] = None # Use ISO format string for datetime input, use server time if not provided
    horizon_override: Optional[int] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# --- Internal model: Raw scheduled task (DB ↔ Solver ↔ Backend) ---
class ScheduledTaskInternal(BaseModel):
    """
    Internal format of a scheduled task, closely tied to solver/database
    """
    production_order_id: int
    process_step_id: int
    assigned_machine_id: int
    start_time: datetime
    end_time: datetime
    scheduled_duration_mins: int
    status: str
    job_id_code: Optional[str] = None
    step_number: Optional[int] = None

    class Config:
        orm_mode = True

# --- Public model: Client-facing scheduled task (API Response) ---
class ScheduledTaskResponse(BaseModel):
    """
    API response model for one scheduled task, adapted for client readability
    """
    production_order_id: str
    process_step_id: str
    assigned_machine_id: int
    start_time: datetime
    end_time: datetime
    scheduled_duration_mins: int
    status: str
    job_id_code: str
    step_number: int

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# --- Output model: Full API response for /schedule endpoint ---
class ScheduleOutputResponse(BaseModel):
    """
    Final API response for schedule execution.
    """
    status: str     # e.g "OPTIMAL", "FEASIBLE", "INFEASIBLE", "ERROR"
    makespan_minutes: Optional[float] = None
    scheduled_tasks: List[ScheduledTaskResponse]
    message: Optional[str] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

