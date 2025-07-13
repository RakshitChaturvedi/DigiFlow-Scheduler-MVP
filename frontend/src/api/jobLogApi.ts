import apiClient from './axios';

export type JobLogStatus = 'completed' | 'cancelled' | 'aborted';

export interface JobLogData {
  id: number;
  production_order_id: number;
  process_step_id: number;
  machine_id: number;
  actual_start_time: string;
  actual_end_time: string | null;
  status: JobLogStatus;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

// ✅ Get all job logs
export const getJobLogs = async (): Promise<JobLogData[]> => {
  const res = await apiClient.get('/api/job_logs/');
  return res.data;
};

// ✅ Create job log
export const createJobLog = async (
  data: Omit<JobLogData, 'id' | 'created_at' | 'updated_at'>
): Promise<JobLogData> => {
  const res = await apiClient.post('/api/job_logs/', data);
  return res.data;
};

// ✅ Update job log
export const updateJobLog = async (
  id: number,
  data: Partial<Omit<JobLogData, 'id' | 'created_at' | 'updated_at'>>
): Promise<JobLogData> => {
  const res = await apiClient.put(`/api/job_logs/${id}`, data);
  return res.data;
};

// ✅ Delete job log
export const deleteJobLog = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/job_logs/${id}`);
};