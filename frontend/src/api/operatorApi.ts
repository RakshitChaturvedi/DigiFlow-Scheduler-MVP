import apiClient from './axios';

// --- Type Definitions (Updated) ---
export interface WaitingInfo {
  step_name: string;
  status: string;
}

export interface OperatorJob {
  id: number;
  job_id_code: string;
  product_name: string | null;
  quantity_to_produce: number;
  priority: number;
  status: string;
}

export interface MachineQueue {
  machine_name: string;
  current_job: OperatorJob | null;
  next_task_in_sequence: OperatorJob | null; // Renamed for clarity
  is_next_task_ready: boolean;
  waiting_for: WaitingInfo | null;
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

// --- NEW FUNCTIONS ---
export const pauseTask = async (taskId: number): Promise<void> => {
  await apiClient.post(`/api/scheduled-tasks/${taskId}/pause`);
};

export const cancelTask = async (taskId: number): Promise<void> => {
  await apiClient.post(`/api/scheduled-tasks/${taskId}/cancel`);
};