import enum
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Type, TypeVar, Union, Optional, cast
from datetime import datetime, timezone
from uuid import UUID

from backend.app import schemas
from backend.app.models import (
    ProductionOrder, 
    ProcessStep, 
    Machine, 
    DowntimeEvent, 
    ScheduledTask, 
    JobLog,
    User
    )
from backend.app import models
from backend.app.schemas import (
    ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderOut, ProductionOrderImport,
    ProcessStepCreate, ProcessStepUpdate, ProcessStepOut,
    MachineCreate, MachineUpdate, MachineOut,
    DowntimeEventCreate, DowntimeEventUpdate, DowntimeEventOut,
    JobLogCreate, JobLogUpdate, JobLogOut,
    UserCreate, UserUpdate, UserUpdateMe, UserOut
    )
from backend.app.enums import OrderStatus, JobLogStatus
from backend.app.config import PRODUCTION_ORDER_TRANSITIONS, JOBLOG_TRANSITIONS
from backend.app.utils import hash_password, verify_password

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER --- 
def create_production_order(db: Session, order_data: ProductionOrderCreate) -> models.ProductionOrder:
    order = ProductionOrder(**order_data.model_dump())
    db.add(order)
    return order

def import_production_orders(db: Session, orders: List[ProductionOrderImport]):
    seen_ids = set()
    for order in orders:
        if order.order_id_code in seen_ids:
            raise HTTPException(status_code=400, detail=f"Duplicate order_id_code in file: {order.order_id_code}")
        seen_ids.add(order.order_id_code)

    existing_ids = set(
        row[0] for row in db.execute(
            select(ProductionOrder.order_id_code)
            .where(ProductionOrder.order_id_code.in_(seen_ids))
        ).all()
    )
    if existing_ids:
        raise HTTPException(
            status_code=409,
            detail=f"These order IDs already exist in DB: {', '.join(existing_ids)}"
        )

    db_orders = [
        models.ProductionOrder(
            order_id_code = order.order_id_code,
            product_name = order.product_name,
            product_route_id = order.product_route_id,
            quantity_to_produce = order.quantity_to_produce,
            priority = order.priority,
            arrival_time = order.arrival_time,
            due_date = order.due_date,
            current_status = order.current_status
        ) for order in orders
    ]
    db.add_all(db_orders)
    db.commit()
    return db_orders

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
# --- JOB LOGS ---

def create_job_log(db: Session, job_log_data: schemas.JobLogCreate) -> models.JobLog:
    db_job_log = models.JobLog(**job_log_data.model_dump())
    db.add(db_job_log)
    return db_job_log

def get_job_log(db:Session, job_log_id: int) -> Optional[models.JobLog]:
    return db.query(models.JobLog).filter(models.JobLog.id == job_log_id).first()

def get_all_job_logs(db: Session) -> List[models.JobLog]:
    return db.query(models.JobLog).all()

def update_job_log(db: Session, db_obj: models.JobLog, job_log_update: schemas.JobLogUpdate) -> models.JobLog:
    update_data = job_log_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Handle specific field updates or transformations if necessary
        setattr(db_obj, field, value)
    db.add(db_obj)
    return db_obj

def delete_job_log(db: Session, db_obj: models.JobLog):
    db.delete(db_obj)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- USER --- 
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_pw = hash_password(user_in.password)
    db_user = User(
        username = user_in.username,
        email = user_in.email,
        hashed_password = hashed_pw,
        full_name = user_in.full_name,
        is_active = True,
        role = user_in.role,
        is_superuser = user_in.is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_by_admin(db: Session, db_user: User, updates: UserUpdate) -> User:
    if updates.email:
        existing = get_user_by_email(db, updates.email)
        if existing and existing.id != db_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        db_user.email = updates.email
    if updates.full_name is not None:
        db_user.full_name = updates.full_name
    if updates.role is not None:
        db_user.role = updates.role
    if updates.is_active is not None:
        db_user.is_active = updates.is_active
    if updates.is_superuser is not None:
        db_user.is_superuser = updates.is_superuser
    if updates.password:
        db_user.hashed_password = hash_password(updates.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_me(db: Session, db_user: User, user_in: UserUpdateMe) -> User:
    for field, value in user_in.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_password(db: Session, db_user: User, current_pw: str, new_pw: str) -> User:
    if not verify_password(current_pw, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    db_user.hashed_password = hash_password(new_pw)
    db.commit()
    db.refresh(db_user)
    return db_user
    


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
    return db_order

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- JOB LOGS STATUS TRANSITION ---
def update_job_log_status(db: Session, job_log_id: int, new_status: JobLogStatus) -> models.JobLog:
    db_job_log = db.query(models.JobLog).filter(models.JobLog.id == job_log_id).first()
    if not db_job_log:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job Log not found.")

    current_status_enum = db_job_log.status

    # Validate the status transition
    try:
        validate_transition(current_status_enum, new_status, JOBLOG_TRANSITIONS)
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))

    if new_status == JobLogStatus.COMPLETED and db_job_log.actual_end_time is None:
        setattr(db_job_log, 'actual_end_time', datetime.now(timezone.utc))

    db_job_log.status = new_status # Assign the Enum member
    db.add(db_job_log) # Mark as dirty
    if new_status == JobLogStatus.COMPLETED:
        check_and_update_production_order_completion(db, cast(int,db_job_log.production_order_id))

    return db_job_log

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- AUTOMATIC COMPLETION LOGIC ---
def check_and_update_production_order_completion(db: Session, production_order_id: int):
    # Checks if all JobLogs for a given ProductionOrder are COMPLETED, If so, updates the ProductionOrder's status to COMPLETED.
    production_order = get_production_order(db, production_order_id)
    if not production_order:
        # Log but don't raise HTTPException here as it's an internal helper
        print(f"Warning: Production Order with ID {production_order_id} not found for completion check.")
        return

    incomplete_logs_count = db.query(models.JobLog).filter(
        models.JobLog.production_order_id == production_order_id,
        models.JobLog.status != JobLogStatus.COMPLETED
    ).count()

    if incomplete_logs_count == 0:
        logging.info(f"All JobLogs for PO {production_order_id} are completed. Updating PO status to COMPLETED.")
        # This will now be part of the parent transaction, not a new one.
        update_production_order_status(db, production_order_id, OrderStatus.COMPLETED)    

    # Check if the ProductionOrder is already completed to avoid unnecessary work
    if production_order.current_status == OrderStatus.COMPLETED:
        return
    
    # Fetch all job logs for this production order. Note: Use db.query directly for a more focused query here
    get_all_job_logs_for_order = db.query(models.JobLog).filter(
        models.JobLog.production_order_id == production_order_id
    ).all()

    # If there are no job logs, the order cant be completed by this logic. 
    # This scenario might need manual intervention or different logic depending on business rules.
    if not get_all_job_logs_for_order:
        print(f"Info: Production Order {production_order_id} has no associated JobLogs. Cannot auto-complete.")
        return
    
    # Check if all job logs are COMPLETED in status
    all_logs_completed = all(log.status == JobLogStatus.COMPLETED for log in get_all_job_logs_for_order)

    if all_logs_completed:
        print(f"All JobLogs for Production Order {production_order_id} are completed. Marking Production Order as COMPLETED.")
        # Use the existing status update function to ensure transiition validation
        # Wrap in try-except in case the transition is not allowed from current state
        try:
            update_production_order_status(db, production_order_id, OrderStatus.COMPLETED)
        except HTTPException as e:
            print(f"Error auto-completing Production Order {production_order_id}: {e.detail}")
    else:
        print(f"Not all JobLogs for Production Order {production_order_id} are completed. Production Order status remains {production_order.current_status.value}.")


    
    

