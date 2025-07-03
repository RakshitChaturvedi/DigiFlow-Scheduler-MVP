// src/api/machinesApi.ts

import apiClient from "./axios";

export type MachineData = {
  id: number;
  machine_id_code: string;
  machine_type: string;
  default_setup_time_mins: number;
  is_active: boolean;
};

// ✅ GET all machines
export const getMachines = async (): Promise<MachineData[]> => {
  const response = await apiClient.get('/api/machines/');
  return response.data;
};

// ✅ CREATE a machine
export const createMachine = async (data: Omit<MachineData, 'id'>): Promise<MachineData> => {
  const response = await apiClient.post('/api/machines/', data);
  return response.data;
};

// ✅ UPDATE a machine
export const updateMachine = async (id: number, data: Omit<MachineData, 'id'>): Promise<MachineData> => {
  const response = await apiClient.put(`/api/machines/${id}`, data);
  return response.data;
};

// ✅ DELETE a machine
export const deleteMachine = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/machines/${id}`);
};

// ✅ IMPORT machines from file
export const importMachines = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/machines/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};
