import React, { useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { type SubmitHandler, useForm } from 'react-hook-form';
import { type ProductionOrderData, createProductionOrder, updateProductionOrder } from '../api/productionOrdersApi';
import toast from 'react-hot-toast';

type FormData = Omit<ProductionOrderData, 'id' | 'created_at' | 'updated_at' | 'progress'>;

interface Props {
  onClose: () => void;
  isEditing?: boolean;
  initialData?: ProductionOrderData;
}

const AddProductionOrderModal: React.FC<Props> = ({ onClose, isEditing = false, initialData }) => {
    const { register, handleSubmit, reset, formState: { errors,  isSubmitting } } = useForm<FormData>({
        defaultValues: initialData ? {
        ...initialData,
        arrival_time: initialData.arrival_time.slice(0, 16), // Format for datetime-local input
        due_date: initialData.due_date ? initialData.due_date.slice(0, 10) : '', // Format for date input
        } : {
        priority: 1,
        quantity_to_produce: 1,
        current_status: 'pending',
        }
    });

    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: (order: Omit<ProductionOrderData, 'id' | 'created_at' | 'updated_at' | 'progress'>) => {
        return isEditing && initialData
            ? updateProductionOrder(initialData.id, order)
            : createProductionOrder(order);
        },
        onSuccess: () => {
        toast.success(`Production order ${isEditing ? 'updated' : 'created'} successfully!`);
        queryClient.invalidateQueries({ queryKey: ['productionOrders'] });
        onClose();
        },
        onError: (err: any) => {
        toast.error(err.response?.data?.detail || 'Failed to save order');
        },
    });

    const onSubmit: SubmitHandler<FormData> = (data) => {
        mutation.mutate({
        ...data,
        due_date: data.due_date || null,
        priority: Number(data.priority),
        quantity_to_produce: Number(data.quantity_to_produce),
        });
    };

    useEffect(() => {
        if (initialData) {
        reset({
            ...initialData,
            arrival_time: initialData.arrival_time.slice(0, 16),
            due_date: initialData.due_date ? initialData.due_date.slice(0, 10) : '',
        });
        }
    }, [initialData, reset]);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
            <h2 className="text-lg font-bold mb-4">{isEditing ? 'Edit Production Order' : 'Add Production Order'}</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <input {...register('order_id_code', { required: true })} placeholder="Order ID Code" className="w-full border p-2 rounded" />
            <input {...register('product_name')} placeholder="Product Name" className="w-full border p-2 rounded" />
            <input {...register('product_route_id', { required: true })} placeholder="Product Route ID" className="w-full border p-2 rounded" />
            <input type="number" {...register('quantity_to_produce', { required: true, valueAsNumber: true, min: 1 })} placeholder="Quantity" className="w-full border p-2 rounded" />
            <input type="number" {...register('priority', { required: true, valueAsNumber: true, min: 1 })} placeholder="Priority" className="w-full border p-2 rounded" />
            <input type="datetime-local" {...register('arrival_time', { required: true })} className="w-full border p-2 rounded" />
            <input type="date" {...register('due_date')} className="w-full border p-2 rounded" />
            
            <div className="flex justify-end gap-2 mt-6">
                <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300">
                {isSubmitting ? 'Saving...' : (isEditing ? 'Update Order' : 'Create Order')}
                </button>
            </div>
            </form>
        </div>
        </div>
    );
};

export default AddProductionOrderModal;