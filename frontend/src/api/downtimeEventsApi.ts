// src/api/downtimeEventsApi.ts

import apiClient from './axios';

export type DowntimeEventData = {
  id: number;
  machine_id: number;
  reason: string;
  start_time: string; // ISO string
  end_time: string;   // ISO string
  machine?: {
    machine_id_code: string;
    machine_type: string;
  };
};

// Utility: Convert IST to UTC ISO string
const convertIstToUtcIso = (datetimeStr: string): string => {
  // treat input as local IST manually
  const [datePart, timePart] = datetimeStr.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  
  const istDate = new Date(Date.UTC(year, month - 1, day, hour - 5, minute - 30));
  return istDate.toISOString(); // now correct UTC
};

// ✅ GET all downtime events
export const getDowntimeEvents = async (): Promise<DowntimeEventData[]> => {
  const response = await apiClient.get('/api/downtimes/');
  return response.data;
};

// ✅ CREATE downtime event
export const createDowntimeEvent = async (
  data: Omit<DowntimeEventData, 'id'>
): Promise<DowntimeEventData> => {
  const payload = {
    ...data,
    start_time: convertIstToUtcIso(data.start_time),
    end_time: convertIstToUtcIso(data.end_time),
  };
  const response = await apiClient.post('/api/downtimes/', payload);
  return response.data;
};

// ✅ UPDATE downtime event
export const updateDowntimeEvent = async (
  id: number,
  data: Omit<DowntimeEventData, 'id'>
): Promise<DowntimeEventData> => {
  const payload = {
    ...data,
    start_time: convertIstToUtcIso(data.start_time),
    end_time: convertIstToUtcIso(data.end_time),
  };
  const response = await apiClient.put(`/api/downtimes/${id}`, payload);
  return response.data;
};

// ✅ DELETE downtime event
export const deleteDowntimeEvent = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/downtimes/${id}`);
};

// ✅ IMPORT downtime events from file (handled by backend)
export const importDowntimeEvents = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/api/downtimes/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
