import React, { useState } from "react";
import { importDowntimeEvents } from "../api/downtimeEventsApi";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

const ImportDowntimeEventsModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await importDowntimeEvents(file);
      onSuccess();
      onClose();
      setFile(null); // Reset input
    } catch (err: any) {
      const message =
        err.response?.data?.detail || "Failed to import downtime events. Please check file format and content.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Import Downtime Events</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select File</label>
            <input
              type="file"
              accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex justify-end space-x-4 pt-2">
            <button
              type="button"
              onClick={() => {
                setFile(null);
                setError(null);
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
              {isSubmitting ? "Importing..." : "Import"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ImportDowntimeEventsModal;