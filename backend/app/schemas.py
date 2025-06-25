from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.enums import OrderStatus, JobLogStatus

# --- 2.3.2 Define ScheduleRequest Schema ---
class ScheduleRequest(BaseModel):
    """
    Pydantic model for the requst body when triggreing a schedule.
    """
    run_id: Optional[str] = None # A client-provided label for the scheduling run (for logging/tracking)
    start_time_anchor: Optional[datetime] = None # Use ISO format string for datetime input, use server time if not provided
    horizon_override: Optional[int] = None

    class Config:
        from_attributes = True
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
        from_attributes = True

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
        from_attributes = True
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
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# --- Production  Order ---
class ProductionOrderBase(BaseModel):
    order_id_code: str
    product_name: Optional[str]
    product_route_id: str
    quantity_to_produce: int
    priority: int
    arrival_time: datetime
    due_date: Optional[datetime] = None
    current_status: str

    @field_validator("arrival_time", "due_date", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v=datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
    
    @field_validator("quantity_to_produce")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity_to_produce must be a positive integer")
        return v
    
    @ field_validator("due_date")
    def due_date_must_be_after_arrival(cls, v, values):
        if v and 'arrival_time' in values.data and v < values.data['arrival_time']:
            raise ValueError('due_date must be on or after arrival_time')
        return v

class ProductionOrderCreate(ProductionOrderBase): pass
class ProductionOrderUpdate(BaseModel): # Partial
    product_name: Optional[str] = None
    product_route_id: Optional[str] = None
    quantity_to_produce: Optional[int] = None
    priority: Optional[int] = None
    arrival_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    current_status: Optional[str] = None

    @field_validator("arrival_time", "due_date", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v=datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

class ProductionOrderOut(ProductionOrderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Process Steps ---
class ProcessStepBase(BaseModel):
    product_route_id: str
    step_number: int
    step_name: Optional[str]
    required_machine_type: str
    base_duration_per_unit_mins: int

    @field_validator("step_number", "base_duration_per_unit_mins")
    def values_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("step_number and base_duration_per_mins must be positive")
        return v

class ProcessStepCreate(ProcessStepBase): pass
class ProcessStepUpdate(BaseModel):
    step_name: Optional[str] = None
    required_machine_type: Optional[str] = None
    base_duration_per_unit_mins: Optional[int] = None

class ProcessStepOut(ProcessStepBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Machine ---
class MachineBase(BaseModel):
    machine_id_code: str
    machine_type: str
    default_setup_time_mins: int
    is_active: bool = True

    @field_validator("default_setup_time_mins")
    def setup_time_cannot_be_negative(cls, v):
        if v < 0:
            raise ValueError("default_setup_time_mins cannot be negative")
        return v

class MachineCreate(MachineBase): pass
class MachineUpdate(BaseModel):
    machine_type: Optional[str] = None
    default_setup_time_mins: Optional[int] = None
    is_active: Optional[bool] = None

class MachineOut(MachineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Downtime Events ---
class DowntimeEventBase(BaseModel):
    machine_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v=datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
class DowntimeEventCreate(DowntimeEventBase): pass
class DowntimeEventUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = None

class DowntimeEventOut(DowntimeEventBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

