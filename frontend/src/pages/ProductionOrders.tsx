import React from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getProductionOrders,
  deleteProductionOrder,
  type ProductionOrderData,
} from '../api/productionOrdersApi';
import { createSchedule } from '../api/createSchedule';
import AddProductionOrderModal from '../components/AddProductionOrderModal';
import ImportOrdersModal from '../components/ImportProductionOrderModal';
import { queryClient } from '../lib/react-query';

const ProductionOrders: React.FC = () => {
  const [searchTerm, setSearchTerm] = React.useState<string>('');
  const navigate = useNavigate();

  const [filters, setFilters] = React.useState({
    sort_by: '',
    sort_order: '',
    filter_by_status: '',
    filter_by_priority: '',
    filter_by_product: '',
    filter_by_progress_min: '',
    filter_by_progress_max: '',
  });

  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedOrder, setSelectedOrder] = React.useState<ProductionOrderData | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);

  const { data: productionOrders = [], isLoading, isError, error } = useQuery<ProductionOrderData[], Error>({
    queryKey: ['productionOrders', filters],
    queryFn: () => getProductionOrders(filters),
    staleTime: 5 * 60 * 1000,
  });

  const visibleOrders = productionOrders.filter(
    order => order.current_status !== 'scheduled' && order.current_status !== 'completed' && order.current_status !== 'cancelled'
  )

  const deleteMutation = useMutation({
    mutationFn: deleteProductionOrder,
    onSuccess: () => {
      toast.success('Order deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['visibleOrders'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to delete order');
    }
  });

  const handleAddOrder = () => {
    setIsEditing(false);
    setSelectedOrder(null);
    setIsAddModalOpen(true);
  };

  const handleEditOrder = (id: number) => {
    const orderToEdit = visibleOrders.find(order => order.id === id);
    if (orderToEdit) {
      setIsEditing(true);
      setSelectedOrder(orderToEdit);
      setIsAddModalOpen(true);
    }
  };

  const handleDeleteOrder = (id: number) => {
    if (window.confirm(`Are you sure you want to delete Order ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  const handleImportOrders = () => setIsImportModalOpen(true);

  const handleSchedule = async () => {
    const nonZeroOrders = visibleOrders.filter(o => o.quantity_to_produce > 0);
    if (nonZeroOrders.length === 0) {
      toast.warning("No valid production orders to schedule.");
      return;
    }
    const confirmed = window.confirm(`Create schedule for ${nonZeroOrders.length} production orders?`);
    if (!confirmed) return;
    try {
      await createSchedule(); // API call to trigger scheduling
      toast.success("Schedule created successfully.");
      navigate("/digiflow/schedule");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create schedule.");
      console.error("Scheduler error:", error)
    }
  };

  const getStatusDisplay = (status: ProductionOrderData['current_status']) => {
    switch (status) {
      case 'completed': return { text: 'Completed', color: 'text-green-600 bg-green-100' };
      case 'in_progress': return { text: 'In Progress', color: 'text-orange-600 bg-orange-100' };
      case 'pending': return { text: 'Pending', color: 'text-blue-600 bg-blue-100' };
      case 'cancelled': return { text: 'Cancelled', color: 'text-red-600 bg-red-100' };
      case 'scheduled': return { text: 'Scheduled', color: 'text-purple-600 bg-purple-100' };
      default: return { text: 'Unknown', color: 'text-gray-600 bg-gray-100' };
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark mb-4 md:mb-0">Production Orders</h2>
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4">
          <button
            onClick={handleSchedule}
            className="bg-green-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors"
          >
            Create Schedule
          </button>
          <button
            onClick={handleAddOrder}
            className="bg-primaryBlue text-white px-5 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Add Production Order
          </button>
          <button
            onClick={handleImportOrders}
            className="bg-gray-700 text-white px-5 py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Import Orders
          </button>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-borderColor">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Route ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Arrival</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-borderColor">
              {isLoading && (
                <tr><td colSpan={10} className="text-center py-4">Loading...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={10} className="text-center py-4 text-red-600">{error.message}</td></tr>
              )}
              {!isLoading && !isError && visibleOrders.length === 0 && (
                <tr><td colSpan={10} className="text-center py-4 text-gray-500">No production orders found.</td></tr>
              )}
              {!isLoading && !isError && visibleOrders.map(order => {
                const status = getStatusDisplay(order.current_status);
                return (
                  <tr key={order.id}>
                    <td className="px-6 py-4 text-sm">{order.order_id_code}</td>
                    <td className="px-6 py-4 text-sm">{order.product_name || '-'}</td>
                    <td className="px-6 py-4 text-sm">{order.product_route_id}</td>
                    <td className="px-6 py-4 text-sm">{order.quantity_to_produce}</td>
                    <td className="px-6 py-4 text-sm">{order.priority}</td>
                    <td className="px-6 py-4 text-sm">{new Date(order.arrival_time).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-sm">{order.due_date ? new Date(order.due_date).toLocaleDateString() : '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full font-semibold ${status.color}`}>
                        {status.text}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="w-24 bg-gray-200 rounded-full h-2.5">
                        <div
                          className="h-2.5 rounded-full"
                          style={{
                            width: `${order.progress ?? 0}%`,
                            backgroundColor:
                              (order.progress ?? 0) === 100
                                ? 'green'
                                : (order.progress ?? 0) > 0
                                  ? 'blue'
                                  : 'gray',
                          }}
                        ></div>
                      </div>
                      <span className="ml-2 text-xs">{order.progress ?? 0}%</span>
                    </td>
                    <td className="px-6 py-4 text-right space-x-4">
                      <button onClick={() => handleEditOrder(order.id)} className="text-yellow-600 hover:underline mr-3">Edit</button>
                      <button onClick={() => handleDeleteOrder(order.id)} className="text-red-600 hover:underline">Delete</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {isAddModalOpen && (
        <AddProductionOrderModal
          onClose={() => {
            setIsAddModalOpen(false);
            setIsEditing(false);
            setSelectedOrder(null);
            queryClient.invalidateQueries({ queryKey: ['visibleOrders'] });
          }}
          isEditing={isEditing}
          initialData={selectedOrder ?? undefined}
        />
      )}

      {isImportModalOpen && (
        <ImportOrdersModal onClose={() => setIsImportModalOpen(false)} />
      )}
    </div>
  );
};

export default ProductionOrders;