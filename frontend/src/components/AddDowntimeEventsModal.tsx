// AddDowntimeEventsModal.tsx
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import {
  createDowntimeEvent,
  updateDowntimeEvent,
  type DowntimeEventData,
} from "../api/downtimeEventsApi";
import { formatInTimeZone } from "date-fns-tz"; 
import {toast} from 'react-hot-toast';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  machines: { id: number; name: string }[];
  isEditing: boolean;
  initialData?: DowntimeEventData;
  onSuccess: () => void;
};

type FormData = {
  machine_id: number;
  reason: string;
  start_time: string;
  end_time: string;
};

// ✅ Helper to convert datetime-local (assumed IST) → UTC ISO
const convertIstToUtcIso = (datetime: string): string =>
  formatInTimeZone(new Date(datetime), 'Asia/Kolkata', "yyyy-MM-dd'T'HH:mm:ssXXX");

const AddDowntimeEventsModal: React.FC<Props> = ({
  isOpen,
  onClose,
  machines,
  isEditing,
  initialData,
  onSuccess,
}) => {
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>();

  // Pre-fill form when editing
  useEffect(() => {
    if (isEditing && initialData) {
      setValue("machine_id", initialData.machine_id);
      setValue("reason", initialData.reason);
      setValue("start_time", initialData.start_time.slice(0, 16)); // Truncate ISO
      setValue("end_time", initialData.end_time.slice(0, 16));
    } else {
      reset();
    }
  }, [isEditing, initialData, setValue, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      const convertedData = {
        ...data,
        start_time: convertIstToUtcIso(data.start_time),
        end_time: convertIstToUtcIso(data.end_time),
      };

      if (isEditing && initialData) {
        await updateDowntimeEvent(initialData.id, convertedData);
        toast.success("Downtime event updated");
      } else {
        await createDowntimeEvent(convertedData);
        toast.success("Downtime event created");
      }

      onSuccess();
      reset();
      onClose();
    } catch (error) {
      console.error("Failed to save downtime event:", error);
      toast.error("Failed to save downtime event");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">
          {isEditing ? "Edit Downtime Event" : "Add Downtime Event"}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Machine */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Machine</label>
            <select
              {...register("machine_id", { required: "Machine is required" })}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">Select a machine</option>
              {machines.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            {errors.machine_id && (
              <p className="text-red-600 text-sm">{errors.machine_id.message}</p>
            )}
          </div>

          {/* Reason */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Reason</label>
            <input
              type="text"
              {...register("reason", { required: "Reason is required" })}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
            {errors.reason && (
              <p className="text-red-600 text-sm">{errors.reason.message}</p>
            )}
          </div>

          {/* Start Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Start Time</label>
            <input
              type="datetime-local"
              {...register("start_time", { required: "Start time is required" })}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
            {errors.start_time && (
              <p className="text-red-600 text-sm">{errors.start_time.message}</p>
            )}
          </div>

          {/* End Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700">End Time</label>
            <input
              type="datetime-local"
              {...register("end_time", { required: "End time is required" })}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
            {errors.end_time && (
              <p className="text-red-600 text-sm">{errors.end_time.message}</p>
            )}
          </div>

          {/* Buttons */}
          <div className="flex justify-end space-x-4 pt-2">
            <button
              type="button"
              onClick={() => {
                reset();
                onClose();
              }}
              className="px-4 py-2 rounded text-sm bg-gray-100 hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded text-sm bg-blue-600 text-white hover:bg-blue-700"
            >
              {isSubmitting
                ? isEditing
                  ? "Updating..."
                  : "Saving..."
                : isEditing
                ? "Update Event"
                : "Add Event"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddDowntimeEventsModal;