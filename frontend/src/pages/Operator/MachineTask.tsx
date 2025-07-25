import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  getMachineQueue,
  startTask,
  finishTask,
  reportIssue,
  pauseTask,
  cancelTask,
  type MachineQueue,
} from '../../api/operatorApi';

// A simple modal for reporting issues
const ReportIssueModal = ({ isOpen, onClose, onSubmit }: { isOpen: boolean, onClose: () => void, onSubmit: (reason: string) => void }) => {
  const [reason, setReason] = useState('');
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-sm">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Report Issue</h2>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full p-3 mb-4 border rounded text-lg"
        >
          <option value="">Select a reason...</option>
          <option value="Tool Breakage">Tool Breakage</option>
          <option value="No Material">No Material</option>
          <option value="Maintenance Needed">Maintenance Needed</option>
          <option value="Quality Check Failed">Quality Check Failed</option>
        </select>
        <div className="flex justify-end gap-4">
          <button onClick={onClose} className="px-4 py-2 bg-gray-300 rounded-md">Cancel</button>
          <button
            onClick={() => onSubmit(reason)}
            disabled={!reason}
            className="px-4 py-2 bg-red-600 text-white rounded-md disabled:bg-red-300"
          >
            Submit Report
          </button>
        </div>
      </div>
    </div>
  );
};


const MachineTaskPage: React.FC = () => {
  const { machineIdCode } = useParams<{ machineIdCode: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isIssueModalOpen, setIssueModalOpen] = useState(false);

  const { data: queue, isLoading, isError } = useQuery<MachineQueue, Error>({
    queryKey: ['machineQueue', machineIdCode],
    queryFn: () => getMachineQueue(machineIdCode!),
    refetchInterval: 15000, // Refreshes to check if prerequisites are complete
    enabled: !!machineIdCode,
  });

  const invalidateQueue = () => {
    queryClient.invalidateQueries({ queryKey: ['machineQueue', machineIdCode] });
  };

  // Mutations for ALL job actions
  const startMutation = useMutation({ mutationFn: startTask, onSuccess: invalidateQueue, onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to start task.") });
  const finishMutation = useMutation({ mutationFn: finishTask, onSuccess: invalidateQueue, onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to finish task.") });
  const issueMutation = useMutation({ mutationFn: (payload: { taskId: number; reason: string }) => reportIssue(payload.taskId, { reason: payload.reason }), onSuccess: invalidateQueue, onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to report issue.") });
  const pauseMutation = useMutation({ mutationFn: pauseTask, onSuccess: invalidateQueue, onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to pause task.") });
  const cancelMutation = useMutation({ mutationFn: cancelTask, onSuccess: invalidateQueue, onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to cancel task.") });

  useEffect(() => {
    const timerId = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timerId);
  }, []);

  const handleReportIssue = (reason: string) => {
    if (queue?.current_job && reason) {
      issueMutation.mutate({ taskId: queue.current_job.id, reason });
    }
    setIssueModalOpen(false);
  };

  if (isLoading) return <div className="bg-gray-900 text-white text-4xl flex items-center justify-center h-screen animate-pulse">Loading Machine Queue...</div>;
  if (isError) return <div className="bg-gray-900 text-red-500 text-4xl flex items-center justify-center h-screen">Error: Could not load data for machine '{machineIdCode}'.</div>;
  if (!queue) return <div className="bg-gray-900 text-white text-4xl flex items-center justify-center h-screen">No data available.</div>;

  const { current_job, next_task_in_sequence, is_next_task_ready, waiting_for } = queue;
  
  const jobToDisplay = current_job || next_task_in_sequence;
  const currentStatus = current_job?.status.toLowerCase();

  return (
    <div className="bg-gray-900 text-white h-screen flex flex-col p-4 md:p-8 font-sans">
      <ReportIssueModal isOpen={isIssueModalOpen} onClose={() => setIssueModalOpen(false)} onSubmit={handleReportIssue} />

      <header className="flex justify-between items-center border-b-2 border-gray-700 pb-4">
        <button onClick={() => navigate('/operator/select-machine')} className="text-blue-400 hover:text-blue-300 text-lg">
          &larr; Back to Machines
        </button>
        <h1 className="text-3xl md:text-5xl font-bold uppercase">{queue.machine_name}</h1>
        <div className="text-2xl md:text-4xl font-mono bg-gray-800 p-2 rounded-lg">
          {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center">
        {jobToDisplay ? (
          <>
            <div className={`text-4xl font-semibold mb-4 ${
              current_job ? 
                (currentStatus === 'in_progress' ? 'text-green-400 animate-pulse' :
                 currentStatus === 'blocked' ? 'text-red-500' :
                 currentStatus === 'paused' ? 'text-yellow-400' : 'text-gray-400')
              : (is_next_task_ready ? 'text-blue-400' : 'text-gray-500')
            }`}>
              {current_job ? currentStatus?.replace('_', ' ').toUpperCase() : (is_next_task_ready ? 'UP NEXT' : 'WAITING')}
            </div>
            
            <div className="text-8xl md:text-9xl font-bold mb-2">{jobToDisplay.job_id_code}</div>
            <div className="text-5xl md:text-6xl text-gray-300 mb-2">{jobToDisplay.product_name}</div>
            <div className="text-3xl text-gray-400">Qty: {jobToDisplay.quantity_to_produce} | Priority: {jobToDisplay.priority}</div>

            {!is_next_task_ready && waiting_for && !current_job && (
                <div className="mt-6 p-4 bg-yellow-900 border border-yellow-700 rounded-lg max-w-lg">
                    <p className="text-yellow-300 text-xl font-semibold">Cannot Start Job</p>
                    <p className="text-yellow-400 text-lg">Previous step '{waiting_for.step_name}' is not complete yet.</p>
                </div>
            )}
          </>
        ) : (
          <div className="text-5xl text-gray-500">NO JOBS READY FOR THIS MACHINE</div>
        )}
      </main>
      
      <footer className="w-full">
        {(() => {
          const status = queue?.current_job?.status.toLowerCase();

          if (status === 'in_progress') {
            return (
              <div className="grid grid-cols-2 gap-4">
                <button onClick={() => pauseMutation.mutate(queue.current_job!.id)} disabled={pauseMutation.isPending} className="w-full text-4xl font-bold p-6 rounded-lg bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-900">PAUSE</button>
                <button onClick={() => finishMutation.mutate(queue.current_job!.id)} disabled={finishMutation.isPending} className="w-full text-4xl font-bold p-6 rounded-lg bg-red-600 hover:bg-red-700 disabled:bg-red-900">FINISH</button>
              </div>
            );
          }
          
          if (status === 'paused' || status === 'blocked') {
            return (
              <div className="grid grid-cols-3 gap-4">
                <button onClick={() => setIssueModalOpen(true)} disabled={issueMutation.isPending} className="w-full text-3xl font-bold p-6 rounded-lg bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-900">REPORT ISSUE</button>
                <button onClick={() => { if (window.confirm('Are you sure you want to cancel this job?')) { cancelMutation.mutate(queue.current_job!.id); } }} disabled={cancelMutation.isPending} className="w-full text-3xl font-bold p-6 rounded-lg bg-gray-600 hover:bg-gray-700 disabled:bg-gray-900">CANCEL</button>
                <button onClick={() => startMutation.mutate(queue.current_job!.id)} disabled={startMutation.isPending} className="w-full text-3xl font-bold p-6 rounded-lg bg-green-600 hover:bg-green-700 disabled:bg-green-900">RESUME</button>
              </div>
            );
          }

          if (next_task_in_sequence && is_next_task_ready) {
            return (
              <button onClick={() => startMutation.mutate(next_task_in_sequence.id)} disabled={startMutation.isPending} className="w-full text-6xl font-bold p-8 rounded-lg bg-green-600 hover:bg-green-700 disabled:bg-green-900">
                {startMutation.isPending ? '...' : 'START JOB'}
              </button>
            );
          }
          
          return null;
        })()}
      </footer>
    </div>
  );
};

export default MachineTaskPage;
