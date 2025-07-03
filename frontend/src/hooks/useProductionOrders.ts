import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export interface ProductionOrder {
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
  progress: number;
}

export const useProductionOrders = () => {
  return useQuery<ProductionOrder[]>({
    queryKey: ["production-orders"],
    queryFn: async () => {
      const res = await axios.get("http://localhost:8000/api/production-orders");
      return res.data;
    }
  });
};
