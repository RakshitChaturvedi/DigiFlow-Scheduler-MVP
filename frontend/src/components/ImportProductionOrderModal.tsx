import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/axios'

interface Props {
    onClose: () => void;
}

const ImportOrdersModal: React.FC<Props> = ({ onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await apiClient.post('/api/orders/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: (data) => {
      alert(data?.message || 'Orders imported successfully!');
      queryClient.invalidateQueries({ queryKey: ['productionOrders'] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail || 'Import failed');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!file) {
      setError('Please select a file.');
      return;
    }

    if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Only CSV or Excel files are supported.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    mutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-96 shadow-md">
        <h2 className="text-xl font-bold mb-4">Import Production Orders</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="file"
            accept=".csv, .xlsx, .xls"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer p-2 mb-3"
          />
          {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-300 text-gray-800 px-4 py-2 rounded hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Upload
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ImportOrdersModal;