from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from backend.app import crud, schemas, models
from backend.app.database import get_db

router = APIRouter(prefix="/api", tags=["CRUD Operations"])

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
