import collections
from collections import defaultdict
import logging
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any, DefaultDict, cast
import pandas as pd
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import SessionLocal
from app.models import Machine, ProcessStep, ProductionOrder, ScheduledTask, DowntimeEvent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CONFIGURATION
DEFAULT_SOLVER_TIMEOUT_SECONDS = 120.0
BASE_SOLVER_TIMEOUT = 10.0
TIMEOUT_PER_TASK = 0.2

# -- Data Structures for OR Tools --
TaskData = Dict[str, Any] # type hint for dictionary representing a task for the solver
MachineInstanceData = Dict[str, Any]
TaskIdentifier = Tuple[str, int]

def load_and_prepare_data_for_ortools(
        db: Session,
        scheduling_anchor_time : datetime,
) -> Tuple[
    Dict[TaskIdentifier, TaskData],
    Dict[str, List[TaskIdentifier]], 
    List[Machine], 
    List[ScheduledTask], 
    List[DowntimeEvent]
]:
    
    """
    Loads data from the database, prepares it for the OR-Tools model,
    identifies in-progress jobs (by status), and filters production orders.
    Returns:
        all_tasks_for_solver: Dictionary of tasks (key=(order_id_code, step_num)) ready for OR-Tools.
        job_to_tasks: Map from job_id_code to its task_keys.
        active_machines: List of active Machine ORM objects.
        in_progress_scheduled_tasks: List of ScheduledTask ORM objects that are currently running.
        downtime_events_orm: List of DowntimeEvent ORM objects relevant for the planning horizon.
    """

    logging.info("Loading input data from the database and preparing for OR-Tools... ")
    
    try:
        # Fetch data
        active_machines = db.query(Machine).filter(Machine.is_active==True).all()

        # -- Dynamic job pool selection: Fetch only 'Pending' or 'Queued' orders --
        production_orders_orm = db.query(ProductionOrder).filter(
            ProductionOrder.current_status.in_(['Pending', 'Queued'])
        ).order_by(ProductionOrder.priority, ProductionOrder.arrival_time).all()

        process_steps_orm = db.query(ProcessStep).all()

        # -- Modeling Maintenance and Unplanned Downtime: Fetch relevant Downtime events --
        downtime_events_orm = db.query(DowntimeEvent).filter(
            DowntimeEvent.end_time > scheduling_anchor_time # Only future or ongoing downtime
        ).all()

        # -- Handling In-Progress Jobs: Identify tasks with status 'In Progress' ---
        # if status is "In Progress", we assume ScheduledTask.start_time is its actual start
        in_progress_scheduled_tasks = db.query(ScheduledTask).filter(
            ScheduledTask.status == "In Progress"
        ).all()
        logging.info(f"Found {len(in_progress_scheduled_tasks)} in-progress tasks based on status.")

        if not active_machines:
            logging.warning("No active machines found. Cannot schedule")
            return {}, {}, [], [], []
        if not process_steps_orm:
            logging.warning("No process steps found. Cannot Schedule.")
            # still return machines, and in-progress tasks, as they are part of the state
            return {}, {}, active_machines, in_progress_scheduled_tasks, downtime_events_orm
        if not production_orders_orm and not in_progress_scheduled_tasks:
            logging.info("No new production orders or in-progress tasks to schedule/monitor.")
            return {}, {}, active_machines, in_progress_scheduled_tasks, downtime_events_orm
        

        # Data structures for loookup
        machines_by_id = {m.id: m for m in active_machines}
        machines_by_type: Dict[str, List[Machine]] = collections.defaultdict(list)
        for m in active_machines:
            machines_by_type[cast(str, m.machine_type)].append(m)

        process_steps_by_id = {ps.id: ps for ps in process_steps_orm}

        process_steps_by_route: Dict[str, Dict[int, ProcessStep]] = collections.defaultdict(
            lambda: collections.defaultdict(ProcessStep)
        )
        for ps_obj in process_steps_orm:
            route_id_key = cast(str, ps_obj.product_route_id)
            step_num_key = cast(int, ps_obj.step_number)
            process_steps_by_route[route_id_key][step_num_key] = ps_obj
        
        production_orders_by_id = {order.id: order for order in production_orders_orm}
        production_orders_by_code = {cast(str, order.order_id_code): order for order in production_orders_orm}

        
        # OR-Tools input structures
        all_tasks_for_solver = {}
        job_to_tasks = collections.defaultdict(list) # changed job_to_tasks key to order_id_code for consistency
        job_next_available_time = collections.defaultdict(lambda: scheduling_anchor_time) # track last completed/in-progress step for each production order to enforce precedence
        job_last_fixed_task_key = {} # store task_key of the last fixed task for a job

        # 1. Process in-progress tasks first to establish fixed intervals and next available times
        for ip_task in in_progress_scheduled_tasks:
            # need to get the prodctionorder and process step objects via their ids
            order = production_orders_by_id.get(ip_task.production_order_id)
            process_step = process_steps_by_id.get(ip_task.process_step_id)
            assigned_machine = machines_by_id.get(ip_task.assigned_machine_id)

            if not order or not process_step or not assigned_machine:
                logging.warning(f"In-Progress task {ip_task.id} references missing ProductionOrder, ProcessStep or Machine. Skipping.")
                continue

            order_id_code = cast(str, order.order_id_code)
            start_time_actual = cast(datetime, ip_task.start_time) # the start time in the db is now the actual start for in-progress tasks
            if isinstance(ip_task.scheduled_duration_mins, int):
                duration = ip_task.scheduled_duration_mins
            else:
                duration = cast(int, ip_task.scheduled_duration_mins) if isinstance(ip_task.scheduled_duration_mins, int) else int(getattr(ip_task, "scheduled_duration_mins", 0))
            end_time_actual = cast(datetime, ip_task.end_time)
            if not isinstance(end_time_actual, datetime):
                end_time_actual = datetime.fromisoformat(str(end_time_actual))

            if start_time_actual is None: # shouldn't happen for in progress status
                logging.warning(f"In-Progress task {ip_task.id} has status 'In Progress' but no start_time. Treating as ready now.")
                start_time_actual = scheduling_anchor_time
                end_time_actual = scheduling_anchor_time + timedelta(minutes=duration)
            
            # Calculate offsets relative to the scheduling anchor time
            start_offset = int((start_time_actual - scheduling_anchor_time).total_seconds()//60)
            end_offset = int((end_time_actual - scheduling_anchor_time).total_seconds()//60)

            # Ensures offsets are non-negative for the solver. If task started before anchor, start_offset=0
            if start_offset < 0:
                logging.debug(f"Adjusting negative start-offset ({start_offset}) for fixed task {ip_task.id} to 0.")
                start_offset=0

            # Recalculate duration from adjusted offsets for solver's perspective
            adjusted_duration = end_offset - start_offset
            if adjusted_duration < 1: adjusted_duration = 1 # duration must be atleast 1 for solver

            task_key: TaskIdentifier = (order_id_code, cast(int, process_step.step_number))
            all_tasks_for_solver[task_key] = {
                'production_order_id': cast(int, order.id),
                'job_id_code': order_id_code,
                'step': cast(int, process_step.step_number),
                'process_step_id': cast(int, process_step.id), # Cast here
                'assigned_machine_id': cast(int, assigned_machine.id), # Cast here
                'machine_type': cast(str, assigned_machine.machine_type), # Cast here
                'duration': adjusted_duration, # use adjusted duration for solver
                'start_offset_mins': start_offset,
                'end_offset_mins': end_offset,
                'process_step_name': cast(str, process_step.step_name), # Cast here
                'is_fixed': True, # mark this task as fixed for solver
                'scheduled_task_db_id': cast(int, ip_task.id) # keep reference to the DB object ID
            }
            job_to_tasks[order_id_code].append(task_key)

            # next available time for this job is when the current in-progress task finishes
            job_next_available_time[order_id_code] = end_time_actual
            job_last_fixed_task_key[order_id_code] = task_key

        
        # 2. Process new/pending production orders and future steps of in-progress jobs
        for order in production_orders_orm:
            order_id_code = cast(str, order.order_id_code)
            product_route_id = cast(str, order.product_route_id)
            quantity = cast(int, order.quantity_to_produce) if order.quantity_to_produce is not None else 1

            # start processing from the next step if this job already has fixed steps
            current_step_number_for_order = 0
            if order_id_code in job_last_fixed_task_key:
                last_fixed_step_key = job_last_fixed_task_key[order_id_code]
                current_step_number_for_order = last_fixed_step_key[1]

            order_arrival_time = cast(datetime, order.arrival_time) if order.arrival_time else scheduling_anchor_time
            job_next_time = job_next_available_time[order_id_code]
            earliest_task_start_time = max(order_arrival_time, job_next_time)

            if product_route_id in process_steps_by_route:
                sorted_steps_for_order = sorted([
                    ps_obj 
                    for ps_obj in process_steps_by_route[product_route_id].values()
                    if ps_obj.step_number > current_step_number_for_order
                ], key=lambda x: cast(int, x.step_number))

                #Recalculate start_offset_mins relative to scheduling_anchor-time for these dynamic tasks
                if earliest_task_start_time < scheduling_anchor_time:
                    start_offset_mins = 0
                else:
                    start_offset_mins = int((earliest_task_start_time - scheduling_anchor_time).total_seconds() // 60)

                for step_data in sorted_steps_for_order:
                    machine_type = cast(str, step_data.required_machine_type)

                    # check if there are any active machines of required type
                    if machine_type not in machines_by_type or not any(m.is_active for m in machines_by_type[machine_type]):
                        logging.warning(f"No active machine found for type '{machine_type}' required by job '{order_id_code}' step '{step_data.step_number}'. Skipping this task.")
                        continue

                    # get setup_time for this machine type from one of the machines of that type
                    base_duration_per_unit = cast(int, step_data.base_duration_per_unit_mins)
                    if base_duration_per_unit is None: base_duration_per_unit=0        

                    operation_duration = int(base_duration_per_unit*quantity)
                    if operation_duration < 1:operation_duration = 1

                    task_key = (order_id_code, cast(int, step_data.step_number))
                    all_tasks_for_solver[task_key] = {
                        'production_order_id': order.id,
                        'job_id_code': order_id_code,
                        'step': step_data.step_number,
                        'process_step_id': step_data.id,
                        'machine_type': machine_type,
                        'operation_duration': operation_duration, # Store ONLY the operation duration
                        'start_offset_mins': start_offset_mins,
                        'process_step_name': step_data.step_name,
                        'is_fixed': False
                    }
                    job_to_tasks[order_id_code].append(task_key)
            else:
                logging.warning(f"No process route found for product_route_id: {product_route_id} for job {order_id_code}. Skipping Job.")
        
        logging.info(f"Prepared {len(all_tasks_for_solver)} tasks for OR-Tools schedulingb (including fixed).")
        return all_tasks_for_solver, job_to_tasks, active_machines, in_progress_scheduled_tasks, downtime_events_orm
    
    except Exception as e:
        logging.error(f"Error during data loading or preparation for OR-Tools: {e}", exc_info=True)
        raise


