import React, { useEffect } from 'react';
import { useForm, type SubmitHandler } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  createProcessStep,
  updateProcessStep,
  type ProcessStepData,
} from '../api/processStepsApi';

// This now matches the backend schema exactly
type FormData = Omit<ProcessStepData, 'id'>;

type Props = {
  isEditing: boolean;
  initialData?: ProcessStepData;
  onClose: () => void;
};

const AddProcessStepModal: React.FC<Props> = ({ isEditing, initialData, onClose }) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: isEditing && initialData ? initialData : {
      product_route_id: '',
      step_number: 1,
      step_name: '',
      required_machine_type: '',
      base_duration_per_unit_mins: 10,
    },
  });

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      isEditing && initialData
        ? updateProcessStep(initialData.id, data)
        : createProcessStep(data),
    onSuccess: () => {
      toast.success(`Process Step ${isEditing ? 'updated' : 'created'} successfully!`);
      queryClient.invalidateQueries({ queryKey: ['processSteps'] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to save process step.');
    },
  });

  const onSubmit: SubmitHandler<FormData> = (data) => {
    // Convert numeric fields from string input if necessary
    const payload = {
      ...data,
      step_number: Number(data.step_number),
      base_duration_per_unit_mins: Number(data.base_duration_per_unit_mins),
    };
    mutation.mutate(payload);
  };
  
  // Reset form when modal opens or initialData changes
  useEffect(() => {
    if (isEditing && initialData) {
      reset(initialData);
    } else {
      reset();
    }
  }, [isEditing, initialData, reset]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'Edit Process Step' : 'Add Process Step'}
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Product Route ID</label>
            <input
              {...register('product_route_id', { required: 'Route ID is required' })}
              placeholder="e.g., MOLD-001-ROUTE"
              className="w-full border border-gray-300 rounded px-3 py-2 mt-1"
            />
            {errors.product_route_id && <p className="text-red-500 text-sm mt-1">{errors.product_route_id.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Step Name</label>
            <input
              {...register('step_name', { required: 'Step name is required' })}
              placeholder="e.g., CNC Milling"
              className="w-full border border-gray-300 rounded px-3 py-2 mt-1"
            />
            {errors.step_name && <p className="text-red-500 text-sm mt-1">{errors.step_name.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Step Number</label>
            <input
              type="number"
              {...register('step_number', { required: 'Step number is required', valueAsNumber: true, min: { value: 1, message: 'Must be at least 1' } })}
              placeholder="1"
              className="w-full border border-gray-300 rounded px-3 py-2 mt-1"
            />
            {errors.step_number && <p className="text-red-500 text-sm mt-1">{errors.step_number.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Required Machine Type</label>
            <input
              {...register('required_machine_type', { required: 'Machine type is required' })}
              placeholder="e.g., VMC"
              className="w-full border border-gray-300 rounded px-3 py-2 mt-1"
            />
            {errors.required_machine_type && <p className="text-red-500 text-sm mt-1">{errors.required_machine_type.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Base Duration per Unit (mins)</label>
            <input
              type="number"
              {...register('base_duration_per_unit_mins', { required: 'Duration is required', valueAsNumber: true, min: { value: 1, message: 'Must be at least 1' } })}
              placeholder="e.g., 30"
              className="w-full border border-gray-300 rounded px-3 py-2 mt-1"
            />
            {errors.base_duration_per_unit_mins && <p className="text-red-500 text-sm mt-1">{errors.base_duration_per_unit_mins.message}</p>}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300">
              {isSubmitting ? 'Saving...' : (isEditing ? 'Update Step' : 'Create Step')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProcessStepModal;
