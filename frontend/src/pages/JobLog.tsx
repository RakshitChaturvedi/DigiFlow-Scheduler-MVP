import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { deleteJobLog, getJobLogs, type JobLogData } from '../api/jobLogApi';
import { queryClient } from '../lib/react-query';

const JobLogs: React.FC = () => {
  const { data: jobLogs = [], isLoading, isError, error } = useQuery<JobLogData[], Error>({
    queryKey: ['jobLogs'],
    queryFn: getJobLogs,
    staleTime: 5 * 60 * 1000,
  });

  const visibleJobs = jobLogs.filter(
    order => order.status === 'completed' || order.status === 'cancelled' || order.status === 'aborted'
  )

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
    if (window.confirm(`Are you sure you want to delete Job Log ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  const getStatusDisplay = (status: JobLogData['status']) => {
    switch (status) {
      case 'completed': return { text: 'Completed', color: 'text-green-600 bg-green-100' };
      case 'cancelled': return { text: 'Cancelled', color: 'text-red-600 bg-red-100' };
      case 'aborted': return { text: 'Aborted', color: 'text-yellow-600 bg-yellow-100' };
      default: return { text: status, color: 'text-gray-600 bg-gray-100' };
    }
  };

  return (
    <div className="bg-backgroundLight p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Job Logs</h2>
        <div className="space-x-4">
          <button
            className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-800"
            disabled
          >
            Import
          </button>
          <button
            className="bg-primaryBlue text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            disabled
          >
            Export
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine ID</th>
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
              <tr>
                <td colSpan={8} className="text-center py-4">Loading...</td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={8} className="text-center text-red-600 py-4">{error.message}</td>
              </tr>
            )}
            {!isLoading && !isError && visibleJobs.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-4 text-gray-500">No job logs found.</td>
              </tr>
            )}
            {!isLoading && !isError && visibleJobs.map(log => {
              const status = getStatusDisplay(log.status);
              return (
                <tr key={log.id}>
                  <td className="px-6 py-4 text-sm">{log.production_order_id}</td>
                  <td className="px-6 py-4 text-sm">{log.machine_id}</td>
                  <td className="px-6 py-4 text-sm">{log.process_step_id}</td>
                  <td className="px-6 py-4 text-sm">{new Date(log.actual_start_time).toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm">
                    {log.actual_end_time ? new Date(log.actual_end_time).toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 text-xs rounded-full font-semibold ${status.color}`}>
                      {status.text}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{log.remarks || '-'}</td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleDeleteLog(log.id)}
                      className="text-red-600 hover:underline"
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
