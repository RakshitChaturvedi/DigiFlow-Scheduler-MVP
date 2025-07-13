import apiClient from "./axios"; // Assuming axios is configured for your backend base URL

// Define the interfaces for the nested objects first
export type ProductionOrderInfo = {
    order_id_code: string;
    product_name?: string | null; // product_name is nullable
};

export type ProcessStepInfo = {
    step_number: number;
    step_name: string;
};

export type AssignedMachineInfo = {
    machine_id_code: string;
};

// Define the main ScheduledTaskData interface to match the backend's ScheduledTaskResponse
export type ScheduledTaskData = {
    id: number;
    start_time: string; // ISO format datetime string
    end_time: string;   // ISO format datetime string
    scheduled_duration_mins: number;
    status: string; // e.g., "scheduled", "in_progress", "completed", "delayed"
    job_id_code?: string | null; // Optional, as per your backend schema
    // step_number?: number | null; // Removed this from here as it's part of process_step_definition

    // Nested objects from backend joins
    production_order: ProductionOrderInfo;
    process_step_definition: ProcessStepInfo;
    assigned_machine: AssignedMachineInfo;

    // Optional: if your backend still sends these for legacy reasons, keep them
    // production_order_id?: number;
    // process_step_id?: number;
    // assigned_machine_id?: number;
    // archived?: boolean; // If archived is still sent in the response
};

// --- Get all scheduled tasks ---
export const getScheduledTasks = async(): Promise<ScheduledTaskData[]> => {
    // Ensure this URL matches your backend route for fetching scheduled tasks
    // Based on your routes.py, it's /schedule, not /api/schedule/
    const response = await apiClient.get('/api/schedule/'); // Changed from /api/schedule/ to /schedule
    // Assuming apiClient is configured to prepend the base URL (e.g., http://127.0.0.1:8000)
    return response.data;
};

export const updateScheduledTask = async(
    id: number,
    updateData: Partial<ScheduledTaskData>
): Promise<ScheduledTaskData> => {
    const response = await apiClient.put(`/api/schedule/${id}`, updateData);
    return response.data;
};

export const deleteScheduledTask = async (id: number): Promise<void> => {
    await apiClient.delete(`/api/schedule/${id}`);
};

