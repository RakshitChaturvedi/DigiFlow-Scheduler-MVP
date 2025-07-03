import React from 'react';
import { useQuery, useQueryClient, useMutation, keepPreviousData } from '@tanstack/react-query';
import { getProductionOrders, deleteProductionOrder } from '../api/productionOrdersApi';
import type { ProductionOrderData } from '../api/productionOrdersApi';
import AddProductionOrderModal from '../components/AddProductionOrderModal';
import { queryClient } from '../lib/react-query';
import ImportOrdersModal from '../components/ImportProductionOrderModal';

const ProductionOrders: React.FC = () => {
  const [searchTerm, setSearchTerm] = React.useState<string>('');

  const [filters, setFilters] = React.useState({
    sort_by: '', // e.g. 'arrival_time', 'priority', etc.
    sort_order: '', // 'asc' or 'desc'
    filter_by_status: '',
    filter_by_priority: '',
    filter_by_product: '',
    filter_by_progress_min: '',
    filter_by_progress_max: '',
  });

  const { data: productionOrders, isLoading, isError, error } = useQuery<ProductionOrderData[], Error>({
    queryKey: ['productionOrders', filters],
    queryFn: () => getProductionOrders(filters),
    staleTime: 5 * 60 * 1000,
  });


  const filteredOrders = productionOrders || [];

  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedOrder, setSelectedOrder] = React.useState<ProductionOrderData | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);

  const handleAddOrder = () => {
    setIsEditing(false);
    setSelectedOrder(null);
    setIsAddModalOpen(true);
  };
  const handleImportOrders = () => setIsImportModalOpen(true);
  const handleEditOrder = (id: number) => {
    const orderToEdit = productionOrders?.find(order => order.id === id);
    if (orderToEdit) {
      setIsEditing(true);
      setSelectedOrder(orderToEdit);
      setIsAddModalOpen(true);
    }
  };

  const deleteMutation = useMutation({
    mutationFn: deleteProductionOrder,
    onSuccess: () => {
      alert("Order deleted successfully.");
      queryClient.invalidateQueries({ queryKey: ['productionOrders'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete order');
    }
  });

  const handleDeleteOrder = (id: number) => {
    if (window.confirm(`Are you sure you want to delete Order ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  const getStatusDisplay = (status: ProductionOrderData['current_status']) => {
    switch (status) {
      case 'completed': return { text: 'Completed', color: 'text-green-600 bg-green-100' };
      case 'in_progress': return { text: 'In Progress', color: 'text-orange-600 bg-orange-100' };
      case 'pending': return { text: 'Pending', color: 'text-blue-600 bg-blue-100' };
      case 'cancelled': return { text: 'Cancelled', color: 'text-red-600 bg-red-100' };
      default: return { text: 'Unknown', color: 'text-gray-600 bg-gray-100' };
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark mb-4 md:mb-0">Production Orders</h2>
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4">
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

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="mb-4 flex flex-col md:flex-row md:justify-between md:items-center space-y-3 md:space-y-0">

          <input
            type="text"
            placeholder="Search orders..."
            className="border border-borderColor rounded-lg px-4 py-2 w-full md:w-1/3 focus:ring-primaryBlue focus:border-transparent"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="flex flex-wrap gap-3 mt-3">
            <input
              type="text"
              placeholder="Filter by product..."
              className="border rounded px-2 py-1"
              value={filters.filter_by_product}
              onChange={(e) => setFilters(prev => ({ ...prev, filter_by_product: e.target.value }))}
            />

            <select
              className="border rounded px-2 py-1"
              value={filters.filter_by_status}
              onChange={(e) => setFilters(prev => ({ ...prev, filter_by_status: e.target.value }))}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <input
              type="number"
              placeholder="Min Progress %"
              className="border rounded px-2 py-1 w-28"
              value={filters.filter_by_progress_min}
              onChange={(e) => setFilters(prev => ({ ...prev, filter_by_progress_min: e.target.value }))}
            />

            <input
              type="number"
              placeholder="Max Progress %"
              className="border rounded px-2 py-1 w-28"
              value={filters.filter_by_progress_max}
              onChange={(e) => setFilters(prev => ({ ...prev, filter_by_progress_max: e.target.value }))}
            />
          </div>

          <div className="flex space-x-3">

            <select
              className="border rounded-lg px-3 py-2 text-sm"
              value={filters.sort_by}
              onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value }))}
            >
              <option value="">Sort By</option>
              <option value="arrival_time">Arrival Time</option>
              <option value="due_date">Due Date</option>
              <option value="priority">Priority</option>
              <option value="progress">Progress</option>
            </select>

            <select
              className="border rounded-lg px-3 py-2 text-sm"
              value={filters.sort_order}
              onChange={(e) => setFilters(prev => ({ ...prev, sort_order: e.target.value }))}
            >
              <option value="">Order</option>
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>

          </div>
        </div>

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
              {!isLoading && !isError && filteredOrders.length === 0 && (
                <tr><td colSpan={10} className="text-center py-4 text-gray-500">No production orders found.</td></tr>
              )}
              {!isLoading && !isError && filteredOrders.map(order => {
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
                      <span className={`px-2 py-1 text-xs rounded-full font-semibold ${status.color}`}>{status.text}</span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="w-24 bg-gray-200 rounded-full h-2.5">
                        <div className="h-2.5 rounded-full"
                          style={{
                            width: `${order.progress ?? 0}%`,
                            backgroundColor: (order.progress ?? 0) === 100 ? 'green' : ((order.progress ?? 0) > 0 ? 'blue' : 'gray')
                          }}>
                        </div>
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
        <AddProductionOrderModal onClose={() => {
          setIsAddModalOpen(false);
          setIsEditing(false);
          setSelectedOrder(null);
          queryClient.invalidateQueries({queryKey: ['productionOrders'] });
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
