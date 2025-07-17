import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getMachines,
  deleteMachine,
  type MachineData,
} from '../../api/machinesAPI';
import { queryClient } from '../../lib/react-query';
import AddMachineModal from '../../components/AddMachineModal';
import ImportMachinesModal from '../../components/ImportMachinesModal';

const Machines: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedMachine, setSelectedMachine] = React.useState<MachineData | null>(null);

  const { data: machines, isLoading, isError, error } = useQuery<MachineData[], Error>({
    queryKey: ['machines'],
    queryFn: getMachines,
    staleTime: 5 * 60 * 1000,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMachine,
    onSuccess: () => {
      alert('Machine deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['machines'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete machine');
    }
  });

  const handleAddMachine = () => {
    setIsEditing(false);
    setSelectedMachine(null);
    setIsAddModalOpen(true);
  };

  const handleEditMachine = (machine: MachineData) => {
    setIsEditing(true);
    setSelectedMachine(machine);
    setIsAddModalOpen(true);
  };

  const handleDeleteMachine = (id: number) => {
    if (window.confirm(`Are you sure you want to delete machine ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Machines</h2>
        <div className="flex gap-4">
          <button
            onClick={handleAddMachine}
            className="bg-primaryBlue text-white px-5 py-2 rounded-lg hover:bg-blue-700"
          >
            Add Machine
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-gray-700 text-white px-5 py-2 rounded-lg hover:bg-gray-800"
          >
            Import Machines
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-borderColor">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Setup Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
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
              {!isLoading && !isError && machines?.length === 0 && (
                <tr><td colSpan={5} className="text-center py-4 text-gray-500">No machines found.</td></tr>
              )}
              {!isLoading && !isError && machines?.map(machine => (
                <tr key={machine.id}>
                  <td className="px-6 py-4 text-sm">{machine.machine_id_code}</td>
                  <td className="px-6 py-4 text-sm">{machine.machine_type}</td>
                  <td className="px-6 py-4 text-sm">{machine.default_setup_time_mins} mins</td>
                  <td className="px-6 py-4 text-sm">{machine.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="px-6 py-4 text-right space-x-4">
                    <button
                      onClick={() => handleEditMachine(machine)}
                      className="text-yellow-600 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteMachine(machine.id)}
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
        <AddMachineModal
          isEditing={isEditing}
          initialData={selectedMachine ?? undefined}
          onClose={() => {
            setIsAddModalOpen(false);
            setIsEditing(false);
            setSelectedMachine(null);
            queryClient.invalidateQueries({ queryKey: ['machines'] });
          }}
        />
      )}

      {isImportModalOpen && (
        <ImportMachinesModal
          onClose={() => setIsImportModalOpen(false)}
        />
      )}
    </div>
  );
};

export default Machines;
