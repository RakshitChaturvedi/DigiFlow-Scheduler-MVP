import collections
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, DefaultDict, Dict, List, Optional, Tuple, cast

import pandas as pd
from ortools.sat.python import cp_model
from sqlalchemy import func
from sqlalchemy.orm import Session

# Assuming these are defined in app/config.py
from backend.app.config import BASE_SOLVER_TIMEOUT, TIMEOUT_PER_TASK, NON_WORKING_DAYS
from backend.app.database import SessionLocal
from backend.app.models import DowntimeEvent, JobLog, Machine, ProcessStep, ProductionOrder, ScheduledTask
from backend.app.schemas import ProductionOrderOut, ScheduledTaskResponse
from backend.app.enums import JobLogStatus, OrderStatus
from backend.app.utils import ensure_utc_aware

logger = logging.getLogger(__name__)

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
    earliest_start_time_actual: Optional[datetime] = None
    deadline_time_actual: Optional[datetime] = None

TaskIdentifier = Tuple[str, int] # (job_id_code, step_number)

def to_utc_aware(dt: datetime) -> datetime:
    """Converts datetime to UTC-aware if it's naive, returns as is if already aware"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def load_and_prepare_data_for_ortools(
    db: Session,
    scheduling_anchor_time: datetime
) -> Tuple[Dict[TaskIdentifier, TaskData], Dict[str, List[TaskIdentifier]], List[Machine], List[DowntimeEvent]]:
    """
    Loads data, correctly handles in-progress tasks, and prepares data for OR-Tools.
    This is now robust and accounts for real-world states.
    """
    scheduling_anchor_time = ensure_utc_aware(scheduling_anchor_time)
    logging.info("Loading and preparing data for OR-Tools...")

    active_machines = db.query(Machine).filter(Machine.is_active == True).all()
    if not active_machines:
        logging.warning("No active machines found. Cannot create a schedule.")
        return {}, {}, [], []

    # --- JOB POOL SELECTION ---
    # Fetch orders that are not yet fully completed.
    production_orders_orm = db.query(ProductionOrder).filter(
        ProductionOrder.current_status.in_([
            OrderStatus.PENDING.value,
            OrderStatus.SCHEDULED.value,
            OrderStatus.IN_PROGRESS.value
        ])
    ).all()

    last_completed_steps = {}

    process_step_id_to_num = {ps.id: ps.step_number for ps in db.query(ProcessStep.id, ProcessStep.step_number).all()}

    # find latest completed joblog for each relevent production order
    completed_logs = db.query(
        JobLog.production_order_id,
        func.max(JobLog.process_step_id).label('last_step_id') # get highest process step id
    ).filter(
        JobLog.status == JobLogStatus.COMPLETED,
        JobLog.production_order_id.in_([o.id for o in production_orders_orm])
    ).group_by(JobLog.production_order_id).all()

    # map the last completed step_id to its step_num
    for log in completed_logs:
        last_step_number = process_step_id_to_num.get(log.last_step_id, 0)
        last_completed_steps[log.producion_order_id] = last_step_number

    for order in production_orders_orm:
        if order.due_date:
            order.due_date = ensure_utc_aware(order.due_date)
        order.arrival_time = ensure_utc_aware(order.arrival_time)

    # --- IN-PROGRESS & DOWNTIME HANDLING ---
    in_progress_logs = db.query(JobLog).filter(
        JobLog.actual_start_time.isnot(None),
        JobLog.actual_end_time.is_(None)
    ).all()

    for log in in_progress_logs:
        log.actual_start_time = ensure_utc_aware(log.actual_start_time)

    all_downtime_events_raw = db.query(DowntimeEvent).all()
    future_downtime_events: List[DowntimeEvent] = []
    for event in all_downtime_events_raw:
        event_start_time_aware = ensure_utc_aware(event.start_time)
        event_end_time_aware = ensure_utc_aware(event.end_time)

        if event_end_time_aware > scheduling_anchor_time:
            event.start_time = max(event_start_time_aware, scheduling_anchor_time)
            event.end_time = event_end_time_aware
            future_downtime_events.append(event)

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
        actual_start_time_aware = to_utc_aware(log.actual_start_time)
        start_offset = int((log.actual_start_time_aware - scheduling_anchor_time).total_seconds() // 60)
        setup_time = int(getattr(step_def, 'setup_time_mins', 0) or 0)
        # Estimate remaining duration based on original plan
        op_duration = int(cast(int, step_def.base_duration_per_unit_mins or 0)) * int((order.quantity_to_produce or 1))
        total_original_duration = int(setup_time + op_duration)
        
        all_tasks_for_solver[task_key] = TaskData(
            production_order_id=order.id, 
            job_id_code=order.order_id_code, 
            step=log.step_number,
            process_step_id=step_def.id, 
            machine_type=step_def.required_machine_type, 
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
        start_scheduling_from_step = last_completed_steps.get(order.id, 0) + 1
        order_id_code = order.order_id_code
        route_id = order.product_route_id
        
        # Determine the earliest this job can start its *next* schedulable step
        job_arrival = ensure_utc_aware(order.arrival_time) or scheduling_anchor_time
        next_step_earliest_start = max(job_arrival, job_next_available_time.get(order_id_code, scheduling_anchor_time))
        start_offset_mins = max(0, int((next_step_earliest_start - scheduling_anchor_time).total_seconds() // 60))
        aware_due_date = ensure_utc_aware(order.due_date)
        deadline_offset = int((aware_due_date - scheduling_anchor_time).total_seconds() // 60) if aware_due_date else None

        if str(route_id) in process_steps_by_route:
            for step_num, step_data in sorted(process_steps_by_route[str(route_id)].items()):

                if step_num < start_scheduling_from_step: # only schedule steps that have not been completed
                    continue

                task_key = (order_id_code, step_num)

                if task_key in all_tasks_for_solver: # Skip if it was an in-progress task
                    print(f"[SKIP] Duplicate task_key found: {task_key}")
                    continue
                
                base_per_unit = int(step_data.base_duration_per_unit_mins or 0)
                quantity = int(order.quantity_to_produce or 1)
                op_duration = max(1, base_per_unit * quantity)

                earliest_start_mins = max(0, int((order.arrival_time - scheduling_anchor_time).total_seconds() // 60))
                deadline_offset_mins = None
                if order.due_date:
                    deadline_offset_mins = int((order.due_date - scheduling_anchor_time).total_seconds() // 60)

                all_tasks_for_solver[task_key] = TaskData(
                    production_order_id=order.id, 
                    job_id_code=order.order_id_code, 
                    step=step_num,
                    process_step_id=step_data.id, 
                    machine_type=step_data.required_machine_type,
                    process_step_name=step_data.step_name, 
                    is_fixed=False,
                    operation_duration=op_duration,
                    earliest_start_mins=earliest_start_mins,
                    deadline_offset_mins=deadline_offset_mins
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

    horizon_days = (horizon // 1440) + 2 # buffer for 2 days


    for machine_id in machine_instances.keys():
        for day in range(horizon_days):
            current_day = scheduling_anchor_time.date() + timedelta(days=day)

            # Check if entire day is a non-working day
            if current_day.weekday() in NON_WORKING_DAYS:
                start_of_day = datetime(current_day.year, current_day.month, current_day.day, tzinfo=timezone.utc)
                start_offset = max(0, int((start_of_day - scheduling_anchor_time).total_seconds() // 60))
                # create a 24 hour forbidden interval for the entire day
                interval = model.NewFixedSizeIntervalVar(start_offset, 1440, f"nonwork_{machine_id}_day_{day}")
                intervals_on_specific_machine[machine_id].append(interval)
                continue

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

    all_orders = {task.production_order_id: task for task in tasks.values()}
    deadline_penalties = []
    for order_id, task in all_orders.items():
        order = db_session.get(ProductionOrder, task.production_order_id)
        if order and order.due_date:
            last_step_key = jobs_map[order.order_id_code][-1]
            deadline_offset = int((order.due_date - scheduling_anchor_time).total_seconds() // 60)

            if deadline_offset > 0:
                if last_step_key not in task_intervals:
                    logging.error(f"Deadline constraint target {last_step_key} not found in task_intervals. Task may have been skipped.")
                else:
                    end_expr = task_intervals[last_step_key].EndExpr()
                    # Calculatig how late job is
                    late_by = model.NewIntVar(0, horizon, f"late_{order_id}")
                    model.Add(late_by >= end_expr - deadline_offset)

                    # penalty multiplier (10 points per minute late)
                    penalty_per_minute = 10
                    weighted_penalty = model.NewIntVar(0, horizon * penalty_per_minute, f"penalty_{order_id}")
                    model.AddMultiplicationEquality(weighted_penalty, [late_by, penalty_per_minute])

                    # save for objective function
                    deadline_penalties.append(weighted_penalty)
                    logging.info(f"Added deadline constraint for job {order.order_id_code} at minute {deadline_offset}.")


    # --- OBJECTIVE & SOLVER ---
    makespan = model.NewIntVar(0, horizon, 'makespan')
    if task_intervals:
        model.AddMaxEquality(makespan, [iv.EndExpr() for iv in task_intervals.values()])
    model.Minimize(1*makespan + 3*sum(deadline_penalties))

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

def save_scheduled_tasks_to_db(db: Session, scheduled_tasks_data: List[Dict]) -> List[ScheduledTask]:
    """Atomically updates the schedule in the database."""
    logging.info(f"Saving {len(scheduled_tasks_data)} tasks to the database...")

    db.query(ScheduledTask).filter(ScheduledTask.archived == False).update(
        {ScheduledTask.archived: True},
        synchronize_session= False
    )
    logger.info("Archived all previous ScheduledTasks.")

    scheduled_task_allowed_keys = {
        'production_order_id',
        'process_step_id',
        'assigned_machine_id',
        'start_time',
        'end_time',
        'scheduled_duration_mins',
        'status'
    }

    persisted_scheduled_tasks: List[ScheduledTask] = []

    try:
        # --- FIX 5: ROBUST DB SAVE LOGIC ---
        # Get all existing schedulable tasks for potential deletion
        existing_scheduled_tasks_map = {
            (t.production_order_id, t.process_step_id): t
            for t in db.query(ScheduledTask).filter(ScheduledTask.status == 'Scheduled').all()
        }
        
        newly_scheduled_po_ids = set()
        
        for task_data in scheduled_tasks_data:
            po_id = task_data['production_order_id']
            ps_id = task_data['process_step_id']
            machine_id = task_data['assigned_machine_id']

            newly_scheduled_po_ids.add(po_id)

            scheduled_task_key = (po_id, ps_id, machine_id)
            task_obj = existing_scheduled_tasks_map.pop(scheduled_task_key, None)

            if task_obj:
                # This is an existing task (likely was 'In-Progress'), update its details
                task_obj.start_time = task_data['start_time']
                task_obj.end_time = task_data['end_time']
                task_obj.scheduled_duration_mins = task_data['scheduled_duration_mins']
                task_obj.status = task_data.get('status', 'scheduled')
                db.add(task_obj)
                persisted_scheduled_tasks.append(task_obj)
                logger.debug(f"Updated existing ScheduledTask ID: {task_obj.id} for PO:{po_id}, PS:{ps_id}, M:{machine_id}.")
            else:
                # This is a new task to be scheduled
                filtered_data = {k: v for k, v in task_data.items() if k in scheduled_task_allowed_keys}
                filtered_data['status'] = filtered_data.get('status', 'scheduled').lower()
                new_task = ScheduledTask(archived=False, **filtered_data)
                db.add(new_task)
                persisted_scheduled_tasks.append(new_task)
                logger.debug(f"Created new ScheduledTask for PO:{po_id}, PS:{ps_id}, M:{machine_id}.")

            existing_job_log = db.query(JobLog).filter(
                JobLog.production_order_id == po_id,
                JobLog.process_step_id == ps_id,
                JobLog.machine_id == machine_id,
                JobLog.status.in_([JobLogStatus.PENDING, JobLogStatus.SCHEDULED])
            ).first()

            if existing_job_log:
                if existing_job_log.status != JobLogStatus.SCHEDULED:
                    existing_job_log.status = JobLogStatus.SCHEDULED
                if existing_job_log.actual_start_time != task_data['start_time']:
                    existing_job_log.actual_start_time = task_data['start_time']
                if existing_job_log.actual_end_time != task_data['end_time']:
                    existing_job_log.actual_end_time = task_data['end_time']
                
                db.add(existing_job_log)
                logger.debug(f"Updated existing JobLog ID: {existing_job_log.id} to SCHEDULED.")
            else:
                new_job_log = JobLog(
                    production_order_id=po_id,
                    process_step_id=ps_id,
                    machine_id=machine_id,
                    actual_start_time=task_data['start_time'], # Use scheduled start time
                    actual_end_time=task_data['end_time'],     # Use scheduled end time
                    status=JobLogStatus.SCHEDULED,             # Set status to SCHEDULED
                    remarks="Automatically created/updated by scheduler run."                    
                )
                db.add(new_job_log)
                logger.debug(f"Created new JobLog for PO:{po_id}, PS:{ps_id}, M:{machine_id}.")

        # Update parent ProductionOrder statuses
        if newly_scheduled_po_ids:
            db.query(ProductionOrder).filter(
                ProductionOrder.id.in_(newly_scheduled_po_ids)
            ).update({'current_status': OrderStatus.SCHEDULED}, synchronize_session=False)
            logger.info(f"Updated {len(newly_scheduled_po_ids)} Production Orders from PENDING to SCHEDULED.")

        db.commit()
        for task in persisted_scheduled_tasks:
            db.refresh(task)

        logging.info("All scheduled tasks, JobLogs, and ProductionOrders successfully committed to database.")
        return persisted_scheduled_tasks
    except Exception as e:
        db.rollback()
        logging.error(f"Database error during schedule save. Rolling back transaction. {e}", exc_info=True)
        raise


def main():
    """Main function to orchestrate the scheduling process."""
    logging.info("Optimal (OR-Tools) Scheduler script started.")
    db: Session = SessionLocal()
    current_real_time_anchor = datetime.now(timezone.utc)
    
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

