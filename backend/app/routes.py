from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.database import get_db

router = APIRouter(prefix="/api", tags=["CRUD"])

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PRODUCTION ORDER ---
@router.post("/orders/", response_model=schemas.ProductionOrderOut)
def create_production_order(order_data: schemas.ProductionOrderCreate, db: Session = Depends(get_db)):
    return crud.create_production_order(db, order_data)

@router.get("/orders/", response_model=list[schemas.ProductionOrderOut])
def get_all_production_orders(db:Session = Depends(get_db)):
    return crud.get_all_production_orders(db)

@router.get("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def get_production_order(order_id: int, db: Session = Depends(get_db)):
    return crud.get_production_order(db, order_id)

@router.put("/orders/{order_id}", response_model=schemas.ProductionOrderOut)
def update_production_order(order_id: int, update_data: schemas.ProductionOrderUpdate, db: Session = Depends(get_db)):
    return crud.update_production_order(db, order_id, update_data)

@router.delete("/orders/{order_id}")
def delete_production_order(order_id: int, db: Session = Depends(get_db)):
    crud.delete_production_order(db, order_id)
    return {"detail": "Production order deleted"}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- PROCESS STEPS ---
@router.post("/steps/", response_model=schemas.ProcessStepOut)
def create_process_step(step_data: schemas.ProcessStepCreate, db: Session = Depends(get_db)):
    return crud.create_process_step(db, step_data)

@router.get("/steps/", response_model=list[schemas.ProcessStepOut])
def get_all_process_steps(db: Session = Depends(get_db)):
    return crud.get_all_process_steps(db)

@router.get("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def get_process_step(step_id: int, db: Session = Depends(get_db)):
    return crud.get_process_step(db, step_id)

@router.put("/steps/{step_id}", response_model=schemas.ProcessStepOut)
def update_process_step(step_id: int, update_data: schemas.ProcessStepUpdate, db:Session= Depends(get_db)):
    return crud.update_process_step(db, step_id, update_data)

@router.delete("/steps/{step_id}")
def delete_process_step(step_id: int, db: Session = Depends(get_db)):
    crud.delete_process_step(db, step_id)
    return {"detail": "Process step deleted"}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- MACHINE ---
@router.post("/machines/", response_model=schemas.MachineOut)
def create_machine(machine_data: schemas.MachineCreate, db: Session = Depends(get_db)):
    return crud.create_machine(db, machine_data)

@router.get("/machines/", response_model=list[schemas.MachineOut])
def get_all_machines(db: Session = Depends(get_db)):
    return crud.get_all_machines(db)

@router.get("/machines/{machine_id}", response_model=schemas.MachineOut)
def get_machine(machine_id: int, db: Session = Depends(get_db)):
    return crud.get_machine(db, machine_id)

@router.put("/machines/{machine_id}", response_model=schemas.MachineOut)
def update_machine(machine_id: int, update_data: schemas.MachineUpdate, db: Session = Depends(get_db)):
    return crud.update_machine(db, machine_id, update_data)

@router.delete("/machines/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    crud.delete_machine(db, machine_id)
    return {"detail": "Machine deleted"}

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# --- DOWNTIME EVENT ---
@router.post("/downtimes/", response_model=schemas.DowntimeEventOut)
def create_downtime_event(event_data: schemas.DowntimeEventCreate, db: Session = Depends(get_db)):
    return crud.create_downtime_event(db, event_data)

@router.get("/downtimes/", response_model=list[schemas.DowntimeEventOut])
def get_all_downtime_events(db: Session = Depends(get_db)):
    return crud.get_all_downtime_events(db)

@router.get("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def get_downtime_event(event_id: int, db: Session = Depends(get_db)):
    return crud.get_downtime_event(db, event_id)

@router.put("/downtimes/{event_id}", response_model=schemas.DowntimeEventOut)
def update_downtime_event(event_id: int, update_data: schemas.DowntimeEventUpdate, db: Session = Depends(get_db)):
    return crud.update_downtime_event(db, event_id, update_data)

@router.delete("/downtimes/{event_id}")
def delete_downtime_event(event_id: int, db: Session = Depends(get_db)):
    crud.delete_downtime_event(db, event_id)
    return {"detail": "Downtime event deleted"}