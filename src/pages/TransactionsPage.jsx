import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import api from "../lib/api";
import { 
  TrendingUp, 
  Search, 
  CheckCircle, 
  XCircle, 
  Clock, 
  DollarSign,
  FileDown,
  AlertTriangle,
  User,
  MapPin,
  FileText
} from "lucide-react";

export default function TransactionsPage() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      
      const data = await api.getAllTransactions({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchTerm || undefined
      });
      
      setTransactions(data);
    } catch (error) {
      console.error("Error fetching transactions:", error);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [statusFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm !== undefined) {
        fetchTransactions();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleApprove = async (transactionId) => {
    if (!confirm("Are you sure you want to approve this transaction?")) return;
    
    try {
      
      const landOfficers = await api.getUsers({ role: 'land_officer' });
      
      if (!landOfficers || landOfficers.length === 0) {
        alert("No land officer available to assign to this transaction.");
        return;
      }

      const landOfficer = landOfficers[0];

      const approvalData = {
        status: 'approved',
        legal_notes: 'Transaction approved by legal officer',
        land_officer_id: landOfficer.id
      };
      
      
      await api.approveTransaction(transactionId, approvalData);
      
      alert("✅ Transaction approved successfully!");
      fetchTransactions();
    } catch (error) {
      console.error(" Error approving transaction:", error);
      alert(` Failed to approve transaction: ${error.message}`);
    }
  };

  const handleReject = async (transactionId) => {
    const reason = prompt("Please enter reason for rejection:");
    if (!reason) return;
    
    try {
      
      await api.rejectTransaction(transactionId, reason);
      
      alert("✅ Transaction rejected!");
      fetchTransactions();
    } catch (error) {
      console.error(" Error rejecting transaction:", error);
      alert(` Failed to reject transaction: ${error.message}`);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const downloadParams = {};
      
      if (user?.role === 'admin') {
        downloadParams.county = 'all';
      }
      
      if (statusFilter !== 'all') {
        downloadParams.status = statusFilter;
      }
      
      if (searchTerm) {
        downloadParams.searchTerm = searchTerm;
      }
      
      downloadParams.period = 'all_time';
      
      await api.downloadTransactionReport(downloadParams);
    } catch (error) {
      console.error("Failed to download report:", error);
      alert("Failed to download transaction report.");
    }
  };
  
  const getStatusBadge = (transaction) => {
    if (transaction.transaction_payment_status === 'failed') {
      return { color: "bg-red-100 text-red-700", label: "Payment Failed", icon: XCircle };
    } else if (transaction.transaction_payment_status === 'pending') {
      return { color: "bg-amber-100 text-amber-700", label: "Awaiting Payment", icon: Clock };
    }
    
    if (transaction.transaction_legal_approval_status === 'approved') {
      return { color: "bg-green-100 text-green-700", label: "Completed", icon: CheckCircle };
    } else if (transaction.transaction_legal_approval_status === 'pending') {
      return { color: "bg-blue-100 text-blue-700", label: "Processing", icon: Clock };
    } else if (transaction.transaction_legal_approval_status === 'rejected') {
      return { color: "bg-red-100 text-red-700", label: "Rejected", icon: XCircle };
    }
    
    return { color: "bg-slate-100 text-slate-700", label: "Unknown", icon: Clock };
  };
  
  const filteredTransactions = transactions.map((transaction) => {
    const mappedTransaction = {
      id: transaction.transaction_id || transaction.Transaction_id || transaction.id,
      transaction_id: transaction.transaction_id || transaction.Transaction_id || transaction.id,
      land_record: {
        land_records_parcel_number:
          transaction.land_record?.land_records_parcel_number ||
          transaction.transaction_land_record_id?.land_records_parcel_number ||
          "N/A",
        land_records_deed_number:
          transaction.land_record?.land_records_deed_number ||
          transaction.transaction_land_record_id?.land_records_deed_number ||
          "N/A",
        land_records_location:
          transaction.land_record?.land_records_location ||
          transaction.transaction_land_record_id?.land_records_location ||
          "N/A",
        land_records_county:
          transaction.land_record?.land_records_county ||
          transaction.transaction_land_record_id?.land_records_county ||
          "N/A",
      },
      from_owner: {
        user_full_name:
          transaction.from_owner?.user_full_name ||
          transaction.transaction_from_owner_id?.user_full_name ||
          "N/A",
      },
      to_owner: {
        user_full_name:
          transaction.to_owner?.user_full_name ||
          transaction.transaction_to_owner_id?.user_full_name ||
          "N/A",
      },
      transaction_type: transaction.transaction_type,
      transaction_amount: transaction.transaction_amount,
      transaction_legal_approval_status: transaction.transaction_legal_approval_status,
      transaction_payment_status: transaction.transaction_payment_status,
      transaction_payment_reference: transaction.transaction_payment_reference,
      transaction_created_at: transaction.transaction_created_at,
      transaction_county: transaction.transaction_county,
      transfer_accepted: transaction.transfer_accepted,
      transfer_rejected: transaction.transfer_rejected,
      legal_officer_commission: transaction.legal_officer_commission,
      land_officer_commission: transaction.land_officer_commission,
      transaction_legal_officer_share: transaction.transaction_legal_officer_share,
      transaction_land_officer_share: transaction.transaction_land_officer_share,
      transaction_legal_officer_id: transaction.transaction_legal_officer_id,
      transaction_land_officer_id: transaction.transaction_land_officer_id,
    };

    return mappedTransaction;
  }).filter(transaction => {
    const matchesSearch = 
      transaction.land_record.land_records_parcel_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.land_record.land_records_deed_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.from_owner.user_full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.to_owner.user_full_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === "all" || transaction.transaction_legal_approval_status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const canApproveLegal = user?.role === "legal_officer";
  const canApproveLand = user?.role === "land_officer";
  const canDownloadLedger = user?.role === "admin" || user?.role === "land_officer" || user?.role === "legal_officer" || user?.role === "user";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
          Transactions
        </h1>
        
        {canDownloadLedger && (
          <button
            onClick={handleDownloadReport}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <FileDown className="w-5 h-5" />
            Download Report
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative w-full md:w-1/3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by parcel, deed, or owner..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full py-2 pl-10 pr-4 border border-slate-300 rounded-lg focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Transaction ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Property</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Transfer Details</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Amount & Fees</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-200">
              {filteredTransactions.map((transaction) => {
                const statusBadge = getStatusBadge(transaction);
                const StatusIcon = statusBadge.icon;

                return (
                  <tr key={transaction.transaction_id || transaction.id} className="hover:bg-slate-50">
                    
                    {/* Transaction ID */}
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 flex items-center gap-1">
                        {transaction.transaction_id}
                      </p>
                    </td>

                    {/* Property */}
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-slate-800 flex items-center gap-1">
                          {transaction.land_record.land_records_parcel_number}
                        </p>
                        <p className="text-sm text-slate-600">{transaction.land_record.land_records_deed_number}</p>
                        <p className="text-xs text-slate-500">{transaction.land_record.land_records_location}</p>
                      </div>
                    </td>

                    {/* Transfer Details / Type */}
                    <td className="px-4 py-3">
                      {transaction.transaction_type === 'verification' ? (
                        <div className="space-y-1">
                          <div className="flex items-center gap-1">
                            <span className="text-sm font-medium text-black-700">
                              Document Verification
                            </span>
                          </div>
                          <p className="text-xs text-slate-500">
                            Paid by: {transaction.from_owner.user_full_name}
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <div className="flex items-center gap-1">
                            <span className="text-sm">
                              <strong>From:</strong> {transaction.from_owner.user_full_name}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-sm">
                              <strong>To:</strong> {transaction.to_owner.user_full_name}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 capitalize">
                            Type: {transaction.transaction_type}
                          </p>
                        </div>
                      )}
                    </td>

                    {/* Amount & Fees */}
                    <td className="px-4 py-3">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-slate-800">
                          KES {transaction.transaction_amount?.toLocaleString() || "0"}
                        </p>
                        {transaction.transaction_type === 'verification' ? (
                          <div className="text-xs">
                            <p className="text-slate-600 font-medium">
                              Document Verification Fee
                            </p>
                            <p className="text-slate-500">
                              (Admin Revenue)
                            </p>
                          </div>
                        ) : (
                          <div className="text-xs space-y-0.5">
                            <p className="text-slate-600">
                              Legal Fee: KES {transaction.transaction_legal_officer_share?.toLocaleString() || "350"}
                            </p>
                            <p className="text-slate-600">
                              Land Fee: KES {transaction.transaction_land_officer_share?.toLocaleString() || "650"}
                            </p>
                          </div>
                        )}
                        <p className="text-xs text-slate-500 mt-1">
                          Ref: {transaction.transaction_payment_reference || 'N/A'}
                        </p>
                        {transaction.transaction_payment_status === 'completed' && (
                          <p className="text-xs text-green-600 font-semibold">
                            ✓ Paid
                          </p>
                        )}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}
                      >
                        <StatusIcon className="w-3 h-3" />
                        {statusBadge.label}
                      </span>
                    </td>

                    {/* Date */}
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {new Date(transaction.transaction_created_at).toLocaleDateString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredTransactions.length === 0 && (
            <div className="text-center py-12">
              <TrendingUp className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">No transactions found</p>
              <p className="text-sm text-slate-500 mt-1">
                {searchTerm || statusFilter !== "all"
                  ? "Try adjusting your search or filters"
                  : "All transactions will appear here"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}