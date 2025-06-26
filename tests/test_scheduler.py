import collections
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, DefaultDict, Dict, List, Tuple, cast

# --- IMPORTANT: Add the project root to the Python path ---
# This allows us to import from the 'app' module correctly.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import the ACTUAL functions and models to be tested ---
from backend.app.models import (DowntimeEvent, JobLog, Machine, ProcessStep,
                           ProductionOrder, ScheduledTask)
from backend.app.enums import OrderStatus
from backend.app.scheduler import (load_and_prepare_data_for_ortools,
                               schedule_with_ortools, save_scheduled_tasks_to_db)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Mock Database Setup ---
class MockORM:
    """A base class to easily create mock objects from dictionaries."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Add relationships for back-population
        if 'production_order' not in kwargs:
            self.production_order = None

# Define mock classes that inherit from MockORM for simplicity
class MockMachine(MockORM): pass
class MockDowntimeEvent(MockORM): pass
class MockProcessStep(MockORM): pass
class MockJobLog(MockORM): pass

@dataclass
class MockProductionOrder:
    id: int
    order_id_code: str
    product_route_id: str
    quantity_to_produce: int
    current_status: OrderStatus
    arrival_time: datetime
    due_date: datetime

class MockDbSession:
    def get(self, model_class, pk):
        # Mimics SQLAlchemy 2.0 style db.get(Model, pk)
        items = self._data.get(model_class, [])
        for item in items:
            if hasattr(item, "id") and getattr(item, "id") == pk:
                return item
        return None

    """A mock database session that simulates querying and committing."""
    def __init__(self, initial_data: Dict[type, List[MockORM]]):
        # Create a copy of the data to keep the test isolated
        self._data = initial_data.copy()
    
    def query(self, entity_class):
        class MockQuery:
            def __init__(self, parent_session, entity_cls):
                self._session = parent_session
                self._entity_class = entity_cls
                self._data = list(parent_session._data.get(entity_cls, []))

            def filter(self, *criterion):
                # Simplified filter for this test's needs
                if not criterion: return self
                
                for cond in criterion:
                    column_name = cond.left.key
                    operator = cond.operator.__name__
                    
                    if operator == 'in_op':
                        # The values are the Enum members themselves. Get their string values.
                        values_to_match = {s.value if hasattr(s, "value") else s for s in cond.right.value}
                        self._data = [item for item in self._data if (val := getattr(item, column_name)) in values_to_match or (hasattr(val, "value") and val.value in values_to_match)]
                    elif operator == 'is_':
                         self._data = [item for item in self._data if getattr(item, column_name, None) is None]
                return self
            
            def update(self, values, synchronize_session=None):
                """Mocks the update method."""
                for item in self._data:
                    for key, value in values.items():
                        if hasattr(item, key):
                            setattr(item, key, value)

            def all(self):
                return self._data
            
            def first(self):
                return self._data[0] if self._data else None
            
            def get(self, pk):
                for item in self._data:
                    if hasattr(item, 'id') and item.id == pk:
                        return item
                return None

        return MockQuery(self, entity_class)
    
    def add(self, obj):
        entity_class = type(obj)
        if entity_class not in self._data: self._data[entity_class] = []
        self._data[entity_class].append(obj)
    
    def commit(self): pass # In-memory changes are instant
    def refresh(self, obj): pass
    def rollback(self): pass
    def close(self): pass


def test_scheduler_updates_order_status():
    """
    Tests that the scheduler correctly updates a ProductionOrder's status
    from 'Pending' to 'Scheduled' after a successful run.
    """
    print("\n--- Running Test: Scheduler Status Update ---")

    # 1. Define Test Parameters
    anchor_time = datetime.now(timezone.utc)
    print(f"Scheduling Anchor Time: {anchor_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # 2. Create Mock Data: One 'Pending' order
    mock_machines = [
        MockMachine(id=1, machine_id_code="CNC-01", machine_type="CNC", default_setup_time_mins=15, is_active=True),
        MockMachine(id=2, machine_id_code="EDM-01", machine_type="EDM", default_setup_time_mins=30, is_active=True),
    ]
    mock_process_steps = [
        MockProcessStep(id=101, product_route_id="ROUTE-A", step_number=1, step_name="CNC Work", required_machine_type="CNC", base_duration_per_unit_mins=10, setup_time_mins=15),
        MockProcessStep(id=102, product_route_id="ROUTE-A", step_number=2, step_name="EDM Work", required_machine_type="EDM", base_duration_per_unit_mins=30, setup_time_mins=30),
    ]
    
    # The order that should be updated
    order_to_update = MockProductionOrder(
        id=1, 
        order_id_code="JOB-PENDING-01", 
        product_route_id="ROUTE-A", 
        quantity_to_produce=5, 
        current_status=OrderStatus.PENDING, 
        arrival_time=anchor_time, 
        due_date=anchor_time + timedelta(days=2)
    )
    
    initial_data = {
        Machine: mock_machines,
        ProcessStep: mock_process_steps,
        ProductionOrder: [order_to_update],
        JobLog: [], # No in-progress jobs for this simple case
        DowntimeEvent: [],
        ScheduledTask: []
    }

    # 3. Initialize the Mock Database Session
    mock_db = MockDbSession(initial_data)
    print("Mock database created with 1 'Pending' Production Order.")

    # 4. Call the REAL data preparation function from scheduler.py
    all_tasks, job_to_tasks, active_machines, downtime_events = load_and_prepare_data_for_ortools(
        db=mock_db, 
        scheduling_anchor_time=anchor_time
    )

    # 5. Call the REAL scheduler function
    optimal_schedule, makespan, solver_status = schedule_with_ortools(
        tasks=all_tasks, jobs_map=job_to_tasks, machines_orm=active_machines,
        downtime_events=downtime_events, scheduling_anchor_time=anchor_time, db_session=mock_db
    )

    # 6. Call the REAL save function to trigger the status update
    if optimal_schedule:
        save_scheduled_tasks_to_db(mock_db, optimal_schedule)
    else:
        assert False, "Scheduler failed to produce a schedule."

    # 7. Assert and Verify the Outcome
    print("\n--- Verifying Results ---")
    
    assert solver_status in ["OPTIMAL", "FEASIBLE"], f"Solver failed. Status: {solver_status}"
    
    # THE CRITICAL ASSERTION: Check if the order's status was updated in our mock data
    final_order_status = order_to_update.current_status
    
    print(f"Checking status for Order ID {order_to_update.id} ('{order_to_update.order_id_code}')...")
    print(f"  - Initial Status: {OrderStatus.PENDING.value}")
    print(f"  - Final Status:   {final_order_status.value}")
    
    assert final_order_status == OrderStatus.SCHEDULED, \
        f"Order status was not updated correctly! Expected '{OrderStatus.SCHEDULED.value}', but got '{final_order_status.value}'."
    
    print("\n✅ Test case passed successfully!")

if __name__ == "__main__":
    test_scheduler_updates_order_status()

