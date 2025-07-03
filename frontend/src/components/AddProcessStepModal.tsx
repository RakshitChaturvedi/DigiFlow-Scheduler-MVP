import React from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  createProcessStep,
  updateProcessStep,
  type ProcessStepData
} from '../api/processStepsApi';
import { queryClient } from '../lib/react-query';

type Props = {
  isEditing: boolean;
  initialData?: ProcessStepData;
  onClose: () => void;
};

const AddProcessStepModal: React.FC<Props> = ({ isEditing, initialData, onClose }) => {
  const [form, setForm] = React.useState({
    name: initialData?.name || '',
    sequence: initialData?.sequence?.toString() || '1',
    is_active: initialData?.is_active ?? true,
  });

  const mutation = useMutation({
    mutationFn: isEditing
      ? (data: any) => updateProcessStep(initialData!.id, data)
      : createProcessStep,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['process-steps'] });
      onClose();
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to save process step');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const fieldValue =
      type === 'checkbox' && 'checked' in e.target
        ? (e.target as HTMLInputElement).checked
        : value;

    setForm((prev) => ({
      ...prev,
      [name]: fieldValue,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      name: form.name.trim(),
      sequence: parseInt(form.sequence),
      is_active: form.is_active,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'Edit Process Step' : 'Add Process Step'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            name="name"
            placeholder="Step Name"
            value={form.name}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            name="sequence"
            placeholder="Sequence Number"
            type="number"
            value={form.sequence}
            onChange={handleChange}
            required
            min={1}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              name="is_active"
              checked={form.is_active}
              onChange={handleChange}
            />
            Active
          </label>
          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 rounded">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 bg-primaryBlue text-white rounded">
              {isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProcessStepModal;
