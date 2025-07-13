import pandas as pd
import numpy as np
import random

from sqlalchemy.orm.session import Session
from sqlalchemy import inspect

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Machine, ProcessStep, ProductionOrder, ScheduledTask, DowntimeEvent, JobLog, User

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
        db.query(DowntimeEvent).delete()
        db.query(JobLog).delete()
        db.query(ScheduledTask).delete()
        db.query(ProductionOrder).delete()
        db.query(ProcessStep).delete()
        db.query(Machine).delete()
        db.query(User).delete()
        db.commit()
        print("Existing data cleared.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

