// src/api/productionOrdersApi.js
import apiClient from './axios';
import qs from 'qs'

// src/api/productionOrdersApi.ts
export interface ProductionOrderData {
  id: number;
  order_id_code: string;
  product_name: string | null;
  product_route_id: string;
  quantity_to_produce: number;
  priority: number;
  arrival_time: string;
  due_date: string | null;
  current_status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
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
    progress: order.progress ?? Math.floor(Math.random() * 101),
  }));
};



export const deleteProductionOrder = async (id:number): Promise<void> => {
  await apiClient.delete(`/api/orders/${id}`);
};

