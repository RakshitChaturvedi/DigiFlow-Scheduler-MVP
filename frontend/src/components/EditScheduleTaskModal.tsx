import React, { useState } from 'react';
import type { ScheduledTaskData } from '../api/scheduledTaskApi';

interface EditModalProps {
    task: ScheduledTaskData;
    isOpen: boolean;
    onClose: () => void;
    onSave: (updates: Partial<ScheduledTaskData>) => void;
}

const EditScheduledTaskModal: React.FC<EditModalProps> = ({ task, isOpen, onClose, onSave }) => {
    const [status, setStatus] = useState(task.status);
    const [startTime, setStartTime] = useState(task.start_time);
    const [endTime, setEndTime] = useState(task.end_time);

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave({
            status,
            start_time: startTime,
            end_time: endTime,
        });
    };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-[400px]">
        <h3 className="text-lg font-semibold mb-4">Edit Scheduled Task</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full border px-3 py-2 rounded">
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Start Time</label>
            <input
              type="datetime-local"
              value={startTime.slice(0, 16)} // ISO format to local datetime
              onChange={(e) => setStartTime(new Date(e.target.value).toISOString())}
              className="w-full border px-3 py-2 rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">End Time</label>
            <input
              type="datetime-local"
              value={endTime.slice(0, 16)}
              onChange={(e) => setEndTime(new Date(e.target.value).toISOString())}
              className="w-full border px-3 py-2 rounded"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 rounded">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditScheduledTaskModal;