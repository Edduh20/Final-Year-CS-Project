import { useState } from "react";
import api from "../lib/api";
import { Search } from "lucide-react";

export default function SearchLandRecordsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setError("Please enter an ID number or parcel number.");
      return;
    }

    setLoading(true);
    setError("");
    setSearched(true);

    try {
      const response = await api.searchLandRecords(searchTerm);
      setRecords(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error("Error fetching records:", err);
      setError("Failed to search land records. Try again.");
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">
        Search Land Records
      </h1>

      <div className="flex gap-3 mb-8">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter ID number, parcel, or deed number"
          className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <Search className="w-5 h-5" />
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && (
        <div className="p-4 mb-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
          {error}
        </div>
      )}

      {!loading && searched && records.length === 0 && !error && (
        <p className="text-slate-500">No records found. Try another search.</p>
      )}

      {records.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {records.map((record) => (
            <div
              key={record.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"
            >
              <h2 className="text-lg font-semibold text-slate-800 mb-2">
                Parcel: {record.parcel_number}
              </h2>
              <p className="text-sm text-slate-600">
                <strong>Deed:</strong> {record.deed_number}
              </p>
              <p className="text-sm text-slate-600">
                <strong>Owner:</strong> {record.owner?.full_name}
              </p>
              <p className="text-sm text-slate-600">
                <strong>ID Number:</strong> {record.owner?.id_number}
              </p>
              <p className="text-sm text-slate-600">
                <strong>Location:</strong> {record.location}
              </p>
              <p className="text-sm text-slate-600">
                <strong>Status:</strong> {record.status}
              </p>
              <p className="text-sm text-slate-600">
                <strong>Size:</strong> {record.size_hectares} hectares
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
