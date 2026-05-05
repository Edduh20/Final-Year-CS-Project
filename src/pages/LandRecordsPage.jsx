import { useEffect, useState } from "react";
import { toast } from "react-hot-toast";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { apiClient } from "../lib/api";
import { useSearchParams } from "react-router-dom";
import {
  MapPin,
  Search,
  Plus,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  X,
  Edit,
  Download,
  FileText,
  Send,
} from "lucide-react";

import TransferModal from './TransferModal';

const API_BASE_URL = "http://127.0.0.1:8000/api";

// --- EDIT LAND RECORD MODAL ---
const EditLandRecordModal = ({
  record,
  onClose,
  onRecordUpdated,
}) => {
  const [formData, setFormData] = useState({
    parcel_number: record.parcel_number,
    deed_number: record.deed_number,
    owner_id: record.owner?.id || "",
    location: record.location,
    size_hectares: (record.size_hectares || "").toString(),
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const { parcel_number, deed_number, owner_id, location, size_hectares } =
      formData;
    if (!parcel_number || !deed_number || !owner_id || !location || !size_hectares) {
      setError("Please fill in all required fields.");
      return;
    }

    const sizeValue = parseFloat(size_hectares);
    if (isNaN(sizeValue) || sizeValue <= 0) {
      setError("Size in hectares must be a valid positive number.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        parcel_number,
        deed_number,
        owner_id,
        location,
        size_hectares: sizeValue,
      };
      await api.updateLandRecord(record.id, payload);

      setSuccess("✅ Land record successfully updated!");
      onRecordUpdated();
      setTimeout(() => onClose(), 1000);
    } catch (err) {
      console.error("Update error:", err);
      setError("Failed to update land record. Please check your data and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg">
        <div className="flex justify-between items-center p-6 border-b border-slate-200">
          <h2 className="text-2xl font-bold text-slate-800">Edit Land Record</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg">
              {success}
            </div>
          )}

          {["parcel_number", "deed_number", "owner_id", "location", "size_hectares"].map(
            (field) => (
              <div key={field}>
                <label
                  htmlFor={field}
                  className="block text-sm font-medium text-slate-700 mb-1 capitalize"
                >
                  {field.replace("_", " ")}
                </label>
                <input
                  type={field === "size_hectares" ? "number" : "text"}
                  name={field}
                  id={field}
                  value={formData[field]}
                  onChange={handleChange}
                  required
                  step={field === "size_hectares" ? "0.01" : undefined}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>
            )
          )}

          <div className="pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-2 rounded-lg font-semibold text-white transition-colors flex items-center gap-2 ${
                loading
                  ? "bg-emerald-400 cursor-not-allowed"
                  : "bg-emerald-600 hover:bg-emerald-700"
              }`}
            >
              {loading ? "Updating..." : "Update Record"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};


const AddLandRecordModal = ({ onClose, onRecordAdded }) => {
  const [mode, setMode] = useState("manual");
  const [formData, setFormData] = useState({
    parcel_number: "",
    deed_number: "",
    owner_input: "",
    location: "",
    county: "",
    size_hectares: "",
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === "manual") {
        const { parcel_number, deed_number, owner_input, location, county, size_hectares } = formData;

        if (!parcel_number?.trim() || !deed_number?.trim() || !location?.trim() || !size_hectares) {
          setError("Please fill in parcel number, deed number, location and size.");
          setLoading(false);
          return;
        }

        const sizeValue = parseFloat(size_hectares);
        if (isNaN(sizeValue) || sizeValue <= 0) {
          setError("Size must be a positive number.");
          setLoading(false);
          return;
        }

        const payload = {
          parcel_number: parcel_number.trim(),
          deed_number: deed_number.trim(),
          location: location.trim(),
          county: county?.trim() || "".toLowerCase(),
          size_hectares: sizeValue,
        };

        if (owner_input?.trim()) {
          const ownerValue = owner_input.trim();
          const isUUID = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/i.test(ownerValue);
          if (isUUID) {
            payload.owner_id = ownerValue;
          } else {
            payload.id_number = ownerValue;
          }
        }

        await api.createLandRecord(payload);

        toast.success("✅ Land record added successfully!");

        onRecordAdded();
        onClose();

      } else {
        if (!file) {
          setError("Please select a file to upload.");
          setLoading(false);
          return;
        }

        const formDataObj = new FormData();
        formDataObj.append("file", file);

        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/land-records/bulk-upload/`, {
          method: "POST",
          headers: {
            'Authorization': `Bearer ${api.getAccessToken()}`,
          },
          body: formDataObj,
        });

        if (!response.ok) {
          let errorMessage = "Upload failed";
          try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorData.message || errorMessage;
          } catch {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          }
          throw new Error(errorMessage);
        }

        const result = await response.json();

        toast.success(result.message || "📄 Land records uploaded successfully!");
        onRecordAdded();
        onClose();
      }
    } catch (err) {
      console.error("Add record error:", err);
      const errorMessage = err.message || "Failed to add land record.";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-slate-200 sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-slate-800">Add Land Record</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex gap-3">
            <button
              type="button"
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                mode === "manual"
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              onClick={() => setMode("manual")}
            >
              Manual Entry
            </button>
            <button
              type="button"
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                mode === "file"
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              onClick={() => setMode("file")}
            >
              CSV / Excel Upload
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "manual" ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Parcel Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="parcel_number"
                    value={formData.parcel_number}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="e.g., LR/123/456"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Deed Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="deed_number"
                    value={formData.deed_number}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="e.g., DEED/LR/NAIROBI/123/1"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Owner's ID Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="owner_input"
                    value={formData.owner_input}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="ID Number"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Location <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="e.g., Westlands, Nairobi"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    County
                  </label>
                  <input
                    name="county"
                    value={formData.county}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="e.g., Nairobi"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Size (Hectares) <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="size_hectares"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={formData.size_hectares}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                    placeholder="e.g., 2.5"
                    required
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Upload CSV / Excel
                </label>
                <input
                  type="file"
                  accept=".csv,.xls,.xlsx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  required
                />
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-800 font-medium mb-1">Required Columns:</p>
                  <p className="text-xs text-blue-700">
                    parcel_number, deed_number, id_number, location, county, size_hectares
                  </p>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-6 py-2 rounded-lg font-semibold text-white transition-colors ${
                  loading
                    ? "bg-emerald-400 cursor-not-allowed"
                    : "bg-emerald-600 hover:bg-emerald-700"
                }`}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                    {mode === "manual" ? "Creating..." : "Uploading..."}
                  </span>
                ) : (
                  mode === "manual" ? "Create Record" : "Upload File"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
// --- RECORD DETAIL MODAL ---
const RecordDetailModal = ({
  record,
  onClose,
  onStatusUpdated,
  onEditRecord,
  onRequestTransfer,
  onOpenHistory, // <--- new prop to open history modal in parent
}) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [downloadingDeed, setDownloadingDeed] = useState(false);

  const handleStatusChange = async (status) => {
    setLoading(true);
    setError(null);

    try {
      await api.updateLandRecordStatus(record.id, status);
      toast.success(`Land record marked as ${status}!`);

      onClose();

      setTimeout(() => {
        onStatusUpdated(record.id, status);
      }, 500);
    } catch (err) {
      console.error("Failed to update record status:", err);
      setError(err.message || "Failed to update record status");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDeed = async () => {
    setDownloadingDeed(true);
    try {
      const blob = await api.downloadDeed(record.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `deed_${record.parcel_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Deed for parcel ${record.parcel_number} downloaded successfully!`);
    } catch (err) {
      console.error("Failed to download deed:", err);
      setError(err.message || "Failed to download deed");
      toast.error("Failed to download deed");
    } finally {
      setDownloadingDeed(false);
    }
  };

  const canEdit = user?.role === ""; 
  const canChangeStatus = user?.role === "land_officer";
  const canDownloadDeed = (user?.role === "user" || user?.role === "land_officer") && record.status === "verified";
  const canRequestTransfer = user?.role === "user" && record.owner?.email === user?.email && record.status === "verified";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg shadow-xl">
        <div className="flex justify-between items-center border-b pb-3 mb-4">
          <h2 className="text-xl font-bold text-slate-800">Land Record Details</h2>
          <button onClick={onClose}>
            <X className="w-6 h-6 text-slate-500" />
          </button>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-600">Parcel Number</p>
              <p className="font-semibold">{record.parcel_number}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Deed Number</p>
              <p className="font-semibold break-words whitespace-normal">
                {record.deed_number || record.deedNumber || record.current_deed_number || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Owner</p>
              <p className="font-semibold">{record.owner?.full_name || "Unknown"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Owner ID</p>
              <p className="font-semibold">{record.owner?.id_number || record.owner?.user_id_number || record.owner?.id || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Location</p>
              <p className="font-semibold">{record.location}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Size</p>
              <p className="font-semibold">{record.size_hectares} Ha</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Status</p>
              <p className="font-semibold capitalize">{record.status}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Registered</p>
              <p className="font-semibold">{new Date(record.created_at || record.createdAt || Date.now()).toLocaleString()}</p>
            </div>
          </div>

          {record.has_legal_case && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm font-semibold text-red-800">Legal Case Active</p>
              <p className="text-sm text-red-700 mt-1">
                {record.legal_case_description || "This property has an active legal case."}
              </p>
            </div>
          )}
        </div>

        {error && <p className="text-red-500 mt-2">{error}</p>}

        <div className="flex flex-wrap justify-end gap-3 mt-6">
          {canDownloadDeed && (
            <button
              onClick={handleDownloadDeed}
              disabled={downloadingDeed}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              <FileText className="w-4 h-4" />
              {downloadingDeed ? "Downloading..." : "Download Deed"}
            </button>
          )}

          {canRequestTransfer && (
            <button
              onClick={() => onRequestTransfer(record)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Send className="w-4 h-4" />
              Request Transfer
            </button>
          )}

          <button
            onClick={() => onOpenHistory && onOpenHistory(record)}
            className="px-4 py-2 rounded-lg text-white font-semibold bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 transition-all shadow"
          >
            Ownership History
          </button>

          {canEdit && (
            <button
              onClick={() => onEditRecord(record)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
            >
              Edit Details
            </button>
          )}

          {canChangeStatus && (
            <>
              <button
                onClick={() => handleStatusChange("verified")}
                disabled={loading}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Verify
              </button>
              <button
                onClick={() => handleStatusChange("flagged")}
                disabled={loading}
                className="bg-amber-500 text-white px-4 py-2 rounded-lg hover:bg-amber-600 disabled:opacity-50"
              >
                Flag
              </button>
              <button
                onClick={() => handleStatusChange("rejected")}
                disabled={loading}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Reject
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// --- MAIN PAGE COMPONENT ---
export default function LandRecordsPage() {
  const { user } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [editingRecord, setEditingRecord] = useState(null);
  const [transferRecord, setTransferRecord] = useState(null);
  const [searchParams] = useSearchParams();
  const [downloadingReport, setDownloadingReport] = useState(false);

  const [showAddModal, setShowAddModal] = useState(false);

  // === Ownership history states ===
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [ownershipHistory, setOwnershipHistory] = useState([]);
  const [historyRecord, setHistoryRecord] = useState(null); // the record whose history we're viewing

  const isFlaggedView = searchParams.get('filter') === 'flagged';

  useEffect(() => {
    if (isFlaggedView) {
      setStatusFilter('flagged');
    }
  }, [isFlaggedView]);

  const fetchRecords = async () => {
    try {
      setLoading(true);

      const recordsArray = await api.getAllLandRecords();

      let filteredRecords = recordsArray;

      if (user?.role === 'user') {
        filteredRecords = recordsArray.filter(record =>
          record.owner?.email === user?.email
        );
      } else if (user?.role === 'legal_officer' && isFlaggedView) {
        filteredRecords = recordsArray.filter(record =>
          record.status === 'flagged' || record.has_legal_case
        );
      }

      setRecords(filteredRecords);

    } catch (error) {
      console.error("Error fetching records:", error);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchRecords();
  }, [user, isFlaggedView]);

  const handleStatusUpdated = async (id, newStatus) => {
    await fetchRecords();
    setRecords((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: newStatus } : r))
    );
  };

  const handleDownloadReport = async () => {
    try {
      setDownloadingReport(true);

      await api.getLandRecords();

      await api.downloadLandRecordsReport({
        searchTerm: searchTerm,
        status: statusFilter !== 'all' ? statusFilter : undefined
      });

      toast.success("Land records report downloaded successfully!");
    } catch (error) {
      console.error("Download failed:", error);

      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          toast.error("Authentication failed. Please log in again.");
        } else {
          toast.error(`Could not download report: ${error.message}`);
        }
      } else {
        toast.error("Could not download report");
      }
    } finally {
      setDownloadingReport(false);
    }
  };

  const handleRequestTransfer = async (record) => {
    setTransferRecord(record);
  };

  const handleTransferRequested = () => {
    fetchRecords();
    toast.success("Transfer initiated successfully! The new owner will receive an email to accept.");
  };

  const handleDownloadDeed = async (recordId, parcelNumber) => {
    try {
      const blob = await api.downloadDeed(recordId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `deed_${parcelNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Deed for parcel ${parcelNumber} downloaded successfully!`);
    } catch (err) {
      console.error("Failed to download deed:", err);
      toast.error("Failed to download deed");
    }
  };

  // === Ownership history fetcher ===
  const fetchOwnershipHistory = async (landId) => {
    setHistoryLoading(true);
    setOwnershipHistory([]);
    setHistoryRecord(null);

    try {
      const res = await apiClient.request(`/land-records/${landId}/ownership-history/`);

      // if res is a fetch Response, parse it; otherwise accept parsed object/array
      let data;
      if (res && typeof res.json === "function") {
        // try parse, but guard against HTML error pages
        const text = await res.text();
        try {
          data = JSON.parse(text);
        } catch (e) {
          // if it's HTML or unexpected, throw a friendly error
          throw new Error("Invalid JSON from ownership history endpoint. Check backend.");
        }
      } else {
        data = res;
      }

      // Normalize many possible response shapes:
      let items = [];
      if (Array.isArray(data)) {
        items = data;
      } else if (data && Array.isArray(data.results)) {
        items = data.results;
      } else if (data && Array.isArray(data.history)) {
        items = data.history;
      } else if (data && data.items && Array.isArray(data.items)) {
        items = data.items;
      } else if (data && typeof data === "object" && Object.keys(data).length === 0) {
        items = [];
      } else if (data && typeof data === "object") {
        // If backend returned a single history object
        items = [data];
      } else {
        items = [];
      }

      setOwnershipHistory(items);
      setHistoryRecord(landId);
      setHistoryModalOpen(true);
    } catch (err) {
      console.error("Failed to fetch ownership history:", err);
      toast.error("Failed to load ownership history");
      setOwnershipHistory([]);
      setHistoryRecord(landId);
      setHistoryModalOpen(true);
    } finally {
      setHistoryLoading(false);
    }
  };

  const filteredRecords = records.filter((record) => {
    const matchesSearch =
      record.parcel_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.deed_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.owner?.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || record.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status) => {
    const badges = {
      verified: { icon: CheckCircle, color: "bg-green-100 text-green-700", label: "Verified" },
      pending: { icon: Clock, color: "bg-amber-100 text-amber-700", label: "Pending" },
      flagged: { icon: AlertTriangle, color: "bg-red-100 text-red-700", label: "Flagged" },
      rejected: { icon: XCircle, color: "bg-slate-100 text-slate-700", label: "Rejected" },
    };
    return badges[status] || badges.pending;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  const canEditRecords = user?.role === "land_officer";
  const canDownloadDeed = (user?.role === "user" || user?.role === "land_officer");
  const canRequestTransfer = user?.role === "user";

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-slate-800 mb-6 flex items-center gap-3">
        {isFlaggedView ? "Flagged Land Records" : "Official Land Records"}
      </h1>

      {/* --- Filters --- */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div className="relative w-full md:w-1/3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Parcel No., Deed No., or Owner"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full py-2 pl-10 pr-4 border border-slate-300 rounded-lg focus:ring-emerald-500"
          />
        </div>

        <div className="flex gap-4 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="py-2 px-4 border border-slate-300 rounded-lg focus:ring-emerald-500 bg-white text-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="verified">Verified</option>
            <option value="pending">Pending</option>
            <option value="flagged">Flagged</option>
            <option value="rejected">Rejected</option>
          </select>

          <button
            onClick={handleDownloadReport}
            disabled={downloadingReport || filteredRecords.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Download className="w-4 h-4" />
            {downloadingReport ? "Generating..." : "Download Report"}
          </button>

          {user?.role === "admin" && (
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Record
            </button>
          )}
        </div>
      </div>

      {/* --- TABLE --- */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                {["Parcel No.", "Deed No.", "Owner", "Location", "Size (Ha)", "Status", "Actions"].map(
                  (header) => (
                    <th
                      key={header}
                      className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider"
                    >
                      {header}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {filteredRecords.map((record) => {
                const statusBadge = getStatusBadge(record.status);
                const StatusIcon = statusBadge.icon;
                const isOwnedByUser = user?.role === 'user' && record.owner?.email === user?.email;
                const canTransfer = isOwnedByUser && record.status === 'verified';
                const canDownloadDeedForRecord = canDownloadDeed && record.status === "verified";

                return (
                  <tr key={record.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">
                      {record.parcel_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{record.deed_number || record.deedNumber || record.current_deed_number || "N/A"}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {record.owner?.full_name || "Unknown"}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{record.location}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {record.size_hectares}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}
                      >
                        <StatusIcon className="w-3 h-3" />
                        {statusBadge.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-3 items-center">
                        <button
                          onClick={() => setSelectedRecord(record)}
                          className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                        >
                          View Details
                        </button>

                        {canDownloadDeedForRecord && (
                          <button
                            onClick={() => handleDownloadDeed(record.id, record.parcel_number)}
                            className="flex items-center gap-1 text-sm font-semibold text-indigo-600 hover:text-indigo-700"
                          >
                            <FileText className="w-4 h-4" />
                            Download Deed
                          </button>
                        )}

                        {canTransfer && (
                          <button
                            onClick={() => handleRequestTransfer(record)}
                            className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 font-medium"
                          >
                            <Send className="w-4 h-4" />
                            Transfer
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredRecords.length === 0 && (
            <div className="text-center py-12">
              <MapPin className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No land records found</p>
            </div>
          )}
        </div>
      </div>

      {/* --- MODALS --- */}
      {selectedRecord && (
        <RecordDetailModal
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          onStatusUpdated={handleStatusUpdated}
          onEditRecord={setEditingRecord}
          onRequestTransfer={handleRequestTransfer}
          onOpenHistory={(rec) => fetchOwnershipHistory(rec.id)} // pass handler to open history
        />
      )}

      {editingRecord && (
        <EditLandRecordModal
          record={editingRecord}
          onClose={() => setEditingRecord(null)}
          onRecordUpdated={fetchRecords}
        />
      )}

      {transferRecord && (
        <TransferModal
          landRecord={transferRecord}
          onClose={() => setTransferRecord(null)}
          onSuccess={handleTransferRequested}
        />
      )}

      {showAddModal && user?.role === "admin" && (
        <AddLandRecordModal
          onClose={() => setShowAddModal(false)}
          onRecordAdded={fetchRecords}
        />
      )}

      {/* === Ownership History Modal (inserted here as requested) === */}
      {historyModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Ownership History</h2>
              <button
                onClick={() => {
                  setHistoryModalOpen(false);
                  setOwnershipHistory([]);
                  setHistoryRecord(null);
                }}
                className="text-gray-600 text-lg"
              >
                ✕
              </button>
            </div>

            {historyLoading && <p>Loading ownership history...</p>}

            {!historyLoading && (!ownershipHistory || ownershipHistory.length === 0) && (
              <p>No ownership history available for this parcel.</p>
            )}

            {!historyLoading && ownershipHistory && ownershipHistory.length > 0 && (
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {ownershipHistory.map((item, idx) => {
                  const prevObj = item.previous_owner || item.history_previous_owner || item.history_previous_owner || item.transferred_from || item.previousOwner;
                  const newObj = item.new_owner || item.history_new_owner || item.transferred_to || item.newOwner;

                  const prevName =
                    (prevObj && (prevObj.full_name || prevObj.name)) ||
                    item.previous_owner_name ||
                    item.history_previous_owner_name ||
                    item.previous_owner?.full_name ||
                    "—";

                  const prevId =
                    (prevObj && (prevObj.id_number || prevObj.user_id_number || prevObj.id)) ||
                    item.previous_owner_id ||
                    item.history_previous_owner_id ||
                    item.previous_owner?.id_number ||
                    "—";

                  const newName =
                    (newObj && (newObj.full_name || newObj.name)) ||
                    item.new_owner_name ||
                    item.history_new_owner_name ||
                    item.new_owner?.full_name ||
                    "—";

                  const newId =
                    (newObj && (newObj.id_number || newObj.user_id_number || newObj.id)) ||
                    item.new_owner_id ||
                    item.history_new_owner_id ||
                    item.new_owner?.id_number ||
                    "—";

                  const oldDeed =
                    item.history_deed_number_old || item.deed_old || item.old_deed_number || item.oldDeedNumber || "N/A";
                  const newDeed =
                    item.history_deed_number_new || item.deed_new || item.new_deed_number || item.newDeedNumber || "N/A";

                  const parcel =
                    (item.history_land_record && (item.history_land_record.land_records_parcel_number || item.history_land_record.parcel_number)) ||
                    item.parcel_number ||
                    item.history_parcel_number ||
                    "—";

                  const transferType =
                    item.history_transfer_type || item.transfer_type || item.type || "—";

                  const transferDate =
                    item.history_transfer_date || item.transfer_date || item.transferDate || item.created_at || item.createdAt || null;

                  const notes =
                    item.history_notes || item.notes || item.note || "None";

                  return (
                    <div key={item.history_id || item.id || idx} className="p-3 border rounded-md">
                      <p className="font-semibold text-slate-700">
                        {prevName} (ID: {prevId}) → {newName} (ID: {newId})
                      </p>

                      <p className="text-sm text-gray-700 font-medium mt-1">
                        Parcel: {parcel}
                      </p>

                      <div className="mt-2 text-xs text-gray-600">
                        <p>Old Deed: {oldDeed}</p>
                        <p>New Deed: {newDeed}</p>
                        <p>Transfer Type: {transferType}</p>
                        <p>Notes: {notes}</p>
                        <p>Transfer Date: {transferDate ? new Date(transferDate).toLocaleString() : "Unknown"}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
