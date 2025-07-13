import React, { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { JobLogData, JobLogStatus } from '../api/jobLogApi';
import { createJobLog, updateJobLog } from '../api/jobLogApi';

interface Props {
  onClose: () => void;
  isEditing?: boolean;
  initialData?: Partial<JobLogData>;
}

const AddJobLogModal: React.FC<Props> = ({ onClose, isEditing = false, initialData }) => {
  const [formData, setFormData] = useState({
    production_order_id: 0,
    process_step_id: 0,
    machine_id: 0,
    actual_start_time: new Date().toISOString(),
    actual_end_time: '',
    status: 'completed' as JobLogStatus,
    remarks: '',
  });

  const queryClient = useQueryClient();

  useEffect(() => {
    if (isEditing && initialData) {
      setFormData({
        production_order_id: initialData.production_order_id || 0,
        process_step_id: initialData.process_step_id || 0,
        machine_id: initialData.machine_id || 0,
        actual_start_time: new Date(initialData.actual_start_time || Date.now()).toISOString(),
        actual_end_time: initialData.actual_end_time ? new Date(initialData.actual_end_time).toISOString().slice(0, 16) : '',
        status: initialData.status || 'completed',
        remarks: initialData.remarks || '',
      });
    }
  }, [isEditing, initialData]);

  const mutation = useMutation({
    mutationFn: async (log: any) => {
      if (isEditing && initialData?.id) {
        return await updateJobLog(initialData.id, log);
      } else {
        return await createJobLog(log);
      }
    },
    onSuccess: () => {
      alert(isEditing ? 'Job log updated successfully!' : 'Job log created successfully!');
      queryClient.invalidateQueries({ queryKey: ['jobLogs'] });
      onClose();
    },
    onError: (err: any) => {
      alert(err?.response?.data?.detail || 'Failed to save job log.');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['production_order_id', 'process_step_id', 'machine_id'].includes(name)
        ? Number(value)
        : value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      ...formData,
      actual_end_time: formData.actual_end_time || null,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
        <h2 className="text-lg font-bold mb-4">
          {isEditing ? 'Edit Job Log' : 'Add Job Log'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="number" name="production_order_id" value={formData.production_order_id} onChange={handleChange} placeholder="Production Order ID" className="w-full border px-3 py-2 rounded" required />
          <input type="number" name="process_step_id" value={formData.process_step_id} onChange={handleChange} placeholder="Process Step ID" className="w-full border px-3 py-2 rounded" required />
          <input type="number" name="machine_id" value={formData.machine_id} onChange={handleChange} placeholder="Machine ID" className="w-full border px-3 py-2 rounded" required />

          <label className="block text-sm font-medium text-gray-700">Actual Start Time</label>
          <input type="datetime-local" name="actual_start_time" value={formData.actual_start_time.slice(0, 16)} onChange={handleChange} className="w-full border px-3 py-2 rounded" required />

          <label className="block text-sm font-medium text-gray-700">Actual End Time</label>
          <input type="datetime-local" name="actual_end_time" value={formData.actual_end_time} onChange={handleChange} className="w-full border px-3 py-2 rounded" />

          <label className="block text-sm font-medium text-gray-700">Status</label>
          <select name="status" value={formData.status} onChange={handleChange} className="w-full border px-3 py-2 rounded">
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="aborted">Aborted</option>
          </select>

          <textarea name="remarks" value={formData.remarks} onChange={handleChange} placeholder="Remarks (optional)" className="w-full border px-3 py-2 rounded" rows={3} />

          <div className="flex justify-end gap-2 mt-6">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              {isEditing ? 'Update Log' : 'Create Log'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddJobLogModal;