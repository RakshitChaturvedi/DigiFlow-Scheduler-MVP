import React, { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast'; // Assuming you've installed react-hot-toast
import { deleteJobLog, getJobLogs, type JobLogData } from '../../api/jobLogApi';
import { getProductionOrders, type ProductionOrderData } from '../../api/productionOrdersApi';
import { getMachines, type MachineData } from '../../api/machinesAPI';
import { getProcessSteps, type ProcessStepData } from '../../api/processStepsApi';

const JobLogs: React.FC = () => {
  const queryClient = useQueryClient();

  // --- Fetch all necessary data in parallel ---
  const { data: jobLogs = [], isLoading: isLoadingLogs } = useQuery<JobLogData[], Error>({
    queryKey: ['jobLogs'],
    queryFn: getJobLogs,
  });

  const { data: orders = [], isLoading: isLoadingOrders } = useQuery<ProductionOrderData[], Error>({
    queryKey: ['productionOrders'],
    queryFn: () => getProductionOrders(), // Fetch all orders for lookup
  });

  const { data: machines = [], isLoading: isLoadingMachines } = useQuery<MachineData[], Error>({
    queryKey: ['machines'],
    queryFn: getMachines,
  });

  const { data: processSteps = [], isLoading: isLoadingSteps } = useQuery<ProcessStepData[], Error>({
    queryKey: ['processSteps'],
    queryFn: getProcessSteps,
  });

  // --- Create lookup maps for efficient rendering ---
  const orderMap = useMemo(() => new Map(orders.map(o => [o.id, o.order_id_code])), [orders]);
  const machineMap = useMemo(() => new Map(machines.map(m => [m.id, m.machine_id_code])), [machines]);
  const processStepMap = useMemo(() => new Map(processSteps.map(p => [p.id, p.step_name])), [processSteps]);
  
  // --- Combined loading state ---
  const isLoading = isLoadingLogs || isLoadingOrders || isLoadingMachines || isLoadingSteps;

  const deleteMutation = useMutation({
    mutationFn: deleteJobLog,
    onSuccess: () => {
      toast.success('Job log deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['jobLogs'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to delete job log');
    },
  });

  const handleDeleteLog = (id: number) => {
    // Replace window.confirm with a proper confirmation modal in the future
    if (window.confirm(`Are you sure you want to delete Job Log ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  const getStatusDisplay = (status: JobLogData['status']) => {
    switch (status) {
      case 'completed': return { text: 'Completed', color: 'text-green-700 bg-green-100' };
      case 'cancelled': return { text: 'Cancelled', color: 'text-red-700 bg-red-100' };
      // Add other statuses from your JobLogStatus enum
      default: return { text: status, color: 'text-gray-700 bg-gray-100' };
    }
  };

  return (
    <div className="bg-backgroundLight p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Job Logs</h2>
        {/* Add buttons here if needed */}
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Process Step</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Time</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Time</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Remarks</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading && (
              <tr><td colSpan={8} className="text-center py-4">Loading data...</td></tr>
            )}
            {!isLoading && jobLogs.length === 0 && (
              <tr><td colSpan={8} className="text-center py-4 text-gray-500">No job logs found.</td></tr>
            )}
            {!isLoading && jobLogs.map(log => {
              const status = getStatusDisplay(log.status);
              return (
                <tr key={log.id}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{orderMap.get(log.production_order_id) || `ID: ${log.production_order_id}`}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{machineMap.get(log.machine_id) || `ID: ${log.machine_id}`}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{processStepMap.get(log.process_step_id) || `ID: ${log.process_step_id}`}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{new Date(log.actual_start_time).toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{log.actual_end_time ? new Date(log.actual_end_time).toLocaleString() : '—'}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${status.color}`}>
                      {status.text}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{log.remarks || '—'}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleDeleteLog(log.id)}
                      className="text-red-600 hover:text-red-900 font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default JobLogs;