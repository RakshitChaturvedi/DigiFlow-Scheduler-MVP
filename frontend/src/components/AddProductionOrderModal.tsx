import React, { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/axios';
import type { ProductionOrderData } from '../api/productionOrdersApi';

interface Props {
    onClose: () => void;
    isEditing?: boolean;
    initialData?: Partial<ProductionOrderData>;
}

const AddProductionOrderModal: React.FC<Props> = ({ onClose, isEditing=false, initialData }) => {
    const [formData, setFormData] = useState({
        order_id_code: '',
        product_name: '',
        product_route_id: '',
        quantity_to_produce: 1,
        priority: 1,
        arrival_time: new Date().toISOString(),
        due_date: '',
        current_status: "pending", 
    });

    const queryClient = useQueryClient();

    useEffect(()=> {
        if (isEditing && initialData) {
            setFormData({
                order_id_code: initialData.order_id_code || '',
                product_name: initialData.product_name || '',
                product_route_id: initialData.product_route_id || '',
                quantity_to_produce: initialData.quantity_to_produce || 1,
                priority: initialData.priority || 1,
                arrival_time: new Date(initialData.arrival_time || Date.now()).toISOString(),
                due_date: initialData.due_date ? new Date(initialData.due_date).toISOString().split('T')[0] : '',
                current_status: initialData.current_status || 'pending'
            });
        }
    }, [isEditing, initialData])

    const mutation = useMutation({
        mutationFn: async (order: Partial<ProductionOrderData>) => {
            if (isEditing && initialData) {
                const res = await apiClient.put(`/api/orders/${initialData.id}`, order);
                return res.data;
            } else {
                const res = await apiClient.post('/api/orders/', order);
                return res.data;
            }
        },
        onSuccess: () => {
            alert(isEditing ? 'Production order updated successfully!' : 'Production order created successfully!');
            queryClient.invalidateQueries({ queryKey: ['productionOrders'] });
            onClose();
        },
        onError: (err: any) => {
            alert(err.response?.data?.detail || 'Failed to create order');
        },
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>)  => {
        const {name, value} = e.target;

        setFormData((prev) => ({
            ...prev,
            [name]: name == 'quantity_to_produce' || name ==='priority'
                ? Number(value)
                : value,
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log("Submitting:", formData);
        mutation.mutate({
            ...formData,
            due_date: formData.due_date === '' ? null : formData.due_date,
            current_status: formData.current_status as 'pending' | 'in_progress' | 'completed' | 'cancelled',
        });
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
                <h2 className="text-lg font-bold mb-4">
                    {isEditing ? 'Edit Production Order' : 'Add Production Order'}
                </h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Order ID Code
                        </label>
                        <input
                            type="text"
                            name="order_id_code"
                            value={formData.order_id_code}
                            onChange={handleChange}
                            required
                            placeholder="e.g. JOB20250703_01"
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Product Name
                        </label>
                        <input
                            type="text"
                            name="product_name"
                            value={formData.product_name}
                            onChange={handleChange}
                            placeholder="e.g. Cap for 250ml Bottle"
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Product Route ID
                        </label>
                        <input
                            type="text"
                            name="product_route_id"
                            value={formData.product_route_id}
                            onChange={handleChange}
                            required
                            placeholder="e.g. 2"
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Quantity to Produce
                        </label>
                        <input
                            type="number"
                            name="quantity_to_produce"
                            value={formData.quantity_to_produce}
                            onChange={handleChange}
                            min={1}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Priority (1 = highest)
                        </label>
                        <input
                            type="number"
                            name="priority"
                            value={formData.priority}
                            onChange={handleChange}
                            min={1}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Arrival Time (auto-set)
                        </label>
                        <input
                            type="datetime-local"
                            name="arrival_time"
                            value={formData.arrival_time.slice(0, 16)}
                            onChange={handleChange}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Due Date
                        </label>
                        <input
                            type="date"
                            name="due_date"
                            value={formData.due_date}
                            onChange={handleChange}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                        />
                    </div>

                    <div className="flex justify-end gap-2 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            {isEditing ? 'Update Order' : 'Create Order'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddProductionOrderModal;