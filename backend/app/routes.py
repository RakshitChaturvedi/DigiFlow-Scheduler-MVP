from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import logging
import traceback
from typing import List

from backend.app import schemas
from backend.app import crud
from backend.app import models
from backend.app.scheduler import save_scheduled_tasks_to_db
from backend.app.database import get_db
from backend.app.config import PRODUCTION_ORDER_TRANSITIONS, JOBLOG_TRANSITIONS
from backend.app.schemas import (
    ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderOut, # Using ProductionOrderOut
    MachineCreate, MachineUpdate, MachineOut, # Assuming MachineOut
    ProcessStepCreate, ProcessStepUpdate, ProcessStepOut, # Assuming ProcessStepOut
    DowntimeEventCreate, DowntimeEventUpdate, DowntimeEventOut, # Assuming DowntimeEventOut
    ProductionOrderStatusUpdate, JobLogStatusUpdate,
    JobLogOut,
    UserOut, LoginRequest, UserRegister, Token, UserCreate
)
from backend.app.crud import get_user_by_email, create_user
from backend.app.utils import hash_password, verify_password, create_access_token
from backend.app.models import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/api", tags=["CRUD Operations"])

def get_db_session(db: Session = Depends(get_db)):
    try:
        yield db
    finally:
        db.close()
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER ---
@router.post("/orders/", response_model=schemas.ProductionOrderOut, status_code=status.HTTP_201_CREATED)
def create_production_order_endpoint(order_data: schemas.ProductionOrderCreate, db: Session = Depends(get_db)):
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
def get_all_production_orders_endpoint(db:Session = Depends(get_db)):
    return crud.get_all_production_orders(db)

@router.get("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def get_production_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_production_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found."
        )
    return db_order

@router.put("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def update_production_order_endpoint(order_id: int, update_data: schemas.ProductionOrderUpdate, db: Session = Depends(get_db)):
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
def delete_production_order_endpoint(order_id: int, db: Session = Depends(get_db)):
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
def create_process_step_endpoint(step_data: schemas.ProcessStepCreate, db: Session = Depends(get_db)):
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
def get_all_process_steps_endpoint(db: Session = Depends(get_db)):
    return crud.get_all_process_steps(db)

@router.get("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def get_process_step_endpoint(step_id: int, db: Session = Depends(get_db)):
    step = crud.get_process_step(db, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Process step not found")
    return step

@router.put("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def update_process_step_endpoint(step_id: int, update_data: schemas.ProcessStepUpdate, db: Session = Depends(get_db)):
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
def delete_process_step_endpoint(step_id: int, db: Session = Depends(get_db)):
    db_step = crud.get_process_step(db, step_id)
    if not db_step:
        raise HTTPException(status_code=404, detail="Process step not found")
    crud.delete_process_step(db, db_step)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- MACHINES ---
@router.post("/machines/", response_model=schemas.MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine_endpoint(machine_data: schemas.MachineCreate, db: Session = Depends(get_db)):
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
def get_all_machines_endpoint(db: Session = Depends(get_db)):
    return crud.get_all_machines(db)

@router.get("/machines/{machine_id}", response_model=schemas.MachineOut)
def get_machine_endpoint(machine_id: int, db: Session = Depends(get_db)):
    machine = crud.get_machine(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.put("/machines/{machine_id}", response_model=schemas.MachineOut)
def update_machine_endpoint(machine_id: int, update_data: schemas.MachineUpdate, db: Session = Depends(get_db)):
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
def delete_machine_endpoint(machine_id: int, db: Session = Depends(get_db)):
    db_machine = crud.get_machine(db, machine_id)
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    crud.delete_machine(db, db_machine)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- DOWNTIME EVENT ---
@router.post("/downtimes/", response_model=schemas.DowntimeEventOut, status_code=status.HTTP_201_CREATED)
def create_downtime_event_endpoint(event_data: schemas.DowntimeEventCreate, db: Session = Depends(get_db)):
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
def get_all_downtime_events_endpoint(db: Session = Depends(get_db)):
    return crud.get_all_downtime_events(db)

@router.get("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def get_downtime_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_downtime_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    return event

@router.put("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def update_downtime_event_endpoint(event_id: int, update_data: schemas.DowntimeEventUpdate, db: Session = Depends(get_db)):
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
def delete_downtime_event_endpoint(event_id: int, db: Session = Depends(get_db)):
    db_event = crud.get_downtime_event(db, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Downtime event not found")
    crud.delete_downtime_event(db, db_event)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- JOB LOG ---
@router.post("/job_logs/", response_model=JobLogOut, status_code=status.HTTP_201_CREATED)
def create_job_log_endpoint(job_log_data: schemas.JobLogCreate, db: Session = Depends(get_db_session)):
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
def list_job_logs_endpoint(db: Session = Depends(get_db_session)):
    return crud.get_all_job_logs(db)

@router.get("/job_logs/{job_log_id}", response_model=JobLogOut)
def read_job_log_endpoint(job_log_id: int, db: Session = Depends(get_db_session)):
    db_job_log = crud.get_job_log(db, job_log_id)
    if db_job_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    return db_job_log

@router.put("/job_logs/{job_log_id}", response_model=JobLogOut)
def update_job_log_endpoint(job_log_id: int, update_data: schemas.JobLogUpdate, db: Session = Depends(get_db_session)):
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
def delete_job_log_endpoint(job_log_id: int, db: Session = Depends(get_db_session)):
    db_job_log = crud.get_job_log(db, job_log_id)
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job Log not found.")
    crud.delete_job_log(db, db_job_log) # crud function already commits
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

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
    db: Session = Depends(get_db_session)
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
    db: Session = Depends(get_db_session)
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
@router.post("/api/register", response_model=UserOut, status_code=201)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_create = UserCreate(
        username= user_data.username,
        email = user_data.email,
        password= user_data.password,
        full_name= user_data.full_name,
        role="user",
        is_active=True,
        is_superuser= False
    )

    db_user = create_user(db, user_create)
    return db_user

@router.post("/api/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user: User = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_access_token(subject=str(user.email), role=user.role)
    return {"access_token": token, "token_type": "bearer"}