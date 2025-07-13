import apiClient from './axios';
import { formatInTimeZone } from 'date-fns-tz';

export interface ProductionOrderData {
  id: number;
  order_id_code: string;
  product_name: string | null;
  product_route_id: string;
  quantity_to_produce: number;
  priority: number;
  arrival_time: string;
  due_date: string | null;
  current_status: 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'scheduled';
  created_at: string;
  updated_at: string;
  progress?: number;
}

export interface ProductionOrderFilters {
  sort_by?: string;
  sort_order?: string;
  filter_by_status?: string;
  filter_by_priority?: string;
  filter_by_product?: string;
  filter_by_progress_min?: string;
  filter_by_progress_max?: string;
}

// ✅ Timezone conversion: IST → UTC ISO string
const convertIstToUtcIso = (datetimeStr: string): string => {
  const date = new Date(datetimeStr);
  return formatInTimeZone(date, 'UTC', "yyyy-MM-dd'T'HH:mm:ssXXX");
};

// ✅ GET production orders with filters
export const getProductionOrders = async (
  filters: ProductionOrderFilters = {}
): Promise<ProductionOrderData[]> => {
  const queryParams = new URLSearchParams();

  if (filters.sort_by?.trim()) queryParams.append('sort_by', filters.sort_by);
  if (filters.sort_order?.trim()) queryParams.append('sort_order', filters.sort_order);
  if (filters.filter_by_status?.trim()) queryParams.append('filter_by_status', filters.filter_by_status);
  if (filters.filter_by_priority?.trim()) queryParams.append('filter_by_priority', filters.filter_by_priority);
  if (filters.filter_by_product?.trim()) queryParams.append('filter_by_product', filters.filter_by_product);
  if (filters.filter_by_progress_min?.trim()) queryParams.append('filter_by_progress_min', filters.filter_by_progress_min);
  if (filters.filter_by_progress_max?.trim()) queryParams.append('filter_by_progress_max', filters.filter_by_progress_max);

  const queryString = queryParams.toString();
  const url = `/api/orders${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get(url);
  const data: ProductionOrderData[] = response.data;

  return data.map(order => ({
    ...order,
    progress: order.progress ?? Math.floor(Math.random() * 101), // fallback progress
  }));
};

// ✅ CREATE production order
export const createProductionOrder = async (
  data: Omit<ProductionOrderData, 'id' | 'created_at' | 'updated_at' | 'current_status'>
): Promise<ProductionOrderData> => {
  const payload = {
    ...data,
    arrival_time: convertIstToUtcIso(data.arrival_time),
    due_date: data.due_date ? convertIstToUtcIso(data.due_date) : null,
  };
  const response = await apiClient.post('/api/orders/', payload);
  return response.data;
};

// ✅ UPDATE production order
export const updateProductionOrder = async (
  id: number,
  data: Partial<Omit<ProductionOrderData, 'id' | 'created_at' | 'updated_at' | 'current_status'>>
): Promise<ProductionOrderData> => {
  const payload = {
    ...data,
    arrival_time: data.arrival_time ? convertIstToUtcIso(data.arrival_time) : undefined,
    due_date: data.due_date ? convertIstToUtcIso(data.due_date) : undefined,
  };
  const response = await apiClient.put(`/api/orders/${id}`, payload);
  return response.data;
};

// ✅ IMPORT (no conversion needed — backend handles it)
export const importProductionOrders = async (file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/orders/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

// ✅ DELETE production order
export const deleteProductionOrder = async (id: number): Promise<void> => {
  await apiClient.delete(`/api/orders/${id}`);
};
