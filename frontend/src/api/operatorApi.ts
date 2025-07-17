import apiClient from "./axios";

// --- Type Definitions ---

export interface OperatorJob {
    id: number;
    job_id_code: string;
    product_name: string;
    quantity_to_produce: number;
    priority: number;
    status: string;
}

export interface MachineQueue {
    machine_name: string;
    current_job: OperatorJob | null;
    next_job: OperatorJob | null;
}

export interface ReportIssuePayload {
    reason: string;
    comments?: string;
}

// --- API Functions ---
export const getMachineQueue = async (machineIdCode: string): Promise<MachineQueue> => {
  const response = await apiClient.get(`/api/operators/${machineIdCode}/queue`);
  return response.data;
};

export const startTask = async (taskId: number): Promise<void> => {
  await apiClient.post(`/api/scheduled-tasks/${taskId}/start`);
};

export const finishTask = async (taskId: number): Promise<void> => {
  await apiClient.post(`/api/scheduled-tasks/${taskId}/finish`);
};

export const reportIssue = async (taskId: number, payload: ReportIssuePayload): Promise<void> => {
  await apiClient.post(`/api/scheduled-tasks/${taskId}/report-issue`, payload);
};