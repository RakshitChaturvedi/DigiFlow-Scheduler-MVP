import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { createMachine, updateMachine, type MachineData } from '../api/machinesAPI'
import { queryClient } from '../lib/react-query';
import toast from 'react-hot-toast';


type Props = {
  isEditing: boolean;
  initialData?: MachineData;
  onClose: () => void;
};

const AddMachineModal: React.FC<Props> = ({ isEditing, initialData, onClose }) => {
  const [form, setForm] = React.useState({
    machine_id_code: initialData?.machine_id_code || '',
    machine_type: initialData?.machine_type || '',
    default_setup_time_mins: initialData?.default_setup_time_mins?.toString() || '0',
    is_active: initialData?.is_active ?? true,
  });

  const mutation = useMutation({
    mutationFn: isEditing
      ? (data: any) => updateMachine(initialData!.id, data)
      : createMachine,
    onSuccess: () => {
      toast.success(`Machine ${isEditing ? 'updated' : 'created'} successfully!`);
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to save machine');
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
      machine_id_code: form.machine_id_code.trim(),
      machine_type: form.machine_type.trim(),
      default_setup_time_mins: parseInt(form.default_setup_time_mins),
      is_active: form.is_active,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'Edit Machine' : 'Add Machine'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            name="machine_id_code"
            placeholder="Machine ID Code"
            value={form.machine_id_code}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            name="machine_type"
            placeholder="Machine Type"
            value={form.machine_type}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
          <input
            name="default_setup_time_mins"
            placeholder="Default Setup Time (mins)"
            type="number"
            value={form.default_setup_time_mins}
            onChange={handleChange}
            required
            min={0}
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

export default AddMachineModal;
