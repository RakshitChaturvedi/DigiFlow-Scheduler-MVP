// src/api/productionOrdersApi.js
import apiClient from './axios';

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

export const getProductionOrders = async (): Promise<ProductionOrderData[]> => {
  const response = await apiClient.get('/api/orders');
  const data: ProductionOrderData[] = response.data;

  return data.map(order => ({
    ...order,
    progress: order.progress ?? Math.floor(Math.random() * 101),
  }));
};

