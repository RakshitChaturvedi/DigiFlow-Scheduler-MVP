from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID
import logging
import traceback
from typing import List
from datetime import datetime, timezone

from backend.app import schemas
from backend.app import crud
from backend.app import models
from backend.app.scheduler import load_and_prepare_data_for_ortools, schedule_with_ortools, save_scheduled_tasks_to_db
from backend.app.database import get_db
from backend.app.config import PRODUCTION_ORDER_TRANSITIONS, JOBLOG_TRANSITIONS
from backend.app.schemas import (
    ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderOut, # Using ProductionOrderOut
    MachineCreate, MachineUpdate, MachineOut, # Assuming MachineOut
    ProcessStepCreate, ProcessStepUpdate, ProcessStepOut, # Assuming ProcessStepOut
    DowntimeEventCreate, DowntimeEventUpdate, DowntimeEventOut, # Assuming DowntimeEventOut
    ProductionOrderStatusUpdate, JobLogStatusUpdate,
    JobLogOut,
    ScheduleRequest, ScheduleOutputResponse, ScheduledTaskResponse,
    UserOut, LoginRequest, UserRegister, Token, UserCreate, UserUpdate, UserUpdateMe, UpdatePassword
)
from backend.app.crud import get_user_by_email, create_user, get_user_by_id, get_all_users, update_user_by_admin
from backend.app.utils import hash_password, verify_password, create_access_token, create_refresh_token, decode_access_token, decode_refresh_token, ensure_utc_aware
from backend.app.models import User
from backend.app.dependencies import get_current_active_user, require_admin, get_current_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/api", tags=["CRUD Operations"])

def get_db_session(db: Session = Depends(get_db)):
    try:
        yield db
    finally:
        db.close()

@router.get("/whoami")
def who_am_i(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_superuser,
        "role": current_user.role
    }
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER ---
@router.post("/orders/", response_model=schemas.ProductionOrderOut, status_code=status.HTTP_201_CREATED)
def create_production_order_endpoint(order_data: schemas.ProductionOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing_order = crud.get_production_order_by_code(db, order_id_code=order_data.order_id_code)
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Production order with code '{order_data.order_id_code}' already exists."
        )
    
    try:
        order = crud.create_production_order(db, order_data)
        db.commit()
        db.refresh(order)
        return order
    except ValueError as e:
        db.rollback()
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occured: {str(e)}"
        )

@router.get("/orders/", response_model=list[schemas.ProductionOrderOut])
def get_all_production_orders_endpoint(db:Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.get_all_production_orders(db)

@router.get("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def get_production_order_endpoint(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_order = crud.get_production_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found."
        )
    return db_order

@router.put("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def update_production_order_endpoint(order_id: int, update_data: schemas.ProductionOrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_order = crud.get_production_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found."
        )
    
    try:
        updated_order = crud.update_production_order(db, db_obj=db_order, order_update=update_data)
        db.commit()
        db.refresh(updated_order)
        return updated_order
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occured: {str(e)}"
        )

@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order_endpoint(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_order = crud.get_production_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found."
        )
    crud.delete_production_order(db, db_obj=db_order)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PROCESS STEPS ---
@router.post("/steps/", response_model=schemas.ProcessStepOut, status_code=status.HTTP_201_CREATED)
def create_process_step_endpoint(step_data: schemas.ProcessStepCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    try:
        step = crud.create_process_step(db, step_data)
        db.commit()
        db.refresh(step)
        return step
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occured: {str(e)}"
        )

@router.get("/steps/", response_model=list[schemas.ProcessStepOut])
def get_all_process_steps_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.get_all_process_steps(db)

@router.get("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def get_process_step_endpoint(step_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    step = crud.get_process_step(db, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Process step not found")
    return step

@router.put("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def update_process_step_endpoint(step_id: int, update_data: schemas.ProcessStepUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_step = crud.get_process_step(db, step_id)
    if not db_step:
        raise HTTPException(status_code=404, detail="Process step not found")
    try:
        updated_step = crud.update_process_step(db, db_obj=db_step, step_update=update_data)
        db.commit()
        db.refresh(updated_step)
        return updated_step
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occured: {str(e)}"
        )

@router.delete("/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_step_endpoint(step_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_step = crud.get_process_step(db, step_id)
    if not db_step:
        raise HTTPException(status_code=404, detail="Process step not found")
    crud.delete_process_step(db, db_step)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- MACHINES ---
@router.post("/machines/", response_model=schemas.MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine_endpoint(machine_data: schemas.MachineCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    try:
        machine = crud.create_machine(db, machine_data)
        db.commit()
        db.refresh(machine)
        return machine
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occured: {str(e)}"
        )

@router.get("/machines/", response_model=list[schemas.MachineOut])
def get_all_machines_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.get_all_machines(db)

@router.get("/machines/{machine_id}", response_model=schemas.MachineOut)
def get_machine_endpoint(machine_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    machine = crud.get_machine(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.put("/machines/{machine_id}", response_model=schemas.MachineOut)
def update_machine_endpoint(machine_id: int, update_data: schemas.MachineUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_machine = crud.get_machine(db, machine_id)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    try:
        updated_machine = crud.update_machine(db, db_obj=db_machine, machine_update=update_data)
        db.commit()
        db.refresh(updated_machine)
        return updated_machine
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occured: {str(e)}"
        )

@router.delete("/machines/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine_endpoint(machine_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_machine = crud.get_machine(db, machine_id)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    crud.delete_machine(db, db_machine)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- DOWNTIME EVENT ---
@router.post("/downtimes/", response_model=schemas.DowntimeEventOut, status_code=status.HTTP_201_CREATED)
def create_downtime_event_endpoint(event_data: schemas.DowntimeEventCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    try:
        event = crud.create_downtime_event(db, event_data)
        db.commit()
        db.refresh(event)
        return event
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occured: {str(e)}"
        )

@router.get("/downtimes/", response_model=list[schemas.DowntimeEventOut])
def get_all_downtime_events_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud.get_all_downtime_events(db)

@router.get("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def get_downtime_event_endpoint(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    event = crud.get_downtime_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    return event

@router.put("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def update_downtime_event_endpoint(event_id: int, update_data: schemas.DowntimeEventUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_event = crud.get_downtime_event(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    try:
        updated_event = crud.update_downtime_event(db, db_obj=db_event, event_update=update_data)
        db.commit()
        db.refresh(updated_event)
        return updated_event
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occured: {str(e)}"
        )

@router.delete("/downtimes/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_downtime_event_endpoint(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    db_event = crud.get_downtime_event(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    crud.delete_downtime_event(db, db_event)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- JOB LOG ---
@router.post("/job_logs/", response_model=JobLogOut, status_code=status.HTTP_201_CREATED)
def create_job_log_endpoint(job_log_data: schemas.JobLogCreate, db: Session = Depends(get_db_session), current_user: User = Depends(require_admin)):
    try:
        db_job_log = crud.create_job_log(db=db, job_log_data=job_log_data)
        db.commit()
        db.refresh(db_job_log)
        return db_job_log # crud function already commits and refreshes
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        db.rollback()
        logger.error("An unexpected error occurred while creating job_log")
        logger.exception(e)
        traceback.print_exc()
        raise e

@router.get("/job_logs/", response_model=List[JobLogOut])
def list_job_logs_endpoint(db: Session = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    return crud.get_all_job_logs(db)

@router.get("/job_logs/{job_log_id}", response_model=JobLogOut)
def read_job_log_endpoint(job_log_id: int, db: Session = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    db_job_log = crud.get_job_log(db, job_log_id)
    if db_job_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    return db_job_log

@router.put("/job_logs/{job_log_id}", response_model=JobLogOut)
def update_job_log_endpoint(job_log_id: int, update_data: schemas.JobLogUpdate, db: Session = Depends(get_db_session), current_user: User = Depends(require_admin)):
    db_job_log = crud.get_job_log(db, job_log_id)
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    try:
        updated_job_log = crud.update_job_log(db, db_obj=db_job_log, job_log_update=update_data)
        db.commit()
        db.refresh(updated_job_log)
        return updated_job_log # crud function already commits and refreshes
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating job log {job_log_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

@router.delete("/job_logs/{job_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_log_endpoint(job_log_id: int, db: Session = Depends(get_db_session), current_user: User = Depends(require_admin)):
    db_job_log = crud.get_job_log(db, job_log_id)
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    crud.delete_job_log(db, db_job_log) # crud function already commits
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- SCHEDULER ROUTE ---
@router.post(
    "/schedule", 
    response_model=ScheduleOutputResponse, 
    summary="Trigger production schedule (Admin Only)",
    description="Admin-only endpoint to generate a production scheduler using OR-Tools." 
)
def trigger_schedule_endpoint(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    anchor_time = request.start_time_anchor or datetime.now(timezone.utc)

    try:
        tasks, jobs_map, machines, downtimes = load_and_prepare_data_for_ortools(db, anchor_time)
        if not tasks:
            return ScheduleOutputResponse(
                status="NO_TASKS",
                message="No schedulable tasks found.",
                scheduled_tasks=[]
            )
        scheduled_raw, makespan, status = schedule_with_ortools(
            tasks, jobs_map, machines, downtimes, anchor_time, db
        )

        if status.upper() in {"INFEASIBLE", "ERROR"}:
            raise HTTPException(status_code=400, detail=f"Scheduling failed: {status}")
        
        saved = save_scheduled_tasks_to_db(db, scheduled_raw)
        response_tasks = [
            ScheduledTaskResponse.model_validate(t) for t in saved if not t.archived
        ]
        return ScheduleOutputResponse(status=status, makespan_minutes=makespan, scheduled_tasks=response_tasks,
                                      message="Schedule successfully generated and saved.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduler error: {str(e)}")

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- STATUS TRANSITIONS ---
@router.patch(
    "/orders/{order_id}/status",
    response_model=ProductionOrderOut,
    summary="Update the status of a specific production order",
    description= "Allows changing the status of a production order, with validation for allowed transitions."
)
def update_production_order_current_status(
    order_id: int,
    status_update: ProductionOrderStatusUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    try:
        # Call the CRUD function to handle the status update logic and validation
        updated_order = crud.update_production_order_status(db, order_id, status_update.new_status)
        db.commit()
        db.refresh(updated_order)
        return updated_order
    except HTTPException as he: # raised by crud.update_production_order_status (e.g., 404, 400 for invalid transition)
        raise he
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        db.rollback()
        logger.exception(f"An unexpected error occured while updating production order {order_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "An unexpected error occurred."
        )

@router.patch(
    "/job_logs/{job_log_id}/status",
    summary="Update the status of a specific job log",
    description="Allows changing the status of a job log, with validation for allowed transitions."
)
def update_job_log_current_status(
    job_log_id: int,
    status_update: JobLogStatusUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_admin)
):
    db_job_log = crud.get_job_log(db, job_log_id)
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    try:
        updated_job_log = crud.update_job_log_status(db, job_log_id, status_update.new_status)
        db.commit()
        db.refresh(updated_job_log)
        return updated_job_log
    except HTTPException as he: # Catch HTTPExceptions raised by crud.update_job_log_status
        raise he
    except ValueError as ve: # Fallback for any unexpected ValueError
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        db.rollback()
        logger.exception(f"An unexpected error occurred while updating job log {job_log_id} status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- REGISTRATION AND LOGIN ---
@router.post("/user/register", response_model=UserOut, status_code=201)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        user_create = UserCreate(
            username= user_data.username,
            email = user_data.email,
            password= user_data.password,
            full_name= user_data.full_name,
            role="user",
            is_active=True,
            is_superuser= False
        )
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail= ve.errors())

    db_user = create_user(db, user_create)
    return db_user

@router.post("/user/login", response_model=Token)
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    user: User = get_user_by_email(db, login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(subject=str(user.email), role=user.role)
    return {"access_token": token, "token_type": "bearer"}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- AUTHENTICATED ROUTES ---
@router.get("/users/me", response_model=UserOut)
def read_own_profile(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return current_user

@router.patch("/users/me", response_model=UserOut)
def update_own_profile(updates: UserUpdateMe, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name

    existing = db.query(User).filter(User.email == updates.email).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="Email already in use.")

    if updates.email is not None: 
        current_user.email = updates.email

    existing = db.query(User).filter(User.username == updates.username).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="Username already in use.")
    
    if updates.username is not None:
        current_user.username = updates.username

    db.commit()
    db.refresh(current_user)
    return current_user

@router.patch("/users/me/password", status_code=204)
def change_user_password(pw_update: UpdatePassword, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not verify_password(pw_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    current_user.hashed_password = hash_password(pw_update.new_password)
    db.commit()
    return

@router.post("/auth/logout", status_code=204)
def logout_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not current_user.refresh_token_hash:
        raise HTTPException(status_code=400, detail="No refresh token found for user")
    current_user.refresh_token_hash = None
    db.commit()
    return

@router.post("/auth/refresh", response_model=Token)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_refresh_token(refresh_token)
        user = get_user_by_email(db, payload["sub"])

        if not user or not user.refresh_token_hash:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if not verify_password(refresh_token, user.refresh_token_hash):
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        new_access_token = create_access_token(subject=user.email, role=user.role)
        return Token(access_token=new_access_token, token_type="bearer")
    
    except Exception as e:
        HTTPException(status_code=401, detail="Could not refresh token")

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- ADMIN ROUTES ---
@router.get("/admin/users", response_model=list[UserOut])
def list_all_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return get_all_users(db)

@router.get("/admin/users/{user_id}", response_model=UserOut)
def get_user_details(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/admin/users/{user_id}", response_model=UserOut)
def admin_update_user( user_id: UUID, updates: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return update_user_by_admin(db, user, updates)
