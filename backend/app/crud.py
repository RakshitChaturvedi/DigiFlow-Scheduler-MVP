from sqlalchemy.orm import Session
from backend.app.models import ProductionOrder, ProcessStep, Machine, DowntimeEvent
from backend.app.schemas import (ProductionOrderCreate, ProductionOrderUpdate, 
                                 ProcessStepCreate, ProcessStepUpdate,
                                 MachineCreate, MachineUpdate,
                                 DowntimeEventCreate, DowntimeEventUpdate)

# --- PRODUCTION ORDER --- 
def create_production_order(db: Session, order_data: ProductionOrderCreate):
    order = ProductionOrder(**order_data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def get_production_order(db: Session, order_id: int):
    return db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()

def get_all_production_orders(db: Session):
    return db.query(ProductionOrder).all()

def update_production_order(db: Session, order_id: int, order_update: ProductionOrderUpdate):
    order = get_production_order(db, order_id)
    if order:
        for field, value in order_update.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        db.commit()
        db.refresh(order)
    return order

def delete_production_order(db: Session, order_id: int):
    order = get_production_order(db, order_id)
    if order:
        db.delete(order)
        db.commit()
    return order


# --- PROCESS STEP --- 
def create_process_step(db: Session, step_data: ProcessStepCreate):
    step = ProcessStep(**step_data.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step

def get_process_step(db:Session, step_id: int):
    return db.query(ProcessStep).filter(ProcessStep.id == step_id).first()

def get_all_process_steps(db:Session):
    return db.query(ProcessStep).all()

def update_process_step(db: Session, step_id: int, step_update: ProcessStepUpdate):
    step = get_process_step(db, step_id)
    if step:
        for field, value in step_update.model_dump(exclude_unset=True).items():
            setattr(step, field, value)
        db.commit()
        db.refresh(step)
    return step

def delete_process_step(db: Session, step_id: int):
    step = get_process_step(db, step_id)
    if step:
        db.delete(step)
        db.commit()
    return step


# --- MACHINE ---
def create_machine(db: Session, machine_data: MachineCreate):
    machine = Machine(**machine_data.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine

def get_machine(db: Session, machine_id: int):
    return db.query(Machine).filter(Machine.id == machine_id).first()

def get_all_machines(db: Session):
    return db.query(Machine).all()

def update_machine(db: Session, machine_id: int, machine_update: MachineUpdate):
    machine = get_machine(db, machine_id)
    if machine:
        for field, value in machine_update.model_dump(exclude_unset=True).items():
            setattr(machine, field, value)
        db.commit()
        db.refresh(machine)
    return machine

def delete_machine(db: Session, machine_id: int):
    machine = get_machine(db, machine_id)
    if machine:
        db.delete(machine)
        db.commit()
    return machine


# --- DOWNTIME EVENT ---
def create_downtime_event(db: Session, event_data: DowntimeEventCreate):
    event = DowntimeEvent(**event_data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_downtime_event(db:Session, event_id: int):
    return db.query(DowntimeEvent).filter(DowntimeEvent.id == event_id).first()

def get_all_downtime_events(db: Session):
    return db.query(DowntimeEvent).all()

def update_downtime_event(db: Session, event_id: int, event_update: DowntimeEventUpdate):
    event = get_downtime_event(db, event_id)
    if event:
        for field, value in event_update.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        db.commit()
        db.refresh(event)
    return event

def delete_downtime_event(db: Session, event_id: int):
    event = get_downtime_event(db, event_id)
    if event:
        db.delete(event)
        db.commit()
    return event

