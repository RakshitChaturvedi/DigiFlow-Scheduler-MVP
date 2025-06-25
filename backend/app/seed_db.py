import pandas as pd
import numpy as np
import random

from sqlalchemy.orm.session import Session
from sqlalchemy import inspect

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Machine, ProcessStep, ProductionOrder, ScheduledTask, DowntimeEvent

import datetime
import os

from backend.app.config import (
    MACHINE_CSV,
    PROCESS_STEP_CSV,
    PRODUCTION_ORDER_CSV,
    DOWNTIME_EVENT_CSV
)

def parse_datetime(dt_str):
    # Safely parses datetime strings from CSV, handling Nat/None
    if pd.isna(dt_str) or dt_str is None:
        return None
    try:
        return datetime.datetime.strptime(str(dt_str), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.datetime.strptime(str(dt_str), '%d-%m-%Y %H:%M')
        except ValueError:
            return None

def seed_data():
    db: Session = SessionLocal()

    try:
        print("--- Starting data seeding ---")

        Base.metadata.create_all(bind=engine)
        print("Ensured all database tables are created.")

        # 1. Clear existing data to ensure a fresh seed

        # IMPORTANT: Delete in reverse order of foreign key dependency
        # Scheduled Task depends on all 3
        # Production nothing
        # Process on nothing
        # Machine on nothing
        print("Clearing existing data...")
        db.query(ScheduledTask).delete()
        db.query(DowntimeEvent).delete()
        db.query(ProductionOrder).delete()
        db.query(ProcessStep).delete()
        db.query(Machine).delete()
        db.commit()
        print("Existing data cleared.")


        # 2. Read CSVs into Pandas DataFrames
        print("Reading mock data from CSVs...")
        machines_df = pd.read_csv(MACHINE_CSV)
        process_steps_df = pd.read_csv(PROCESS_STEP_CSV)
        production_orders_df = pd.read_csv(PRODUCTION_ORDER_CSV)
        downtime_events_df = pd.read_csv(DOWNTIME_EVENT_CSV)
        print("CSVs read.") 

        # 3. Insert Machine Data
        print("Seeding Machine data...")
        for index, row in machines_df.iterrows():
            is_active_val = row['is_active']
            final_is_active: bool

            if pd.isna(is_active_val):
                final_is_active = False
            elif isinstance(is_active_val, str):
                final_is_active = is_active_val.lower() == 'true' # handles true of false strings, case insensitive
            elif isinstance(is_active_val, (int, float)):
                final_is_active = bool(int(is_active_val)) # handles 1 or 0
            else:
                final_is_active = bool(is_active_val)

            machine = Machine(
                machine_id_code = row['machine_id_code'],
                machine_type = row['machine_type'],
                default_setup_time_mins = row['default_setup_time_mins'],
                is_active = final_is_active
            )
            db.add(machine)
        db.commit()
        print(f"Seeded {len(machines_df)} machines.")

        # 4. Insert ProcessSteps Data
        print("Seeding ProcessStep data...")
        for index, row in process_steps_df.iterrows():
            process_step = ProcessStep(
                product_route_id = str(row['product_route_id']),
                step_number = row['step_number'],
                step_name = row['step_name'],
                required_machine_type = row['required_machine_type'],
                base_duration_per_unit_mins = row['base_duration_per_unit_mins']
            )
            db.add(process_step)
        db.commit()
        print(f"Seeded {len(process_steps_df)} process steps.")

        # 5. Insert ProductionOrder Data
        print("Seeding ProductionOrder data...")
        for index, row in production_orders_df.iterrows():
            due_date=None

            if pd.isna(row['order_id_code']) or str(row['order_id_code']).strip().lower() == 'nan':
                print(f"Skipping row {index} due to invalid order_id_code: {row['order_id_code']}")
                continue

            # convert string dates to datetime objects
            if pd.notna(row['due_date']):
                due_date = datetime.datetime.strptime(str(row['due_date']), '%Y-%m-%d %H:%M:%S') # Assuming YYYY-MM-DD HH:MM:SS
            
            arrival_time=None
            if pd.notna(row['arrival_time']):
                arrival_time = datetime.datetime.strptime(str(row['arrival_time']), '%d-%m-%Y %H:%M')
            else:
                arrival_time = datetime.datetime.now()

            order = ProductionOrder(
                order_id_code = row['order_id_code'],
                product_name = row['product_name'],
                product_route_id = str(row['product_route_id']),
                quantity_to_produce = row['quantity_to_produce'],
                priority = row['priority'],
                arrival_time = arrival_time,
                due_date = due_date,
                current_status = row['current_status']
            )
            db.add(order)
        db.commit()
        print(f"Seeded {len(production_orders_df)} production orders.")


        # Fetch IDs for FKs after commit
        db.expire_all()

        machines = db.query(Machine).all()
        machine_code_to_id_map = {m.machine_id_code: m.id for m in machines}
        machine_id_to_obj_map = {m.id: m for m in machines}

        production_orders = db.query(ProductionOrder).all()
        order_code_to_id_map = {po.order_id_code: po.id for po in production_orders}

        process_steps = db.query(ProcessStep).all()
        process_step_lookup = {
            (ps.product_route_id, ps.step_number): ps.id for ps in process_steps
        }

        # 6. Seed Downtime Events
        print("Seeding Downtime Events from CSV...")
        downtime_events_to_add = []
        for index, row in downtime_events_df.iterrows():
            machine_code = row['machine_id_code']

            if pd.isna(machine_code):
                print(f"Warning: Empty or invalid 'machine_id_code' found in downtime event row {index}. Skipping")
                continue

            machine_id = machine_code_to_id_map.get(machine_code)

            if machine_id is None:
                print(f"Warning: Machine '{machine_code}' for downtime event not found in database. Skipping row {index}")
                continue

            start_time = parse_datetime(row['start_time'])
            end_time = parse_datetime(row['end_time'])

            if start_time is None or end_time is None:
                print(f"Warning: Invalid start_time or end_time for the downtime event for machine '{machine_code}', skipping row {index}.")
                continue

            downtime_events_to_add.append(DowntimeEvent(
                machine_id = machine_id,
                start_time = start_time,
                end_time = end_time,
                reason = row['reason']
            ))
        
        db.add_all(downtime_events_to_add)
        db.commit()
        print(f"seeded {len(downtime_events_to_add)} downtime events from CSV.")

        # Note: ScheduledTask data will be populated by scheduler itself (Task 1.5.3)
        # No need to read it directly from a CSV here.

        print("\n--- Data seeding complete! ---")
    
    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

