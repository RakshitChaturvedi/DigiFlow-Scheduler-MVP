import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getProcessSteps,
  deleteProcessStep,
  type ProcessStepData,
} from '../../api/processStepsApi';
import { queryClient } from '../../lib/react-query';
import AddProcessStepModal from '../../components/AddProcessStepModal';
import ImportProcessStepsModal from '../../components/ImportProcessStepsModal';

const ProcessSteps: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedStep, setSelectedStep] = React.useState<ProcessStepData | null>(null);

  const { data: steps, isLoading, isError, error } = useQuery<ProcessStepData[], Error>({
    queryKey: ['processSteps'],
    queryFn: getProcessSteps,
    staleTime: 5 * 60 * 1000,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProcessStep,
    onSuccess: () => {
      alert('Process step deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['processSteps'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete process step');
    },
  });

  const handleAddStep = () => {
    setIsEditing(false);
    setSelectedStep(null);
    setIsAddModalOpen(true);
  };

  const handleEditStep = (step: ProcessStepData) => {
    setIsEditing(true);
    setSelectedStep(step);
    setIsAddModalOpen(true);
  };

  const handleDeleteStep = (id: number) => {
    if (window.confirm(`Are you sure you want to delete process step ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Process Steps</h2>
        <div className="flex gap-4">
          <button
            onClick={handleAddStep}
            className="bg-primaryBlue text-white px-5 py-2 rounded-lg hover:bg-blue-700"
          >
            Add Process Step
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-gray-700 text-white px-5 py-2 rounded-lg hover:bg-gray-800"
          >
            Import Steps
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-borderColor">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Step Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Step Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Step Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base Duration per Unit</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Required Machine Type</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-borderColor">
              {isLoading && (
                <tr><td colSpan={5} className="text-center py-4">Loading...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={5} className="text-center py-4 text-red-600">{error.message}</td></tr>
              )}
              {!isLoading && !isError && steps?.length === 0 && (
                <tr><td colSpan={5} className="text-center py-4 text-gray-500">No process steps found.</td></tr>
              )}
              {!isLoading && !isError && steps?.map(step => (
                <tr key={step.id}>
                  <td className="px-6 py-4 text-sm">{step.product_route_id}</td>
                  <td className="px-6 py-4 text-sm">{step.step_number}</td>
                  <td className="px-6 py-4 text-sm">{step.step_name}</td>
                  <td className="px-6 py-4 text-sm">{step.base_duration_per_unit_mins} mins</td>
                  <td className="px-6 py-4 text-sm">{step.required_machine_type}</td>
                  <td className="px-6 py-4 text-right space-x-4">
                    <button
                      onClick={() => handleEditStep(step)}
                      className="text-yellow-600 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteStep(step.id)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isAddModalOpen && (
        <AddProcessStepModal
          isEditing={isEditing}
          initialData={selectedStep ?? undefined}
          onClose={() => {
            setIsAddModalOpen(false);
            setIsEditing(false);
            setSelectedStep(null);
            queryClient.invalidateQueries({ queryKey: ['processSteps'] });
          }}
        />
      )}

      {isImportModalOpen && (
        <ImportProcessStepsModal
          onClose={() => setIsImportModalOpen(false)}
        />
      )}
    </div>
  );
};

export default ProcessSteps;
