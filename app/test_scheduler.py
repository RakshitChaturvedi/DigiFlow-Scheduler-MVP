import sys
import os
import logging
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, cast
from sqlalchemy.sql.elements import BindParameter

# --- IMPORTANT: Adjust these paths based on your project structure ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.insert(0, project_root)

# Import the main scheduler functions and models
from app.scheduler import (
    load_and_prepare_data_for_ortools, 
    schedule_with_ortools, 
    save_scheduled_tasks_to_db
)
from app.models import ProductionOrder, ProcessStep, Machine, DowntimeEvent, JobLog, ScheduledTask

# Define the path to your mock_data directory
MOCK_DATA_DIR = os.path.join(project_root, 'mock_data')

# Configure logging to see solver output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper to parse CSV data from a file ---
def parse_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Parses a CSV file into a list of dictionaries, stripping BOM from headers."""
    data = []
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            # Read the header line first to check for BOM
            header_line = f.readline()
            if header_line.startswith('\ufeff'):
                header_line = header_line[1:]  # Strip the BOM if present
            
            # Use StringIO to re-create a file-like object with the stripped header
            full_content = header_line + f.read()
            csv_file_like = StringIO(full_content)
            reader = csv.DictReader(csv_file_like)
            
            print(f"DEBUG: CSV Reader fieldnames for {os.path.basename(file_path)}: {reader.fieldnames}")
            
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        logging.error(f"Mock CSV file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading mock CSV file {file_path}: {e}")
        raise
    return data

# --- Mock ORM Classes (matching your actual models) ---
class MockProductionOrder:
    def __init__(self, **kwargs):
        self.id = int(kwargs['id'])
        self.order_id_code = kwargs['order_id_code']
        self.product_route_id = kwargs['product_route_id']  # Keep as string to match scheduler logic
        self.quantity_to_produce = int(kwargs['quantity_to_produce'])
        self.priority = int(kwargs['priority'])
        self.arrival_time = datetime.strptime(kwargs['arrival_time'], '%d-%m-%Y %H:%M')
        self.due_date = datetime.strptime(kwargs['due_date'], '%d-%m-%Y %H:%M') if kwargs.get('due_date') and kwargs['due_date'].strip() else None
        self.current_status = kwargs['current_status']

class MockMachine:
    def __init__(self, **kwargs):
        self.id = int(kwargs['id'])
        self.machine_type = kwargs['machine_type']
        self.machine_id_code = kwargs['machine_id_code']
        self.machine_name = kwargs['machine_name']
        self.is_active = kwargs['is_active'].lower() == 'true'
        self.default_setup_time_mins = int(kwargs['default_setup_time_mins'])

class MockDowntimeEvent:
    def __init__(self, **kwargs):
        self.id = int(kwargs['id'])
        self.machine_id_code = kwargs['machine_id_code']
        self.machine_id = None
        self.start_time = datetime.strptime(kwargs['start_time'], '%d-%m-%Y %H:%M')
        self.end_time = datetime.strptime(kwargs['end_time'], '%d-%m-%Y %H:%M')
        self.reason = kwargs['reason']

class MockProcessStep:
    def __init__(self, **kwargs):
        self.id = int(kwargs['id'])
        self.product_route_id = kwargs['product_route_id']  # Keep as string
        self.step_number = int(kwargs['step_number'])
        self.step_name = kwargs.get('step_name', f"Step {kwargs['step_number']}")
        self.required_machine_type = kwargs['required_machine_type']
        self.base_duration_per_unit_mins = int(kwargs['base_duration_per_unit_mins'])
        self.setup_time_mins = int(kwargs.get('setup_time_mins', 0))

class MockJobLog:
    def __init__(self, **kwargs):
        self.id = int(kwargs.get('id', 0))
        self.production_order_id = int(kwargs['production_order_id'])
        self.step_number = int(kwargs['step_number'])
        self.machine_id = int(kwargs['machine_id']) if kwargs.get('machine_id') else None
        self.actual_start_time = datetime.strptime(kwargs['actual_start_time'], '%d-%m-%Y %H:%M') if kwargs.get('actual_start_time') else None
        self.actual_end_time = datetime.strptime(kwargs['actual_end_time'], '%d-%m-%Y %H:%M') if kwargs.get('actual_end_time') else None
        self.production_order = None  # Will be set after loading production orders

class MockScheduledTask:
    def __init__(self, **kwargs):
        self.id = int(kwargs.get('id', 0))
        self.production_order_id = int(kwargs['production_order_id'])
        self.process_step_id = int(kwargs['process_step_id'])
        self.assigned_machine_id = int(kwargs['assigned_machine_id'])
        self.start_time = kwargs['start_time']
        self.end_time = kwargs['end_time']
        self.scheduled_duration_mins = int(kwargs['scheduled_duration_mins'])
        self.status = kwargs['status']

# --- Mock Database Session ---
class MockDbSession:
    def __init__(self, production_orders_data: List[MockProductionOrder],
                 machines_data: List[MockMachine],
                 downtime_events_data: List[MockDowntimeEvent],
                 process_steps_data: List[MockProcessStep],
                 job_logs_data: List[MockJobLog] = None,
                 scheduled_tasks_data: List[MockScheduledTask] = None):
        
        self.production_orders_by_id = {po.id: po for po in production_orders_data}
        self.machines_by_id = {m.id: m for m in machines_data}
        self.downtime_events = downtime_events_data
        self.process_steps_by_id = {ps.id: ps for ps in process_steps_data}
        self.job_logs = job_logs_data or []
        self.scheduled_tasks = scheduled_tasks_data or []
        
        # Link job logs to production orders
        for log in self.job_logs:
            log.production_order = self.production_orders_by_id.get(log.production_order_id)

    def get(self, entity, pk):
        """Mocks Session.get() for a given entity and primary key."""
        if entity == ProductionOrder:
            return self.production_orders_by_id.get(pk)
        elif entity == Machine:
            return self.machines_by_id.get(pk)
        elif entity == ProcessStep:
            return self.process_steps_by_id.get(pk)
        return None

    def query(self, entity):
        """Mocks Session.query(). Returns a mock query object."""
        class MockQuery:
            def __init__(self, parent_session, entity):
                self._session = parent_session
                self._entity = entity
                self._current_data = []
                if entity == ProductionOrder:
                    self._current_data = list(parent_session.production_orders_by_id.values())
                elif entity == Machine:
                    self._current_data = list(parent_session.machines_by_id.values())
                elif entity == DowntimeEvent:
                    self._current_data = parent_session.downtime_events
                elif entity == ProcessStep:
                    self._current_data = list(parent_session.process_steps_by_id.values())
                elif entity == JobLog:
                    self._current_data = parent_session.job_logs
                elif entity == ScheduledTask:
                    self._current_data = parent_session.scheduled_tasks

            def filter(self, *conditions):
                """Mocks basic filter conditions."""
                filtered_data = []
                for item in self._current_data:
                    include_item = True
                    for condition in conditions:
                        # Handle different types of conditions
                        if hasattr(condition, 'left') and hasattr(condition, 'right'):
                            # Binary expression like Machine.is_active == True
                            attr_name = condition.left.key if hasattr(condition.left, 'key') else str(condition.left)
                            if hasattr(item, attr_name):
                                item_value = getattr(item, attr_name)

                                right = condition.right
                                # Unwrap SQLAlchemy BindParameter if present
                                if isinstance(right, BindParameter):
                                    right_value = right.value
                                else:
                                    right_value = right

                                op_name = condition.operator.__name__

                                if op_name == 'eq':
                                    if item_value != right_value:
                                        include_item = False
                                        break
                                elif op_name == 'in_op':
                                    if item_value not in right_value:
                                        include_item = False
                                        break
                                elif op_name == 'is_not':
                                    if item_value is right_value:
                                        include_item = False
                                        break
                                elif op_name == 'is_':
                                    if item_value is not right_value:
                                        include_item = False
                                        break
                                elif op_name == 'gt':
                                    if not (item_value > right_value):
                                        include_item = False
                                        break
                                else:
                                    print(f"[MOCK WARNING] Unsupported operator: {op_name}")
                                    include_item = False
                                    break

                        else:
                            # Simple attribute checks - this is a simplified mock
                            # For complex SQLAlchemy conditions, you'd need more sophisticated parsing
                            pass
                    
                    if include_item:
                        filtered_data.append(item)
                
                self._current_data = filtered_data
                return self

            def filter_by(self, **kwargs):
                """Mocks filter_by for keyword arguments."""
                filtered_data = []
                for item in self._current_data:
                    match = True
                    for key, value in kwargs.items():
                        if not hasattr(item, key) or getattr(item, key) != value:
                            match = False
                            break
                    if match:
                        filtered_data.append(item)
                self._current_data = filtered_data
                return self

            def update(self, values: Dict[str, Any]):
                """Mocks update operation."""
                updated_count = 0
                for item in self._current_data:
                    for key, value in values.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    updated_count += 1
                return updated_count

            def delete(self, synchronize_session=False):
                """Mocks delete operation."""
                deleted_count = len(self._current_data)
                # Remove from parent session's data structures
                if self._entity == ScheduledTask:
                    for item in self._current_data:
                        if item in self._session.scheduled_tasks:
                            self._session.scheduled_tasks.remove(item)
                return deleted_count

            def all(self):
                """Returns all currently filtered data."""
                return self._current_data

            def first(self):
                """Returns first item or None."""
                return self._current_data[0] if self._current_data else None

        return MockQuery(self, entity)

    def add(self, obj):
        """Mocks session.add()."""
        if isinstance(obj, MockScheduledTask):
            self.scheduled_tasks.append(obj)
        logging.debug(f"MockDbSession: Added {type(obj).__name__} to session")

    def commit(self):
        """Mocks session commit."""
        logging.info("MockDbSession: commit() called - changes committed to mock data")

    def rollback(self):
        """Mocks session rollback."""
        logging.warning("MockDbSession: rollback() called - changes discarded")

    def close(self):
        """Mocks session close."""
        logging.debug("MockDbSession: close() called")

# --- Main Test Function ---
def run_test_case():
    print("\n=== Running Scheduler Test Case with CSV Mock Data ===")

    # 1. Define scheduling anchor time
    anchor_time = datetime.now()
    print(f"Scheduling Anchor Time: {anchor_time.strftime('%d-%m-%Y %H:%M')}")

    # 2. Load Mock Data from CSV files
    print(f"Loading mock data from: {MOCK_DATA_DIR}")
    try:
        parsed_production_orders = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'production_job_schedule_mock_data.csv'))
        parsed_machines = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'machine_catalog_mock_data.csv'))
        parsed_downtime_events = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'downtime_events_mock_data.csv'))
        parsed_process_steps = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'process_route_mock_data.csv'))
        
        # Optional: Load job logs if you have them (for in-progress tasks)
        job_logs_file = os.path.join(MOCK_DATA_DIR, 'job_logs_mock_data.csv')
        parsed_job_logs = []
        if os.path.exists(job_logs_file):
            parsed_job_logs = parse_csv_data(job_logs_file)
            print(f"Loaded job logs from {job_logs_file}")
    except Exception as e:
        logging.error(f"Failed to load CSV data: {e}")
        return

    # 3. Convert to mock ORM objects
    mock_production_orders = [MockProductionOrder(**po) for po in parsed_production_orders]
    mock_machines = [MockMachine(**m) for m in parsed_machines]
    mock_downtime_events = [MockDowntimeEvent(**de) for de in parsed_downtime_events]
    mock_process_steps = [MockProcessStep(**ps) for ps in parsed_process_steps]
    mock_job_logs = [MockJobLog(**jl) for jl in parsed_job_logs]

    machine_lookup = {m.machine_id_code: m.id for m in mock_machines}

    for event in mock_downtime_events:
        if event.machine_id_code in machine_lookup:
            event.machine_id = machine_lookup[event.machine_id_code]
        else:
            raise ValueError(f"Unknown machine_id_code '{event.machine_id_code}' in downtime event ID {event.id}")

    print(f"Loaded:")
    print(f"  - {len(mock_production_orders)} Production Orders")
    print(f"  - {len(mock_machines)} Machines")
    print(f"  - {len(mock_downtime_events)} Downtime Events")
    print(f"  - {len(mock_process_steps)} Process Steps")
    print(f"  - {len(mock_job_logs)} Job Logs")

    # 4. Initialize Mock Database Session
    mock_db_session = MockDbSession(
        production_orders_data=mock_production_orders,
        machines_data=mock_machines,
        downtime_events_data=mock_downtime_events,
        process_steps_data=mock_process_steps,
        job_logs_data=mock_job_logs
    )

    print("\n=== Using Scheduler's Data Loading Function ===")
    
    # 5. Use the actual scheduler's data loading function
    try:
        all_tasks, job_to_tasks, machines_orm, downtime_events = load_and_prepare_data_for_ortools(
            db=mock_db_session,
            scheduling_anchor_time=anchor_time
        )
        
        print(f"Data prepared by scheduler:")
        print(f"  - {len(all_tasks)} tasks for scheduling")
        print(f"  - {len(job_to_tasks)} jobs with precedence constraints")
        print(f"  - {len(machines_orm)} active machines")
        print(f"  - {len(downtime_events)} downtime events")

        if not all_tasks:
            print("No tasks to schedule. Check your mock data and machine availability.")
            return

        # Debug: Print task details
        print("\n=== Task Details ===")
        for task_key, task_data in all_tasks.items():
            print(f"Task {task_key}:")
            print(f"  - Job: {task_data.job_id_code}, Step: {task_data.step}")
            print(f"  - Machine Type: {task_data.machine_type}")
            print(f"  - Duration: {task_data.operation_duration or task_data.duration} mins")
            print(f"  - Fixed: {task_data.is_fixed}")
            if task_data.is_fixed:
                print(f"  - Start Offset: {task_data.start_offset_mins} mins")
                print(f"  - Assigned Machine: {task_data.assigned_machine_id}")

    except Exception as e:
        logging.error(f"Failed to load and prepare data: {e}", exc_info=True)
        return

    print("\n=== Running OR-Tools Scheduler ===")
    
    # 6. Run the scheduler
    try:
        scheduled_tasks_output, makespan, solver_status = schedule_with_ortools(
            tasks=all_tasks,
            jobs_map=job_to_tasks,
            machines_orm=machines_orm,
            downtime_events=downtime_events,
            scheduling_anchor_time=anchor_time,
            db_session=mock_db_session,
            horizon=10080  # 1 week in minutes
        )

        print(f"\n=== Scheduler Results ===")
        print(f"Solver Status: {solver_status}")
        print(f"Makespan: {makespan:.1f} minutes ({makespan/60:.1f} hours)")
        print(f"Scheduled Tasks: {len(scheduled_tasks_output)}")

        if solver_status in ["OPTIMAL", "FEASIBLE"] and scheduled_tasks_output:
            print(f"\n=== Detailed Schedule ===")
            scheduled_tasks_output.sort(key=lambda x: x['start_time'])
            
            current_job = None
            for i, task in enumerate(scheduled_tasks_output, 1):
                if task['job_id_code'] != current_job:
                    if current_job is not None:
                        print("-" * 50)
                    current_job = task['job_id_code']
                    print(f"\nJOB: {current_job}")
                
                print(f"  Step {task['step_number']}: {task['start_time'].strftime('%H:%M')} - {task['end_time'].strftime('%H:%M')} "
                      f"(Machine {task['assigned_machine_id']}, {task['scheduled_duration_mins']}min, {task['status']})")

            # 7. Test saving to database (mock)
            print(f"\n=== Testing Database Save ===")
            try:
                save_scheduled_tasks_to_db(mock_db_session, scheduled_tasks_output)
                print("Successfully saved schedule to mock database")
                
                # Check final production order statuses
                print(f"\n=== Final Production Order Statuses ===")
                for po in mock_production_orders:
                    print(f"  {po.order_id_code}: {po.current_status}")
                    
            except Exception as e:
                logging.error(f"Failed to save schedule: {e}", exc_info=True)

        else:
            print(f"\nScheduling failed or returned no results.")
            print(f"Status: {solver_status}")
            if solver_status == "INFEASIBLE":
                print("The problem constraints cannot be satisfied. Check:")
                print("- Machine availability vs. required machine types")
                print("- Deadline constraints vs. task durations")
                print("- Downtime events vs. scheduling window")

    except Exception as e:
        logging.error(f"Scheduler execution failed: {e}", exc_info=True)

    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    run_test_case()