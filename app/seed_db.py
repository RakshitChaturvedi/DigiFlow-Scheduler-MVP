import pandas as pd
import numpy as np
from sqlalchemy.orm.session import Session
from app.database import SessionLocal, engine
from app.models import Machine, ProcessStep, ProductionOrder, ScheduledTask
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DATA_PATH = os.path.join(BASE_DIR, 'mock_data')

MACHINE_CSV = os.path.join(MOCK_DATA_PATH, 'machine_catalog_mock_data.csv')
PROCESS_STEP_CSV = os.path.join(MOCK_DATA_PATH, 'process_route_mock_data.csv')
PRODUCTION_ORDER_CSV = os.path.join(MOCK_DATA_PATH, 'production_job_schedule_mock_data.csv')

def seed_data():
    db: Session = SessionLocal()

    try:
        print("--- Starting data seeding ---")

        # 1. Clear existing data to ensure a fresh seed

        # IMPORTANT: Delete in reverse order of foreign key dependency
        # Scheduled Task depends on all 3
        # Production nothing
        # Process on nothing
        # Machine on nothing
        print("Clearing existing data...")
        db.query(ScheduledTask).delete()
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
        print("CSVs read.") 

        # 3. Insert Machine Data
        print("Seeding Machine data...")
        for index, row in machines_df.iterrows():
            is_active_val = row['is_active']
            final_is_active: bool

            if not np.isscalar(is_active_val) or pd.isna(is_active_val):
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
                product_route_id = row['product_route_id'],
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
                product_route_id = row['product_route_id'],
                quantity_to_produce = row['quantity_to_produce'],
                priority = row['priority'],
                arrival_time = arrival_time,
                due_date = due_date,
                current_status = row['current_status']
            )
            db.add(order)
        db.commit()
        print(f"Seeded {len(production_orders_df)} production orders.")

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

