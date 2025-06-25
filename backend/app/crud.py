from sqlalchemy.orm import Session
from backend.app import models, schemas
from backend.app.models import ProductionOrder, ProcessStep, Machine, DowntimeEvent
from backend.app.schemas import (ProductionOrderCreate, ProductionOrderUpdate, 
                                 ProcessStepCreate, ProcessStepUpdate,
                                 MachineCreate, MachineUpdate,
                                 DowntimeEventCreate, DowntimeEventUpdate)

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

