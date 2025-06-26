import enum
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Type, TypeVar, Union

from backend.app import models, schemas
from backend.app.models import ProductionOrder, ProcessStep, Machine, DowntimeEvent, ScheduledTask, JobLog
from backend.app.schemas import (ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderOut,
                                 ProcessStepCreate, ProcessStepUpdate, ProcessStepOut,
                                 MachineCreate, MachineUpdate, MachineOut,
                                 DowntimeEventCreate, DowntimeEventUpdate, DowntimeEventOut)
from backend.app.enums import OrderStatus, JobLogStatus
from backend.app.config import PRODUCTION_ORDER_TRANSITIONS, JOBLOG_TRANSITIONS

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER --- 
def create_production_order(db: Session, order_data: ProductionOrderCreate) -> models.ProductionOrder:
    order = ProductionOrder(**order_data.model_dump())
    db.add(order)
    return order

def get_production_order(db: Session, order_id: int) -> models.ProductionOrder | None:
    return db.query(models.ProductionOrder).filter(models.ProductionOrder.id == order_id).first()

def get_production_order_by_code(db: Session, order_id_code: str) -> models.ProductionOrder | None:
    return db.query(models.ProductionOrder).filter(models.ProductionOrder.order_id_code == order_id_code).first()

def get_all_production_orders(db: Session) -> list[models.ProductionOrder]:
    return db.query(models.ProductionOrder).all()

def update_production_order(db: Session, db_obj: models.ProductionOrder, order_update: schemas.ProductionOrderUpdate) -> models.ProductionOrder:
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    return db_obj

def delete_production_order(db: Session, db_obj: models.ProductionOrder):
    db.delete(db_obj)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PROCESS STEP --- 
def create_process_step(db: Session, step_data: schemas.ProcessStepCreate) -> models.ProcessStep:
    step = models.ProcessStep(**step_data.model_dump())
    db.add(step)
    return step

def get_process_step(db:Session, step_id: int) -> models.ProcessStep | None:
    return db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id).first()

def get_all_process_steps(db:Session) -> list[models.ProcessStep]:
    return db.query(models.ProcessStep).all()

def update_process_step(db: Session, db_obj: models.ProcessStep, step_update: schemas.ProcessStepUpdate) -> models.ProcessStep:
    update_data = step_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    return db_obj

def delete_process_step(db: Session, db_obj: models.ProcessStep):
    db.delete(db_obj)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- MACHINE ---
def create_machine(db: Session, machine_data: schemas.MachineCreate) -> models.Machine:
    machine = models.Machine(**machine_data.model_dump())
    db.add(machine)
    return machine

def get_machine(db: Session, machine_id: int) -> models.Machine | None:
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def get_machine_by_code(db: Session, machine_id_code: str) -> models.Machine | None:
    return db.query(models.Machine).filter(models.Machine.machine_id_code == machine_id_code).first()

def get_all_machines(db: Session) -> list[models.Machine]:
    return db.query(models.Machine).all()

def update_machine(db: Session, db_obj: models.Machine, machine_update: schemas.MachineUpdate) -> models.Machine:
    update_data = machine_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    return db_obj

def delete_machine(db: Session, db_obj: models.Machine):
    db.delete(db_obj)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- DOWNTIME EVENT ---
def create_downtime_event(db: Session, event_data: schemas.DowntimeEventCreate) -> models.DowntimeEvent:
    event = models.DowntimeEvent(**event_data.model_dump())
    db.add(event)
    return event

def get_downtime_event(db:Session, event_id: int) -> models.DowntimeEvent | None:
    return db.query(models.DowntimeEvent).filter(models.DowntimeEvent.id == event_id).first()

def get_all_downtime_events(db: Session) -> list[models.DowntimeEvent]:
    return db.query(models.DowntimeEvent).all()

def update_downtime_event(db: Session, db_obj: models.DowntimeEvent, event_update: schemas.DowntimeEventUpdate) -> models.DowntimeEvent:
    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    return db_obj

def delete_downtime_event(db: Session, db_obj: models.DowntimeEvent):
    db.delete(db_obj)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- VALID STATUS TRANSITIONS ---
def validate_transition(current_status_enum: Union[OrderStatus, JobLogStatus],
                        new_status_enum: Union[OrderStatus, JobLogStatus],
                        transition_map: dict
    ):
    if current_status_enum not in transition_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid current status '{current_status_enum.value}' for transition rules. It's not a recognizable status."  
        )

    allowed_next_statuses: List[enum.Enum] = transition_map.get(current_status_enum, [])

    if new_status_enum not in [s for s in allowed_next_statuses]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_status_enum.value}' to '{new_status_enum.value}'. "
                f"Allowed transitions for '{current_status_enum.value}': {', '.join(s.value for s in allowed_next_statuses) if allowed_next_statuses else 'None'}."
        )

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER STATUS TRANSITION ---
def update_production_order_status(db: Session, order_id: int, new_status: OrderStatus) -> ProductionOrder:
    db_order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found"
        )
    try:
        validate_transition(db_order.current_status, new_status, PRODUCTION_ORDER_TRANSITIONS)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve)
        )
    db_order.current_status = new_status
    db.add(db_order)
    try: 
        db.commit()
        db.refresh(db_order)
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Failed to update production order status: {e}"
        )
    
    return db_order

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- JOB LOGS STATUS TRANSITION ---
def update_job_log_status(db: Session, job_log_id: int, new_status: JobLogStatus) -> JobLog:
    db_job_log = db.query(JobLog).filter(JobLog.id == job_log_id).first()
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job Log not found.")

    # Validate the status transition
    try:
        validate_transition(db_job_log.status, new_status, JOBLOG_TRANSITIONS)
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))


    db_job_log.status = new_status # Assign the Enum member
    db.add(db_job_log) # Mark as dirty
    try:
        db.commit()
        db.refresh(db_job_log)
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update job log status: {e}")
    
    return db_job_log

