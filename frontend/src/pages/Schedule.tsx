import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getScheduledTasks, deleteScheduledTask, updateScheduledTask, type ScheduledTaskData } from '../api/scheduledTaskApi';
import { toast } from 'react-toastify'; // Not used in this snippet
import { queryClient } from '../lib/react-query';
import EditScheduledTaskModal from '../components/EditScheduleTaskModal';

const SchedulePage: React.FC = () => {
  // const navigate = useNavigate(); // If you need navigation, keep this
  // const toast = useToast(); // If you use a toast library, ensure it's imported correctly

  const [editTask, setEditTask] = useState<ScheduledTaskData | null>(null);
  const [isModalOpen, setModalOpen] = useState(false);

  const { data: scheduledTasks = [], isLoading, isError, error } = useQuery<ScheduledTaskData[], Error>({
    queryKey: ['scheduledTasks'],
    queryFn: getScheduledTasks,
    staleTime: 5 * 60 * 1000,
    // refetchInterval: 60 * 1000, // Optional: Refetch every minute for "live" updates
  });

  const visibleTasks = scheduledTasks.filter(
    order => order.status === 'scheduled' 
  )

  // Helper function to get status display text and color (reused from ProductionOrders)
  const getStatusDisplay = (status: string) => {
    switch (status.toLowerCase()) { // Ensure status is lowercased for consistent matching
      case 'completed': return { text: 'Completed', color: 'bg-green-100 text-green-700' };
      case 'in_progress': return { text: 'In Progress', color: 'bg-orange-100 text-orange-700' };
      case 'scheduled': return { text: 'Scheduled', color: 'bg-blue-100 text-blue-700' };
      case 'delayed': return { text: 'Delayed', color: 'bg-red-100 text-red-700' };
      case 'cancelled': return { text: 'Cancelled', color: 'bg-gray-100 text-gray-700' }; // Assuming a cancelled status
      default: return { text: status, color: 'bg-gray-100 text-gray-700' };
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this scheduled task?")) return;

    try {
      await deleteScheduledTask(id);
      toast.success("Deleted scheduled task.");
      queryClient.invalidateQueries({ queryKey: ['visibleTasks'] });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Delete failed");
    }
  };

  const handleEditSubmit = async (id: number, updates: Partial<ScheduledTaskData>) => {
    try {
      await updateScheduledTask(id, updates);
      toast.success("Scheduled task updated.");
      queryClient.invalidateQueries({ queryKey: ['visibleTasks'] });
      setModalOpen(false);
      setEditTask(null);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Update failed");
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Production Schedule</h2>
        {/* Optional: Add a "Refresh" button here if desired */}
        {/* <button onClick={() => refetch()} className="bg-primaryBlue text-white px-4 py-2 rounded-lg">Refresh</button> */}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-borderColor">
            <thead className="bg-gray-50">
              <tr>{/* */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job ID</th>{/* New */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order Code</th>{/* Changed */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product Name</th>{/* New */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Process Step</th>{/* Changed */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine</th>{/* Changed */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Time</th>{/* */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Time</th>{/* */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration (min)</th>{/* */}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>{/* */}
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>Actions</th>{/* */}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-borderColor">
              {isLoading && (
                <tr>{/* */}
                  <td colSpan={9} className="text-center py-4">Loading scheduled tasks...</td>{/* Adjusted colSpan */}
                </tr>
              )}
              {isError && (
                <tr>{/* */}
                  <td colSpan={9} className="text-center py-4 text-red-600"> {/* Adjusted colSpan */}
                    Error loading schedule: {error.message}
                  </td>
                </tr>
              )}
              {!isLoading && !isError && visibleTasks.length === 0 && (
                <tr>{/* */}
                  <td colSpan={9} className="text-center py-4 text-gray-500"> {/* Adjusted colSpan */}
                    No scheduled tasks found.
                  </td>
                </tr>
              )}
              {!isLoading && !isError && visibleTasks.map((task) => {
                const statusInfo = getStatusDisplay(task.status); // Get status text and color
                return (
                  <tr key={task.id}>{/* */}
                    <td className="px-6 py-4 text-sm">{task.job_id_code || '-'}</td> {/* Display job_id_code */}
                    <td className="px-6 py-4 text-sm">{task.production_order.order_id_code}</td> {/* Nested access */}
                    <td className="px-6 py-4 text-sm">{task.production_order.product_name || '-'}</td> {/* Nested access, handle nullable */}
                    <td className="px-6 py-4 text-sm">
                      {task.process_step_definition.step_name} (Step {task.process_step_definition.step_number}) {/* Nested access */}
                    </td>
                    <td className="px-6 py-4 text-sm">{task.assigned_machine.machine_id_code}</td> {/* Nested access */}
                    <td className="px-6 py-4 text-sm">{new Date(task.start_time).toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm">{new Date(task.end_time).toLocaleString()}</td>
                    <td className="px-6 py-4 text-sm">{task.scheduled_duration_mins}</td>
                    <td className="px-6 py-4 text-sm capitalize">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusInfo.color}`}>
                        {statusInfo.text}
                      </span>
                    </td>
                    <td className='px-6 py-4 text-sm'>
                      <div className='flex gap-2'>
                        <button className='text-blue-600 hover:underline' onClick={() => {setEditTask(task); setModalOpen(true);}}>Edit</button>
                        <button className='text-red-600 hover:underline' onClick={() => handleDelete(task.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      {editTask && (
        <EditScheduledTaskModal 
          task={editTask}
          isOpen={isModalOpen}
          onClose={() => setModalOpen(false)}
          onSave={(updates) => handleEditSubmit(editTask.id, updates)}
        />
      )}
    </div>
  );
};

export default SchedulePage;
