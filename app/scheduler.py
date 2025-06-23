import collections
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, DefaultDict, Dict, List, Optional, Tuple, cast

import pandas as pd
from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

# Assuming these are defined in app/config.py
from app.config import BASE_SOLVER_TIMEOUT, TIMEOUT_PER_TASK
from app.database import SessionLocal
from app.models import DowntimeEvent, JobLog, Machine, ProcessStep, ProductionOrder, ScheduledTask

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- NEW: Dataclasses for Type Safety and Clarity ---
@dataclass
class TaskData:
    """A structured representation of a task for the solver."""
    production_order_id: int
    job_id_code: str
    step: int
    process_step_id: int
    machine_type: str
    process_step_name: str
    is_fixed: bool = False
    # For fixed tasks
    start_offset_mins: Optional[int] = None
    duration: Optional[int] = None
    assigned_machine_id: Optional[int] = None
    # For schedulable tasks
    operation_duration: Optional[int] = None
    earliest_start_mins: Optional[int] = None
    deadline_offset_mins: Optional[int] = None

TaskIdentifier = Tuple[str, int] # (job_id_code, step_number)

def load_and_prepare_data_for_ortools(
    db: Session,
    scheduling_anchor_time: datetime
) -> Tuple[Dict[TaskIdentifier, TaskData], Dict[str, List[TaskIdentifier]], List[Machine], List[DowntimeEvent]]:
    """
    Loads data, correctly handles in-progress tasks, and prepares data for OR-Tools.
    This is now robust and accounts for real-world states.
    """
    logging.info("Loading and preparing data for OR-Tools...")

    active_machines = db.query(Machine).filter(Machine.is_active == True).all()
    if not active_machines:
        logging.warning("No active machines found. Cannot create a schedule.")
        return {}, {}, [], []

    # --- FIX 1: DYNAMIC & CORRECT JOB POOL SELECTION ---
    # Fetch orders that are not yet fully completed.
    production_orders_orm = db.query(ProductionOrder).filter(
        ProductionOrder.current_status.in_(['Pending', 'Queued', 'In-Progress'])
    ).all()

    # --- FIX 2: ROBUST IN-PROGRESS & DOWNTIME HANDLING ---
    in_progress_logs = db.query(JobLog).filter(
        JobLog.actual_start_time.isnot(None),
        JobLog.actual_end_time.is_(None)
    ).all()
    future_downtime_events = db.query(DowntimeEvent).filter(DowntimeEvent.end_time > scheduling_anchor_time).all()

    # --- Data preparation using lookup dictionaries for efficiency ---
    process_steps_by_route: DefaultDict[str, Dict[int, ProcessStep]] = collections.defaultdict(dict)
    for ps in db.query(ProcessStep).all():
        process_steps_by_route[cast(str, ps.product_route_id)][cast(int, ps.step_number)] = ps

    all_tasks_for_solver: Dict[TaskIdentifier, TaskData] = {}
    job_to_tasks: DefaultDict[str, List[TaskIdentifier]] = collections.defaultdict(list)
    job_next_available_time: Dict[str, datetime] = {}
    
    # Process running tasks first to establish them as fixed constraints
    for log in in_progress_logs:
        order = log.production_order
        step_def = process_steps_by_route.get(order.product_route_id, {}).get(log.step_number)
        if not step_def: continue

        task_key = (order.order_id_code, log.step_number)
        start_offset = int((log.actual_start_time - scheduling_anchor_time).total_seconds() // 60)
        
        # Estimate remaining duration based on original plan
        op_duration = int(cast(int, step_def.base_duration_per_unit_mins or 0)) * int((order.quantity_to_produce or 1))
        setup_time = int(step_def.setup_time_mins or 0)
        total_original_duration = int(setup_time + op_duration)
        
        all_tasks_for_solver[task_key] = TaskData(
            production_order_id=order.id, 
            job_id_code=order.order_id_code, 
            step=log.step_number,
            process_step_id=step_def.id, 
            machine_type="", 
            process_step_name=step_def.step_name,
            is_fixed=True, 
            start_offset_mins=start_offset, 
            duration=total_original_duration,
            assigned_machine_id=log.machine_id
        )
        job_to_tasks[order.order_id_code].append(task_key)
        job_next_available_time[order.order_id_code] = log.actual_start_time + timedelta(minutes=total_original_duration)

    # Process all other pending jobs and future steps of in-progress jobs
    for order in production_orders_orm:
        order_id_code = order.order_id_code
        route_id = order.product_route_id
        
        # Determine the earliest this job can start its *next* schedulable step
        job_arrival = order.arrival_time or scheduling_anchor_time
        next_step_earliest_start = max(job_arrival, job_next_available_time.get(order_id_code, scheduling_anchor_time))
        start_offset_mins = max(0, int((next_step_earliest_start - scheduling_anchor_time).total_seconds() // 60))
        deadline_offset = int((order.due_date - scheduling_anchor_time).total_seconds() // 60) if order.due_date else None

        if str(route_id) in process_steps_by_route:
            for step_num, step_data in sorted(process_steps_by_route[str(route_id)].items()):
                task_key = (order_id_code, step_num)
                if task_key in all_tasks_for_solver: # Skip if it was an in-progress task
                    print(f"[SKIP] Duplicate task_key found: {task_key}")
                    continue
                
                base_per_unit = int(step_data.base_duration_per_unit_mins or 0)
                quantity = int(order.quantity_to_produce or 1)
                op_duration = max(1, base_per_unit * quantity)

                # DEBUG
                print(f"[DEBUG] Order {order_id_code}, Step {step_num}: base={base_per_unit}, qty={quantity} → duration={op_duration}")
                print("[DEBUG] route_id keys available:", list(process_steps_by_route.keys()))
                print(f"[DEBUG] checking route_id = {route_id}")


                all_tasks_for_solver[task_key] = TaskData(
                    production_order_id=order.id, 
                    job_id_code=order_id_code, 
                    step=step_num,
                    process_step_id=step_data.id, 
                    machine_type=step_data.required_machine_type,
                    process_step_name=step_data.step_name, 
                    is_fixed=False,
                    operation_duration=op_duration,
                    earliest_start_mins=start_offset_mins,
                    deadline_offset_mins=deadline_offset
                )
                job_to_tasks[order_id_code].append(task_key)
                print(f"[TASK ADDED] {task_key} → duration: {op_duration}")


    logging.info(f"Prepared {len(all_tasks_for_solver)} tasks for OR-Tools scheduling.")
    return all_tasks_for_solver, job_to_tasks, active_machines, future_downtime_events


def schedule_with_ortools(
    tasks: Dict[TaskIdentifier, TaskData],
    jobs_map: Dict[str, List[TaskIdentifier]],
    machines_orm: List[Machine],
    downtime_events: List[DowntimeEvent],
    scheduling_anchor_time: datetime,
    db_session: Session,
    horizon_override: Optional[int] = None
) -> Tuple[List[Dict], float, str]:
    model = cp_model.CpModel()
    
    machine_instances = {cast(int, m.id): m for m in machines_orm}
    machine_type_to_ids: DefaultDict[str, List[int]] = collections.defaultdict(list)
    for m in machines_orm:
        machine_type_to_ids[cast(str, m.machine_type)].append(cast(int, m.id))

    if horizon_override:
        horizon = horizon_override
    else:
        horizon = sum(t.duration or t.operation_duration or 0 for t in tasks.values()) + 2880 # 2-day buffer

    task_intervals: Dict[TaskIdentifier, cp_model.IntervalVar] = {}
    task_assignment_vars: Dict[Tuple[TaskIdentifier, int], cp_model.BoolVar] = {}
    intervals_on_specific_machine = collections.defaultdict(list)


    for task_key, task_data in tasks.items():
        if task_data.is_fixed:
            task_intervals[task_key] = model.NewFixedSizeIntervalVar(
                cast(int, task_data.start_offset_mins), cast(int, task_data.duration), f"fixed_{task_key}"
            )
        else:
            # Schedulable task
            start = model.NewIntVar(cast(int, task_data.earliest_start_mins), horizon, f"start_{task_key}")
            duration_val = cast(int, task_data.operation_duration)            
            end = model.NewIntVar(0, horizon, f"end_{task_key}")
            
            selected_interval = None
            possible_machine_ids = machine_type_to_ids.get(task_data.machine_type, [])
            literals = []

            for machine_id in possible_machine_ids:
                assign_var = model.NewBoolVar(f"assign_{task_key}_to_{machine_id}")
                literals.append(assign_var)
                task_assignment_vars[(task_key, machine_id)] = assign_var
            if literals:
                model.AddExactlyOne(literals)
            
            for machine_id in possible_machine_ids:
                assign_var = task_assignment_vars[(task_key, machine_id)]
                # Create an optional interval for this task on this specific machine, this interval is only 'present' (active) if assign_var is true

                setup_time = machine_instances[machine_id].default_setup_time_mins or 0
                total_duration = duration_val + setup_time

                machine_task_interval = model.NewOptionalIntervalVar(
                    start=start,
                    size=total_duration,
                    end=end,
                    is_present=assign_var,
                    name=f"interval_{task_key}_on_m{machine_id}"
                )
                intervals_on_specific_machine[machine_id].append(machine_task_interval) 

                if selected_interval is None:
                    selected_interval = machine_task_interval

            if selected_interval:
                task_intervals[task_key] = selected_interval

    # --- ADD CONSTRAINTS ---
    # 1. Precedence
    for job_id, steps in jobs_map.items():
        steps.sort(key=lambda x: x[1])
        for i in range(len(steps) - 1):
            if steps[i] in task_intervals and steps[i+1] in task_intervals:
                model.Add(task_intervals[steps[i+1]].StartExpr() >= task_intervals[steps[i]].EndExpr())
    
    # 2. No-Overlap & Machine-Specific Setup Time

    for machine_id, interval_list in intervals_on_specific_machine.items():
        if interval_list:
            model.AddNoOverlap(interval_list)
    
    # Add downtime intervals to the same structure
    for event in downtime_events:
        mid = event.machine_id
        if mid in machine_instances:
            start_offset = max(0, int((event.start_time - scheduling_anchor_time).total_seconds() // 60))
            duration = int((event.end_time - event.start_time).total_seconds() // 60)
            if duration > 0:
                interval = model.NewFixedSizeIntervalVar(start_offset, duration, f"downtime_{event.id}")
                intervals_on_specific_machine[mid].append(interval)

    """
    for machine_id, machine in machine_instances.items():
        intervals_on_this_machine = []
        for task_key, task_data in tasks.items():
            if task_data.is_fixed:
                if task_data.assigned_machine_id == machine_id:
                    intervals_on_this_machine.append(task_intervals[task_key])
            elif (task_key, machine_id) in task_assignment_vars:
                assign_var = task_assignment_vars[(task_key, machine_id)]
                
                # --- FIX 3: MACHINE-SPECIFIC SETUP TIME ---
                setup_time = machine.default_setup_time_mins or 0
                actual_op_duration = cast(int, task_data.operation_duration)
                
                duration_with_setup_val = actual_op_duration + setup_time
                duration_with_setup_var = model.NewIntVar(
                    duration_with_setup_val,
                    duration_with_setup_val,
                    f"duration_{task_key}_on_m{machine_id}_with_setup"
                )
                
                duration_for_opt_interval = model.NewIntVar(
                    actual_op_duration,
                    actual_op_duration,
                    f"duration_{task_key}_on_m{machine_id}_NO_SETUP"
                )
                
                opt_interval = model.NewOptionalIntervalVar(
                    start = task_intervals[task_key].StartExpr(), 
                    end=task_intervals[task_key].EndExpr(), 
                    size=duration_with_setup_var, 
                    is_present=assign_var, 
                    name= f"opt_{task_key}_on_{machine_id}"
                )
                intervals_on_this_machine.append(opt_interval)
                # Link the main task's duration to this choice
                model.Add(task_intervals[task_key].EndExpr() == opt_interval.EndExpr()).OnlyEnforceIf(assign_var)
        
        # Add downtime events for this machine
        for event in downtime_events:
            if event.machine_id == machine_id:
                start_offset = max(0, int((event.start_time - scheduling_anchor_time).total_seconds() // 60))
                duration = int((event.end_time - event.start_time).total_seconds() // 60)
                if duration > 0:
                    intervals_on_this_machine.append(model.NewFixedSizeIntervalVar(start_offset, duration, f"downtime_{event.id}"))
        
        if intervals_on_this_machine:
            model.AddNoOverlap(intervals_on_this_machine)
    """

    # --- FIX 4: ESSENTIAL FEATURE - DEADLINE CONSTRAINTS ---
    all_orders = {task.production_order_id: task for task in tasks.values()}
    for order_id, task in all_orders.items():
        order = db_session.get(ProductionOrder, task.production_order_id)
        if order and order.due_date:
            last_step_key = jobs_map[order.order_id_code][-1]
            deadline_offset = int((order.due_date - scheduling_anchor_time).total_seconds() // 60)

            if deadline_offset > 0:
                if last_step_key not in task_intervals:
                    logging.error(f"Deadline constraint target {last_step_key} not found in task_intervals. Task may have been skipped.")
                else:
                    model.Add(task_intervals[last_step_key].EndExpr() <= deadline_offset)
                    logging.info(f"Added deadline constraint for job {order.order_id_code} at minute {deadline_offset}.")


    # --- OBJECTIVE & SOLVER ---
    makespan = model.NewIntVar(0, horizon, 'makespan')
    if task_intervals:
        model.AddMaxEquality(makespan, [iv.EndExpr() for iv in task_intervals.values()])
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = BASE_SOLVER_TIMEOUT + (len(tasks) * TIMEOUT_PER_TASK)
    status = solver.Solve(model)
    status_name = solver.StatusName(status)

    # --- EXTRACT RESULTS ---
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule_output = []
        for task_key, task_data in tasks.items():
            if task_key not in task_intervals: continue
            
            assigned_machine_id = None
            if task_data.is_fixed:
                assigned_machine_id = task_data.assigned_machine_id
            else:
                for m_id in machine_type_to_ids.get(task_data.machine_type, []):
                    if (task_key, m_id) in task_assignment_vars and solver.Value(task_assignment_vars[(task_key, m_id)]) == 1:
                        assigned_machine_id = m_id
                        break
            
            if assigned_machine_id is None: continue
            
            start_mins = solver.Value(task_intervals[task_key].StartExpr())
            duration = solver.Value(task_intervals[task_key].SizeExpr())
            
            schedule_output.append({
                "production_order_id": task_data.production_order_id,
                "process_step_id": task_data.process_step_id,
                "assigned_machine_id": assigned_machine_id,
                "start_time": scheduling_anchor_time + timedelta(minutes=start_mins),
                "end_time": scheduling_anchor_time + timedelta(minutes=start_mins + duration),
                "scheduled_duration_mins": duration,
                "status": "In Progress" if task_data.is_fixed else "Scheduled",
                "job_id_code": task_data.job_id_code,
                "step_number": task_data.step
            })
        schedule_output.sort(key=lambda x: x['start_time'])
        return schedule_output, solver.Value(makespan), status_name
    else:
        logging.error(f"Scheduling failed with status: {status_name}. The system will not update the current schedule.")
        return [], 0.0, status_name

def save_scheduled_tasks_to_db(db: Session, scheduled_tasks_data: List[Dict]):
    """Atomically updates the schedule in the database."""
    logging.info(f"Saving {len(scheduled_tasks_data)} tasks to the database...")
    try:

        allowed_keys = {
            'production_order_id',
            'process_step_id',
            'assigned_machine_id',
            'start_time',
            'end_time',
            'scheduled_duration_mins',
            'status'
        }

        # --- FIX 5: ROBUST DB SAVE LOGIC ---
        # Get all existing schedulable tasks for potential deletion
        existing_tasks_map = {
            (t.production_order_id, t.process_step_id): t
            for t in db.query(ScheduledTask).filter(ScheduledTask.status != 'Completed')
        }
        
        newly_scheduled_po_ids = set()
        
        for task_data in scheduled_tasks_data:
            po_id = task_data['production_order_id']
            ps_id = task_data['process_step_id']

            task_to_update = existing_tasks_map.pop((po_id, ps_id), None)

            if task_to_update:
                # This is an existing task (likely was 'In-Progress'), update its details
                task_to_update.assigned_machine_id = task_data['assigned_machine_id']
                task_to_update.start_time = task_data['start_time']
                task_to_update.end_time = task_data['end_time']
                task_to_update.scheduled_duration_mins = task_data['scheduled_duration_mins']
                task_to_update.status = task_data['status']
            else:
                # This is a new task to be scheduled
                filtered_data = {k: v for k, v in task_data.items() if k in allowed_keys}
                db.add(ScheduledTask(**filtered_data))

            if task_data['status'] == 'Scheduled':
                newly_scheduled_po_ids.add(po_id)


        # Delete old 'Scheduled' tasks that were not part of the new schedule
        for old_task in existing_tasks_map.values():
            if old_task.status == 'Scheduled':
                db.delete(old_task)

        # Update parent ProductionOrder statuses
        if newly_scheduled_po_ids:
            db.query(ProductionOrder).filter(
                ProductionOrder.id.in_(newly_scheduled_po_ids),
                ProductionOrder.current_status == 'Pending'
            ).update({'current_status': 'Scheduled'}, synchronize_session=False)

        db.commit()
        logging.info("Successfully committed new schedule to the database.")
    except Exception as e:
        logging.error(f"Database error during schedule save. Rolling back transaction.", exc_info=True)
        db.rollback()
        raise


def main():
    """Main function to orchestrate the scheduling process."""
    logging.info("Optimal (OR-Tools) Scheduler script started.")
    db: Session = SessionLocal()
    current_real_time_anchor = datetime.now()
    
    try:
        all_tasks, job_to_tasks, machines_orm, downtime_events = load_and_prepare_data_for_ortools(db, current_real_time_anchor)
        
        if not all_tasks:
            logging.info("No tasks to schedule. Exiting.")
            return

        orders = {o.id: o for o in db.query(ProductionOrder).all()}
        for k, t in all_tasks.items():
            print(f"{k}: duration={t.operation_duration}, quantity={orders[t.production_order_id].quantity_to_produce}")

        optimal_schedule, makespan, status = schedule_with_ortools(
            all_tasks, job_to_tasks, machines_orm, downtime_events, current_real_time_anchor, db
        )
        
        if optimal_schedule:
            logging.info(f"Schedule found with status '{status}'. Makespan: {makespan / 60:.2f} hours")
            save_scheduled_tasks_to_db(db, optimal_schedule)
            pd.DataFrame(optimal_schedule).to_csv('optimal_schedule_output.csv', index=False)
            logging.info("Detailed schedule saved to 'optimal_schedule_output.csv' for review.")
        else:
            logging.error(f"Scheduling did not yield a usable plan. Status: {status}. The existing schedule remains in effect.")
            
    except Exception as e:
        logging.critical(f"A critical error occurred in the main scheduling process.", exc_info=True)
    finally:
        db.close()
        logging.info("Scheduler script finished.")

if __name__ == "__main__":
    main()

