import React from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getDowntimeEvents,
  deleteDowntimeEvent,
} from '../../api/downtimeEventsApi';
import { queryClient } from '../../lib/react-query';
import AddDowntimeEventsModal from '../../components/AddDowntimeEventsModal';
import ImportDowntimeEventsModal from '../../components/ImportDowntimeEventsModal';
import { getMachines, type MachineData } from '../../api/machinesAPI';
import type { DowntimeEventData } from '../../api/downtimeEventsApi';

const DowntimeEvents: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [selectedEvent, setSelectedEvent] = React.useState<DowntimeEventData | null>(null);
  const [selectedDowntime, setSelectedDowntime] = React.useState<DowntimeEventData | null>(null);

  const { data: events, isLoading, isError, error } = useQuery<DowntimeEventData[], Error>({
    queryKey: ['downtimeEvents'],
    queryFn: getDowntimeEvents,
    staleTime: 5 * 60 * 1000,
  });

  const { data: machines = [], isLoading: isMachinesLoading, isError: isMachinesError } = useQuery<MachineData[], Error>({
    queryKey: ['machines'],
    queryFn: getMachines,
    staleTime: 5 * 60 * 1000,
  });

  const adaptedMachines = machines?.map((m) => ({
    id: m.id,
    name: m.machine_id_code,  // use `machine_id` as fallback name
  }));

  const machineIdToNameMap = React.useMemo(() => {
    const map = new Map();
    adaptedMachines?.forEach(m => map.set(m.id, m.name));
    return map;
  }, [adaptedMachines]);


  const deleteMutation = useMutation({
    mutationFn: deleteDowntimeEvent,
    onSuccess: () => {
      alert('Downtime event deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['downtimeEvents'] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete downtime event.');
    },
  });

  const handleAddEvent = () => {
    setIsEditing(false);
    setSelectedEvent(null);
    setIsAddModalOpen(true);
  };

  const handleEditEvent = (event: DowntimeEventData) => {
    setIsEditing(true);
    setSelectedEvent(event);
    setIsAddModalOpen(true);
  };

  const handleDeleteEvent = (id: number) => {
    if (window.confirm(`Are you sure you want to delete downtime event ${id}?`)) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="bg-backgroundLight overflow-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-textDark">Downtime Events</h2>
        <div className="flex gap-4">
          <button
            onClick={handleAddEvent}
            className="bg-primaryBlue text-white px-5 py-2 rounded-lg hover:bg-blue-700"
          >
            Add Downtime
          </button>
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="bg-gray-700 text-white px-5 py-2 rounded-lg hover:bg-gray-800"
          >
            Import Downtime
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-borderColor">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Machine</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
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
              {!isLoading && !isError && events?.length === 0 && (
                <tr><td colSpan={5} className="text-center py-4 text-gray-500">No downtime events found.</td></tr>
              )}
              {!isLoading && !isError && events?.map(event => (
                <tr key={event.id}>
                  <td className="px-6 py-4 text-sm">{machineIdToNameMap.get(event.machine_id) || event.machine_id}</td>
                  <td className="px-6 py-4 text-sm">{new Date(event.start_time).toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm">{new Date(event.end_time).toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm">{event.reason}</td>
                  <td className="px-6 py-4 text-right space-x-4">
                    <button onClick={() => handleEditEvent(event)} className="text-yellow-600 hover:underline">Edit</button>
                    <button onClick={() => handleDeleteEvent(event.id)} className="text-red-600 hover:underline">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>

          </table>
        </div>
      </div>

      {isAddModalOpen && !isMachinesLoading && (
      <AddDowntimeEventsModal
          isOpen={isAddModalOpen}
          machines={adaptedMachines}
          onClose={() => {
            setIsAddModalOpen(false);
            setIsEditing(false);
            setSelectedEvent(null);
            queryClient.invalidateQueries({ queryKey: ['downtimeEvents'] })
          }}
          isEditing={isEditing}
          initialData={selectedEvent ?? undefined}
          onSuccess={() => {
            setIsAddModalOpen(false);
            setSelectedEvent(null);
            queryClient.invalidateQueries({ queryKey: ['downtimeEvents'] });
          }}
      />
      )}

      {isImportModalOpen && (
        <ImportDowntimeEventsModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
          onSuccess={() => queryClient.invalidateQueries({ queryKey: ['downtimeEvents'] })}
        />
      )}
    </div>
  );
};

export default DowntimeEvents;
