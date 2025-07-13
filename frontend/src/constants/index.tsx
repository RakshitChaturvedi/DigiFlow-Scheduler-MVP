export type JobLogStatus = 'pending' | 'scheduled' | 'in_progress' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface JobLog {
  id: number;
  production_order: { order_id_code: string };
  process_step: { step_name: string };
  machine: { machine_id_code: string };
  actual_start_time: string;
  actual_end_time?: string;
  status: JobLogStatus;
  remarks?: string;
}