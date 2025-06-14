import pandas as pd
from datetime import datetime, timedelta

# 1. CONFIGURATION AND SETUP
SIMULATION_START_TIME = datetime(2025,6,9,8,0,0)


# 2. DATA LOADING
try:
    machines_df = pd.read_csv('machine_catalog_mock_data.csv')
    routes_df = pd.read_csv('mold_routing_mock_data.csv')
    jobs_df = pd.read_csv('job_schedule_mock_data.csv')
except FileNotFoundError as e:
    print(f"Error  : {e}. Please make sure all CSV files are in the same folder as the script. ")
    exit()


# 3. DATA PREPARATION
# Convert the routing data into a more usable dictionary format for quick lookups
routing_dict = {}
for mold_id, group in routes_df.groupby('mold_id'):
    routing_dict[mold_id] = group.sort_values('step').to_dict('records')

# Prepare the final list of jobs with all necessary information
jobs_to_process = []

for _, job in jobs_df.iterrows():
    mold_id = job['mold_id']
    quantity = job['quantity']

    if mold_id in routing_dict:
        job_steps = []
        for step_data in routing_dict[mold_id]:
            machine_type = step_data['machine_type']
            setup_row = machines_df[machines_df['machine_type'] == machine_type]
            if setup_row.empty:
                raise ValueError(f"No setup time found for machine type: {machine_type}")
            setup_time = int(setup_row.iloc[0]['setup_time_mins'])

            # Total time = setup time + run time * quantity
            total_duration_mins = setup_time + (step_data['duration_mins'] * quantity)

            job_steps.append({
                'step': step_data['step'],
                'machine_type': step_data['machine_type'],
                'duration': timedelta(minutes=total_duration_mins)
            })
        
        jobs_to_process.append({
            'job_id': job['job_id'],
            'steps': job_steps,
            'arrival_time': SIMULATION_START_TIME + timedelta(hours=job['arrival_time_hour'])
        })

# Sort jobs by their arrival time (FIFO logic)
jobs_to_process.sort(key=lambda x: x['arrival_time'])

# 4. HELPER FOR MAINTENANCE CHECK
def is_in_maintenance(machine_id, start_time, end_time):
    # Checks if a given time slot conflicts with a machine's maintenance day.
    machine_info = machines_df[machines_df['machine_id'] == machine_id].iloc[0]
    maintenance_day_str = machine_info['maintenance_days']

    if maintenance_day_str == 'None':
        return False
    
    day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    maintenance_weekday = day_map.get(maintenance_day_str)

    #Check every hour within the task's duration
    current_time = start_time
    while current_time < end_time:
        if current_time.weekday() == maintenance_weekday:
            return True
        current_time += timedelta(hours=1)

    return False

# 5. GREEDY SCHEDULING ALGORITHM
def run_greedy_scheduler(jobs, machines):

    # Track the time when each individual machine becomes free
    machine_free_at = {machine_id: SIMULATION_START_TIME for machine_id in machines['machine_id']}

    final_schedule = []

    for job in jobs:
        job_arrival_time = job['arrival_time']
        previous_step_end_time = job_arrival_time

        for step in job['steps']:
            step_duration = step['duration']
            required_machine_type = step['machine_type']

            # Find all physical machines that match the required type
            possible_machines = machines[machines['machine_type'] == required_machine_type]['machine_id'].tolist()

            # Find best machine that can start at earliest
            best_machine=None
            earliest_finish_time = datetime.max
            potential_start_time = None

            for machine_id in possible_machines:

                # A Step can only start after machine is free AND previous step of same job is done
                potential_start_time_for_this_machine = max(machine_free_at[machine_id], previous_step_end_time)

                # Keep checking for a valid slot if current is in maintenance
                while True:
                    potential_end_time = potential_start_time_for_this_machine + step_duration
                    if not is_in_maintenance(machine_id, potential_start_time_for_this_machine, potential_end_time):
                        # Found a valid slot, break the loop
                        break
                    # If it's a maintenance slot, push the start time forward by 1 hour and recheck
                    potential_start_time_for_this_machine += timedelta(hours=1)

                if potential_end_time < earliest_finish_time:
                    earliest_finish_time = potential_end_time
                    best_machine = machine_id
                    potential_start_time = potential_start_time_for_this_machine
            
            # Assign the task to the best machine found
            final_start_time = potential_start_time
            final_end_time = earliest_finish_time

            final_schedule.append({
                'Job ID': job['job_id'],
                'Step': step['step'],
                'Machine ID': best_machine,
                'Machine Type': required_machine_type,
                'Start Time': final_start_time,
                'End Time': final_end_time
            })

            #Update the availability for the chosen machine and the job's timeline
            machine_free_at[best_machine] = final_end_time
            previous_step_end_time = final_end_time

    return final_schedule

# 6. EXECUTION AND OUTPUT

print("Running the Greedy (FIFO) Scheduler... ")
greedy_schedule = run_greedy_scheduler(jobs_to_process, machines_df)
print("Scheduling Complete.")

#Conver the scheduler to a DF for analysis and saving
schedule_df = pd.DataFrame(greedy_schedule)

# Calculate and print key metrics
print(schedule_df)
makespan_end_time = schedule_df['End Time'].max()
total_duration_hours = (makespan_end_time - SIMULATION_START_TIME).total_seconds()/3600

print("\n--- Greedy Schedule Results ---")
print(f"All jobs completed at: {makespan_end_time.strftime('%Y-%m-%d %H:%M')}")
print(f"Total Makespan (duration): {total_duration_hours:.2f} hours")

#Save the schedule to a csv file
output_filename = 'schedule_before.csv'
schedule_df.to_csv(output_filename, index=False)
print(f"\n Detailed Schedule saved to '{output_filename}'")

        