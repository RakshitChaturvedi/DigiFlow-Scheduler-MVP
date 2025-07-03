// src/api/processStepsAPI.ts
import apiClient from "./axios";

export type ProcessStepData = {
  id: number;
  product_route_id: string;
  step_number: number;
  step_name: string;
  required_machine_type: string;
  base_duration_per_unit_mins: number;
};

// ✅ GET all process steps
export const getProcessSteps = async (): Promise<ProcessStepData[]> => {
  const response = await apiClient.get('/api/steps/');
  return response.data;
};

// ✅ CREATE a process step
export const createProcessStep = async (data: Omit<ProcessStepData, 'id'>): Promise<ProcessStepData> => {
  const response = await apiClient.post('/api/steps/', data);
  return response.data;
};

// ✅ UPDATE a process step
export const updateProcessStep = async (id: number, data: Omit<ProcessStepData, 'id'>): Promise<ProcessStepData> => {
  const response = await apiClient.put(`/api/steps/${id}`, data);
  return response.data;
};

// ✅ DELETE a process step
export const deleteProcessStep = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/steps/${id}`);
};

// ✅ IMPORT process steps from file
export const importProcessSteps = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/steps/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};
