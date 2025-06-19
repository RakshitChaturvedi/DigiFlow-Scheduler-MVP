import sys
import os
import logging
import csv
import collections
from io import StringIO # Still useful for internal string parsing if needed, but not for direct file
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, cast

# --- IMPORTANT: Adjust these paths based on your project structure ---
# Assuming:
# Project Root: DigiFlow/
# Your scheduler file: DigiFlow/app/scheduler.py
# This test file: DigiFlow/app/test_scheduler.py
# Your models file: DigiFlow/app/models.py
# Your mock data folder: DigiFlow/mock_data/

# Add project root to sys.path to allow imports like 'app.scheduler' and 'app.models'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.insert(0, project_root)

# Now you can import scheduler and models correctly
from app.scheduler import schedule_with_ortools, Machine, TaskData, ScheduledTask, DowntimeEvent
from app.models import ProductionOrder, ProcessStep # Import ProcessStep as well for mock data

# Define the path to your mock_data directory
MOCK_DATA_DIR = os.path.join(project_root, 'mock_data') # Assumes mock_data is sibling to 'app'


# Configure logging to see solver output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper to parse CSV data from a file ---
def parse_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Parses a CSV file into a list of dictionaries, stripping BOM from headers."""
    data = []
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            # Read the header line first to check for BOM
            header_line = f.readline()
            if header_line.startswith('\ufeff'):
                header_line = header_line[1:] # Strip the BOM if present
            
            # Use StringIO to re-create a file-like object with the stripped header
            # so DictReader gets the correct headers
            full_content = header_line + f.read()
            csv_file_like = StringIO(full_content)

            reader = csv.DictReader(csv_file_like)
            
            # --- Optional: Add a debug print for the actual keys DictReader sees ---
            print(f"DEBUG: CSV Reader actual fieldnames for {os.path.basename(file_path)}: {reader.fieldnames}")
            # --- End optional debug print ---

            for row in reader:
                data.append(row)
    except FileNotFoundError:
        logging.error(f"Mock CSV file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading mock CSV file {file_path}: {e}")
        raise
    return data

# --- Mock ORM Classes (simplified for testing) ---
# These are needed to represent the data loaded from CSV in an object-oriented way
# similar to how SQLAlchemy models behave.
class MockProductionOrder:
    def __init__(self, **kwargs):

        print(f"DEBUG: MockProductionOrder __init__ received kwargs keys: {kwargs.keys()}")
        print(f"DEBUG: Full kwargs received: {kwargs}") # Also print full kwargs for more detail

        self.id = int(kwargs['id'])
        self.order_id_code = kwargs['order_id_code']
        self.product_route_id = int(kwargs['product_route_id'])
        self.quantity_to_produce = int(kwargs['quantity_to_produce'])
        self.priority = int(kwargs['priority'])
        # Handle potential empty string for deadline
        self.arrival_time = datetime.strptime(kwargs['arrival_time'], '%d-%m-%Y %H:%M')
        self.due_date = datetime.strptime(kwargs['due_date'], '%d-%m-%Y %H:%M') if kwargs.get('due_date') else None
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
        self.machine_id = kwargs['machine_id_code']
        self.start_time = datetime.strptime(kwargs['start_time'], '%d-%m-%Y %H:%M')
        self.end_time = datetime.strptime(kwargs['end_time'], '%d-%m-%Y %H:%M')
        self.reason = kwargs['reason'] 

class MockProcessStep:
    def __init__(self, **kwargs):
        self.id = int(kwargs['id'])
        self.production_order_id = int(kwargs['product_route_id'])
        self.step_number = int(kwargs['step_number'])
        self.step_name = kwargs['step_name'] if kwargs.get('step_name') else None
        self.machine_type_required = kwargs['required_machine_type']
        self.duration_mins = int(kwargs['base_duration_per_unit_mins'])


# --- Mock Database Session ---
class MockDbSession:
    def __init__(self, production_orders_data: List[MockProductionOrder],
                 machines_data: List[MockMachine],
                 downtime_events_data: List[MockDowntimeEvent],
                 process_steps_data: List[MockProcessStep]):
        
        self.production_orders_by_id = {po.id: po for po in production_orders_data}
        self.machines_by_id = {m.id: m for m in machines_data}
        self.downtime_events = downtime_events_data # Store as list for filtering
        self.process_steps_by_id = {ps.id: ps for ps in process_steps_data}
        
        # For query filtering and updates, we also need a way to mock the 'filter' and 'update' methods
        self._query_results = [] # Used for chaining filter and all

    def get(self, entity, pk):
        """Mocks Session.get() for a given entity and primary key."""
        if entity == ProductionOrder:
            return self.production_orders_by_id.get(pk)
        elif entity == Machine:
            return self.machines_by_id.get(pk)
        elif entity == ProcessStep:
            return self.process_steps_by_id.get(pk)
        return None # Or raise an error for unsupported entities

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

            def filter(self, *filters):
                """Mocks filter with basic support for '==' and 'in_' on object attributes."""
                filtered_data = []
                for item in self._current_data:
                    match = True
                    for f in filters:
                        # This is a very simplified mock of SQLAlchemy's filter
                        # It assumes filters are simple binary operations like 'attr == value' or 'attr.in_([values])'
                        if hasattr(f, 'compare') and hasattr(f.compare, '__name__'):
                            # Handle attribute comparisons from a column object (e.g., ProductionOrder.status)
                            attr_name = f.compare.__name__ # e.g., 'current_status'
                            if not hasattr(item, attr_name):
                                match = False
                                break
                            item_value = getattr(item, attr_name)
                            
                            if f.operator == '__eq__': # e.g., ==
                                if not (item_value == f.right):
                                    match = False
                                    break
                            elif hasattr(f.operator, '__name__') and f.operator.__name__ == 'in_op': # e.g., .in_
                                if item_value not in f.right:
                                    match = False
                                    break
                            # Add more filter logic as needed (e.g., !=, >, <)
                        else: # Fallback if filter structure is not simple attribute comparison
                            # For filter(ProductionOrder.id.in_(...)), f might be a BinaryExpression object
                            # This mock needs to know how to interpret it.
                            if hasattr(f, 'left') and hasattr(f.left, 'key') and hasattr(f, 'right'):
                                attr_name = f.left.key
                                if not hasattr(item, attr_name):
                                    match = False
                                    break
                                item_value = getattr(item, attr_name)
                                if f.operator == 'in_op' or f.operator.__name__ == 'in_op': # Check for in_ operator
                                    if item_value not in f.right:
                                        match = False
                                        break
                                elif f.operator == '__eq__':
                                    if not (item_value == f.right):
                                        match = False
                                        break
                            else:
                                logging.warning(f"Unsupported filter type in mock query: {f}")
                                pass # Assume it matches or log warning
                    if match:
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
                """Mocks update operation on the filtered data in the parent session's data."""
                updated_count = 0
                for item in self._current_data: # Iterate over the currently filtered items
                    original_item_id = item.id # Assuming 'id' is always present and unique
                    if self._entity == ProductionOrder and original_item_id in self._session.production_orders_by_id:
                        # Apply updates to the actual mock object stored in the session's map
                        actual_item = self._session.production_orders_by_id[original_item_id]
                        for key, value in values.items():
                            if hasattr(actual_item, key):
                                setattr(actual_item, key, value)
                        updated_count += 1
                    # Extend this logic for other entities if they need to be updated
                return updated_count

            def all(self):
                """Returns all currently filtered data."""
                return self._current_data

            def get(self, pk):
                """Mocks Query.get() for compatibility if still used in some parts."""
                for item in self._current_data:
                    if hasattr(item, 'id') and getattr(item, 'id') == pk:
                        return item
                return None
        
        return MockQuery(self, entity)

    def commit(self):
        """Mocks session commit."""
        logging.debug("MockDbSession: commit() called. Changes are in-memory.")
        pass

    def rollback(self):
        """Mocks session rollback."""
        logging.warning("MockDbSession: rollback() called. Changes discarded.")
        pass

    def close(self):
        """Mocks session close."""
        logging.debug("MockDbSession: close() called.")
        pass

# --- Main Test Case Function ---
def run_test_case():
    print("\n--- Running Scheduler Test Case (CSV Mock Data) ---")

    # 1. Define your scheduling anchor time
    anchor_time = datetime.now()
    print(f"Scheduling Anchor Time: {anchor_time.strftime('%d-%m-%Y %H:%M')}")

    # 2. Load Mock Data from CSV files
    print(f"Loading mock data from CSV files in: {MOCK_DATA_DIR}...")
    parsed_production_orders = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'production_job_schedule_mock_data.csv'))
    parsed_machines = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'machine_catalog_mock_data.csv'))
    parsed_downtime_events = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'downtime_events_mock_data.csv'))
    parsed_process_steps = parse_csv_data(os.path.join(MOCK_DATA_DIR, 'process_route_mock_data.csv'))

    # Convert parsed data to mock ORM objects
    mock_production_orders = [MockProductionOrder(**po) for po in parsed_production_orders]
    mock_machines = [MockMachine(**m) for m in parsed_machines]
    mock_downtime_events = [MockDowntimeEvent(**de) for de in parsed_downtime_events]
    mock_process_steps = [MockProcessStep(**ps) for ps in parsed_process_steps]

    print(f"Loaded {len(mock_production_orders)} Production Orders, {len(mock_machines)} Machines, {len(mock_downtime_events)} Downtime Events, {len(mock_process_steps)} Process Steps.")

    # 3. Initialize the Mock Database Session
    mock_db_session = MockDbSession(
        production_orders_data=mock_production_orders,
        machines_data=mock_machines,
        downtime_events_data=mock_downtime_events,
        process_steps_data=mock_process_steps
    )
    
    # 4. Prepare Tasks for OR-Tools using loaded data
    tasks: Dict[Tuple[str, int], TaskData] = {}
    jobs_map: Dict[str, List[Tuple[str, int]]] = collections.defaultdict(list)

    for ps_data in mock_process_steps:
        # Get associated production order to retrieve job_id_code and deadline
        po = mock_db_session.get(ProductionOrder, ps_data.production_order_id)
        if not po:
            logging.warning(f"Production Order with ID {ps_data.production_order_id} not found for Process Step {ps_data.id}.")
            continue
        
        # Determine if it's a "fixed" (in-progress) task based on a condition
        # For example, let's assume Process Step ID 101 for JOB_A is always fixed
        is_fixed_task = (ps_data.id == 101 and po.order_id_code == "JOB_A")
        
        task_identifier = (po.order_id_code, ps_data.step_number)
        
        task_data_instance = TaskData(
            production_order_id=po.id,
            job_id_code=po.order_id_code,
            step=ps_data.step_number,
            process_step_id=ps_data.id,
            machine_type=ps_data.machine_type_required,
            process_step_name=ps_data.step_name,
            is_fixed=is_fixed_task,
            operation_duration=ps_data.duration_mins,
            # For fixed tasks, provide specific start/duration/assigned machine
            start_offset_mins=-30 if is_fixed_task else None, # Example: started 30 mins before anchor
            duration=60 if is_fixed_task else None,            # Example: total 60 mins duration
            assigned_machine_id=1 if is_fixed_task else None,   # Example: assigned to machine 1

            earliest_start_mins=0 if not is_fixed_task else (anchor_time + timedelta(minutes=cast(int, task_data_instance.start_offset_mins)) - anchor_time).total_seconds() / 60
        )
        tasks[task_identifier] = task_data_instance
        jobs_map[po.order_id_code].append(task_identifier)

    # Sort jobs_map tasks to ensure correct precedence order for OR-Tools (by step number)
    for job_id_code in jobs_map:
        jobs_map[job_id_code].sort(key=lambda x: tasks[x].step)

    print(f"Total Tasks to Schedule: {len(tasks)}")
    print(f"Jobs for Precedence: {list(jobs_map.keys())}")

    # 5. Prepare Dummy In-Progress Tasks for the scheduler's horizon calculation
    # These are specific ORM-like objects representing ongoing tasks.
    in_progress_tasks = []
    # If the fixed task 'JOB_A', step 1 is truly in progress, represent it here.
    # Its end_time for the scheduler's horizon is important.
    fixed_task_data = tasks.get(('JOB_A', 1))
    if fixed_task_data and fixed_task_data.is_fixed:
        in_progress_tasks.append(
            ScheduledTask(
                production_order_id=fixed_task_data.production_order_id,
                process_step_id=fixed_task_data.process_step_id,
                assigned_machine_id=fixed_task_data.assigned_machine_id,
                start_time=anchor_time + timedelta(minutes=fixed_task_data.start_offset_mins),
                end_time=anchor_time + timedelta(minutes=fixed_task_data.start_offset_mins + fixed_task_data.duration),
                scheduled_duration_mins=fixed_task_data.duration,
                status="In Progress"
            )
        )
    print(f"In-Progress Tasks (for horizon): {len(in_progress_tasks)}")

    # 6. Downtime events are directly passed as loaded mock objects
    print(f"Downtime Events: {len(mock_downtime_events)}")

    # Call the scheduler with the mock DB session and all prepared data
    scheduled_tasks_output, makespan, solver_status = schedule_with_ortools(
        tasks,
        jobs_map,
        mock_machines, # Pass mock machines
        mock_downtime_events, # Pass mock downtime events
        anchor_time,
        mock_db_session, # Pass the mock DB session
        horizon = 100000
    )

    print("\n--- Scheduler Results ---")
    print(f"Solver Status: {solver_status}")
    print(f"Makespan: {makespan} minutes")
    print(f"Scheduled Tasks Count: {len(scheduled_tasks_output)}")

    if solver_status == "OPTIMAL" or solver_status == "FEASIBLE":
        print("\n--- Detailed Schedule Output ---")
        for task in scheduled_tasks_output:
            print(f"  Job {task['job_id_code']}, Step {task['step_number']}:")
            print(f"    Machine: {task['assigned_machine_id']}")
            print(f"    Start: {task['start_time'].strftime('%d-%m-%Y %H:%M')}")
            print(f"    End:   {task['end_time'].strftime('%d-%m-%Y %H:%M')}")
            print(f"    Duration: {task['scheduled_duration_mins']} mins")
            print(f"    Status: {task['status']}")
            print("-" * 30)
        
        # Verify status updates on mock production orders (if any were "Scheduled")
        print("\n--- Mock Production Order Statuses After Scheduling ---")
        for po_id, po in mock_db_session.production_orders_by_id.items():
            print(f"  PO ID: {po.id}, Order Code: {po.order_id_code}, Status: {po.current_status}")

    else:
        print("\nNo feasible schedule found.")
        print("Check logs for OR-Tools warnings/errors regarding infeasibility.")

if __name__ == "__main__":
    run_test_case()