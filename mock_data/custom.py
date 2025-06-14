import pandas as pd
from datetime import datetime, timedelta
from ortools.sat.python import cp_model
import collections

# --- 1. CONFIGURATION & SETUP ---
SIMULATION_START_TIME = datetime(2025, 6, 9, 8, 0, 0) # A Monday morning

# --- 2. DATA LOADING ---
try:
    machines_df = pd.read_csv('machine_catalog_mock_data.csv')
    routes_df = pd.read_csv('mold_routing_mock_data.csv')
    jobs_df = pd.read_csv('job_schedule_mock_data.csv')
except FileNotFoundError as e:
    print(f"Error: {e}. Please make sure all CSV files are in the same folder as the script.")
    exit()

# --- 3. DATA PREPARATION ---
# This section is identical to the greedy_scheduler.py to ensure an apples-to-apples comparison

# Convert routing data into a more usable dictionary format
routing_dict = {}
for mold_id, group in routes_df.groupby('mold_id'):
    routing_dict[mold_id] = group.sort_values('step').to_dict('records')

# Prepare the final list of jobs with all necessary information
all_tasks = {}
job_to_tasks = collections.defaultdict(list)
task_counter = 0

for _, job in jobs_df.iterrows():
    mold_id = job['mold_id']
    quantity = job['quantity']
    arrival_time_offset = timedelta(hours=job['arrival_time_hour'])
    
    if mold_id in routing_dict:
        for step_data in routing_dict[mold_id]:
            machine_type = step_data['machine_type']
            machine_row = machines_df[machines_df['machine_type'] == machine_type]

            if machine_row.empty:
                raise ValueError(f"No setup time found for machine type: {machine_type}")

            setup_time = int(machine_row.iloc[0]['setup_time_mins'])
            operation_time = int(step_data['duration_mins'] * quantity)
            total_duration_mins = setup_time + operation_time
            
            task_key = (job['job_id'], step_data['step'])
            all_tasks[task_key] = {
                'job_id': job['job_id'],
                'step': step_data['step'],
                'machine_type': step_data['machine_type'],
                'duration': int(total_duration_mins), # OR-Tools prefers integers
                'arrival_time_offset': int(arrival_time_offset.total_seconds() // 60) # in minutes
            }
            job_to_tasks[job['job_id']].append(task_key)

# --- 4. THE OR-TOOLS SCHEDULING ALGORITHM ---

def schedule_with_ortools(tasks, jobs_map, machines):
    model = cp_model.CpModel()

    # Calculate a reasonable upper bound for the schedule horizon
    horizon = sum(task['duration'] for task in tasks.values()) + sum(task['arrival_time_offset'] for task in tasks.values())

    # Create a dictionary to hold all the interval variables for the solver
    task_intervals = {}
    
    # Create variables for each task
    for task_key, task_data in tasks.items():
        start_var = model.NewIntVar(task_data['arrival_time_offset'], horizon, f'start_{task_key}')
        duration = task_data['duration']
        end_var = model.NewIntVar(task_data['arrival_time_offset'], horizon, f'end_{task_key}')
        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{task_key}')
        task_intervals[task_key] = interval_var

    # --- ADD CONSTRAINTS ---

    # 1. Precedence Constraint: Steps within the same job must run in order
    for job_id, steps in jobs_map.items():
        steps.sort(key=lambda x: x[1]) # Sort by step number
        for i in range(len(steps) - 1):
            current_step_key = steps[i]
            next_step_key = steps[i+1]
            model.Add(task_intervals[next_step_key].StartExpr() >= task_intervals[current_step_key].EndExpr())

    # 2. No-Overlap Constraint: A machine cannot do two tasks at once
    tasks_on_machine = collections.defaultdict(list)
    for task_key, task_data in tasks.items():
        possible_machines = machines[machines['machine_type'] == task_data['machine_type']]['machine_id'].tolist()
        
        # This logic is simpler if we assume all machines of a type are interchangeable for the solver
        # A more complex model could assign tasks to specific machines.
        # For now, we group by machine_type.
        tasks_on_machine[task_data['machine_type']].append(task_intervals[task_key])

    for machine_type in tasks_on_machine:
        # The number of machines of this type acts as the capacity
        capacity = len(machines[machines['machine_type'] == machine_type])
        if capacity > 1:
             model.AddCumulative(tasks_on_machine[machine_type], [1] * len(tasks_on_machine[machine_type]), capacity)
        else:
             model.AddNoOverlap(tasks_on_machine[machine_type])
        
    # --- DEFINE OBJECTIVE ---
    # The goal is to minimize the makespan (the end time of the last task)
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, [interval.EndExpr() for interval in task_intervals.values()])
    model.Minimize(makespan)

    # --- SOLVE THE MODEL ---
    solver = cp_model.CpSolver()
    # Optional: Set a time limit for the solver
    solver.parameters.max_time_in_seconds = 60.0
    status = solver.Solve(model)

    # --- EXTRACT RESULTS ---
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = []
        for task_key, task_data in tasks.items():
            start_mins = solver.Value(task_intervals[task_key].StartExpr())
            end_mins = solver.Value(task_intervals[task_key].EndExpr())
            schedule.append({
                'Job ID': task_data['job_id'],
                'Step': task_data['step'],
                'Machine Type': task_data['machine_type'],
                # In this simplified model, we don't know the exact machine_id, just the type
                'Machine ID': f"Type: {task_data['machine_type']}", 
                'Start Time': SIMULATION_START_TIME + timedelta(minutes=start_mins),
                'End Time': SIMULATION_START_TIME + timedelta(minutes=end_mins)
            })
        return schedule, solver.Value(makespan)
    else:
        return None, None



# --- 5. EXECUTION AND OUTPUT ---
print("Running the Optimal (OR-Tools) Scheduler...")
optimal_schedule, makespan_mins = schedule_with_ortools(all_tasks, job_to_tasks, machines_df)

if optimal_schedule:
    print("Optimal schedule found.")
    schedule_df = pd.DataFrame(optimal_schedule)
    total_duration_hours = makespan_mins / 60

    print("\n--- Optimal Schedule Results ---")
    print(f"All jobs completed in: {total_duration_hours:.2f} hours")

    output_filename = 'schedule_after.csv'
    schedule_df.to_csv(output_filename, index=False)
    print(f"\nDetailed schedule saved to '{output_filename}'")
else:
    print("Could not find an optimal solution.")

print(schedule_df)