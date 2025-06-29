from pydantic import BaseModel, field_validator, ConfigDict, Field, EmailStr
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.enums import OrderStatus, JobLogStatus
from backend.app.utils import ensure_utc_aware

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

# --- Job Logs ---
class JobLogBase(BaseModel):
    # Fixed: Removed Field(...) for required fields to avoid Pylance redeclaration warning
    production_order_id: int
    process_step_id: int
    machine_id: int
    actual_start_time: datetime
    actual_end_time: Optional[datetime] = Field(None) # Keep Field(None) for optional defaults
    remarks: Optional[str] = Field(None) # Keep Field(None) for optional defaults
    status: JobLogStatus = JobLogStatus.PENDING

    @field_validator("actual_start_time", "actual_end_time", mode="before")
    @classmethod
    def ensure_utc_joblog(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v=datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
    
    @field_validator('actual_end_time')
    def end_time_must_be_after_start_time_joblog(cls, v, info):
        if 'actual_start_time' in info.data and v is not None and info.data['actual_start_time'] is not None and v <= info.data['actual_start_time']:
            raise ValueError('actual_end_time must be after actual_start_time')
        return v

class JobLogCreate(JobLogBase):
    production_order_id: int
    process_step_id: int
    machine_id: int
    actual_start_time: datetime

class JobLogUpdate(BaseModel):
    # Fixed: Removed Field(...) for optional fields without specific metadata
    production_order_id: Optional[int] = None
    process_step_id: Optional[int] = None
    machine_id: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    status: Optional[JobLogStatus] = None
    remarks: Optional[str] = None

    @field_validator("actual_start_time", "actual_end_time", mode="before")
    @classmethod
    def ensure_utc_joblog_update(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v=datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
    
    @field_validator('actual_end_time')
    def end_time_must_be_after_start_time_joblog_update(cls, v, info):
        if 'actual_start_time' in info.data and v is not None and info.data['actual_start_time'] is not None and v <= info.data['actual_start_time']:
            raise ValueError('actual_end_time must be after actual_start_time')
        return v

class JobLogOut(JobLogBase):
    id: int
    # Ensure all required fields from the model are here for the response
    production_order_id: int
    process_step_id: int
    machine_id: int
    actual_start_time: datetime
    model_config = ConfigDict(from_attributes=True)

# --- PRIVATE USER SCHEMAS ---
class UserBase(BaseModel):
    username: str = Field(..., max_length=255)
    email: EmailStr = Field(..., max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    role: str = "user"
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=40)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    id: UUID
    hashed_password: str
    created_at: datetime
    last_login: Optional[datetime] = None
    refresh_token_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- PUBLIC USER SCHEMAS ---
class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserUpdateMe(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str

# --- PUBLIC AUTHENTICATION USER SCHEMAS ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str 

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: Optional[int] = None
    role: Optional[str] = None

# --- STATUSES ---
class ProductionOrderStatusUpdate(BaseModel):
    new_status: OrderStatus = Field(..., description="The new status to set for the production order.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"new_status": "In Progress"},
                {"new_status": "Completed"}
            ]
        }
    }

class JobLogStatusUpdate(BaseModel):
    new_status: JobLogStatus = Field(..., description="The new status to set for the job log.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"new_status": "In Progress"},
                {"new_status": "Completed"},
                {"new_status": "Failed"}
            ]
        }
    }