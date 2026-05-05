import { useEffect, useState, useMemo, useCallback } from "react";
import { FileDown, DollarSign, MapPin, Filter, TrendingUp, Users, Building2 } from "lucide-react";
import { apiClient } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";

// --- CONSTANTS ---
const LEGAL_COMMISSION_DEFAULT = 350;
const LAND_COMMISSION_DEFAULT = 650;

// --- UTILITY FUNCTIONS ---

/**
 * Normalizes the county name, replacing N/A or null with 'Unknown' for display.
 * @param {string} county - The raw county string.
 * @returns {string} - The normalized county name (Title Case, e.g., "Kilifi", "Unknown").
 */
const normalizeCounty = (county) => {
    if (!county || county.toString().toUpperCase() === 'N/A' || county.toString().toLowerCase() === 'processing...') {
        return 'Unknown';
    }

    return county.toString().replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
};

/**
 * Returns a consistent lowercase key for filtering.
 * @param {string} county - The raw county string.
 * @returns {string} - The lowercase key ('kilifi', 'unknown', 'all').
 */
const getCountyKey = (county) => {
    return normalizeCounty(county).toLowerCase();
}


/**
 * Calculates the revenue breakdown for a list of transactions (used for Admin role).
 * @param {Array} transactions - The list of transactions (Verification or Transfer).
 * @param {string} targetCountyKey - The county key ('all' or 'unknown' or lowercase county name) to filter by.
 * @returns {object} - The aggregated revenue breakdown.
 */
const aggregateAdminRevenue = (transactions, targetCountyKey = 'all') => {
  let verificationRevenue = 0;
  let legalCommissions = 0;
  let landCommissions = 0;
  let filteredTransactions = [];

  const isCountyView = targetCountyKey !== 'all';

  transactions.forEach((transaction) => {
    const transactionType = transaction.transaction_type || transaction.type || 'transfer';
    const isVerification = transactionType === 'verification';
    const transactionCountyRaw = transaction.county || transaction.transaction_county;
    
    const transactionCountyKey = getCountyKey(transactionCountyRaw);

    if (isCountyView) {
        if (transactionCountyKey !== targetCountyKey) {
            return; 
        }
    }
  
    filteredTransactions.push(transaction);

    if (isVerification) {
      const amount = parseFloat(transaction.transaction_amount || transaction.amount || 0);
      verificationRevenue += amount;
    } else {
      const legalShare = parseFloat(
        transaction.transaction_legal_officer_share || 
        transaction.legal_officer_commission || 
        LEGAL_COMMISSION_DEFAULT
      );
      const landShare = parseFloat(
        transaction.transaction_land_officer_share || 
        transaction.land_officer_commission || 
        LAND_COMMISSION_DEFAULT
      );
      
      legalCommissions += legalShare;
      landCommissions += landShare;
    }
  });

  const totalOfficerCommissions = legalCommissions + landCommissions;
  const totalRevenue = verificationRevenue + totalOfficerCommissions;

  return {
    total_earnings: totalRevenue,
    verification_revenue: verificationRevenue,
    officer_commissions: totalOfficerCommissions,
    legal_commissions: legalCommissions,
    land_commissions: landCommissions,
    transaction_count: filteredTransactions.length,
    transactions: filteredTransactions,
  };
};


const getOfficerCommissionAmount = (transaction, role) => {
    if (role === "legal_officer") {
      return transaction.legal_officer_commission || 
             transaction.transaction_legal_officer_share || 
             transaction.legal_officer_revenue ||
             transaction.your_commission ||
             LEGAL_COMMISSION_DEFAULT;
    } else if (role === "land_officer") {
      return transaction.land_officer_commission || 
             transaction.transaction_land_officer_share || 
             transaction.land_officer_revenue ||
             transaction.your_commission ||
             LAND_COMMISSION_DEFAULT;
    }
    return 0;
};


// --- REACT COMPONENT ---
export default function RevenuePage() {
  const { user } = useAuth();
  const [allTransactions, setAllTransactions] = useState([]); 
  const [counties, setCounties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [selectedCounty, setSelectedCounty] = useState("all");

  const isOfficer = user?.role === "legal_officer" || user?.role === "land_officer";
  const isAdmin = user?.role === "admin";
  const allowedRole = isOfficer || isAdmin;


  useEffect(() => {
    if (isOfficer && user?.county) {
        setSelectedCounty(getCountyKey(user.county));
    }
  }, [isOfficer, user?.county]);


  useEffect(() => {
    if (!allowedRole) return;

    const initialFetch = async () => {
      try {
        const data = await apiClient.getMyCommissions({ period: filter });
        setAllTransactions(data.commission_transactions || data.transactions || []);
        
        const countiesData = await apiClient.getCounties();
        setCounties(countiesData);
      } catch (error) {
        console.error("Failed to fetch initial data:", error);
        setAllTransactions([]);
        setCounties([]);
      } finally {
        setLoading(false);
      }
    };
    
    initialFetch();
  }, [allowedRole, filter]); 

  const revenueData = useMemo(() => {
    const activeCountyFilterKey = isAdmin ? selectedCounty : getCountyKey(user?.county);

    if (isAdmin) {
      const data = aggregateAdminRevenue(allTransactions, activeCountyFilterKey);
      return { ...data, user_county: activeCountyFilterKey };
      
    } else if (isOfficer) {
      const officerTransactions = allTransactions.filter(transaction => {
        const transactionType = transaction.transaction_type || transaction.type || 'transfer';
        return transactionType !== 'verification'; 
      });

      const totalEarnings = officerTransactions.reduce((total, transaction) => {
          return total + getOfficerCommissionAmount(transaction, user.role);
      }, 0);

      return {
        total_earnings: totalEarnings,
        transaction_count: officerTransactions.length,
        transactions: officerTransactions,
        user_county: activeCountyFilterKey,
        verification_revenue: 0,
        legal_commissions: 0, 
        land_commissions: 0,
      };
    }

    return {
      total_earnings: 0, transaction_count: 0, transactions: [], user_county: null, verification_revenue: 0, officer_commissions: 0, legal_commissions: 0, land_commissions: 0,
    };
  }, [isAdmin, isOfficer, allTransactions, selectedCounty, user]);



  const handleDownloadReport = useCallback(async () => {
    try {
      const downloadParams = {};
      if (isAdmin && selectedCounty !== 'all' && selectedCounty !== 'unknown') {
        downloadParams.county = selectedCounty;
      }
      if (filter !== 'all') {
        downloadParams.period = filter;
      }
      
      await apiClient.downloadRevenueReport(downloadParams);
    } catch (error) {
      console.error("Failed to download revenue report:", error);
      alert("Failed to download revenue report.");
    }
  }, [isAdmin, selectedCounty, filter]);
  

  const getCommissionRate = () => {
    if (user?.role === "legal_officer") return `KES ${LEGAL_COMMISSION_DEFAULT} per transfer`;
    if (user?.role === "land_officer") return `KES ${LAND_COMMISSION_DEFAULT} per transfer`;
    if (user?.role === "admin") return "Verification + Commissions";
    return "N/A";
  };

  const getRoleDisplay = () => {
    if (user?.role === "legal_officer") return "Legal Officer";
    if (user?.role === "land_officer") return "Land Officer";
    if (user?.role === "admin") return "Administrator";
    return "Officer";
  };

  const getCountyDisplayName = () => {
    if (isAdmin) {
        if (selectedCounty === "all") return "All Counties";
        if (selectedCounty === "unknown") return "Unknown County";
        const county = counties.find(c => c.value === selectedCounty);
        return county ? county.label : normalizeCounty(selectedCounty);
    }
    return normalizeCounty(user?.county) || "Your County";
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString('en-KE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };


  if (!allowedRole) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-600">Revenue reports are only available for officers and administrators.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  const renderRevenueRow = (transaction, idx) => {
    const transactionType = transaction.transaction_type || transaction.type || 'transfer';
    const isVerification = transactionType === 'verification';
    
    const parcelNumber = transaction.land_record?.land_records_parcel_number || 
                         transaction.transaction_land_record_id?.land_records_parcel_number ||
                         "Processing...";
    const rawCounty = transaction.county || 
                      transaction.land_record?.land_records_county ||
                      transaction.transaction_county ||
                      null;
    const displayCounty = normalizeCounty(rawCounty);

    return (
      <tr
        key={transaction.id || transaction.transaction_id || idx}
        className="border-b border-slate-100 hover:bg-slate-50 text-sm transition-colors"
      >
        <td className="p-4 text-slate-600">{idx + 1}</td>
        <td className="p-4 font-medium text-slate-800">
          {(transaction.transaction_id || transaction.id)?.slice(0, 8) || "N/A"}...
        </td>
        <td className="p-4">
          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
            isVerification ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
          }`}>
            {transactionType.toUpperCase()}
          </span>
        </td>
        <td className="p-4 text-slate-600">
          <div className="flex items-center gap-2">
            <span className={parcelNumber === "Processing..." ? "text-amber-600" : ""}>
              {parcelNumber}
            </span>
          </div>
        </td>
        <td className="p-4 text-slate-600">
          {displayCounty === "Unknown" ? (
            <span className="text-amber-600">{displayCounty}</span>
          ) : (
            displayCounty
          )}
        </td>
        <td className="p-4 text-slate-700 font-medium">
          KES {(transaction.transaction_amount || transaction.amount)?.toLocaleString() || "0"}
        </td>
        {isAdmin ? (
          <td className="p-4">
            {isVerification ? (
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-blue-600">Verification Fee</span>
                <span className="text-xs text-slate-600">KES {(transaction.transaction_amount || transaction.amount || 0).toLocaleString()}</span>
              </div>
            ) : (
              <div className="text-xs space-y-1">
                <div className="text-amber-600 font-semibold">Legal: KES {(transaction.transaction_legal_officer_share || transaction.legal_officer_commission || LEGAL_COMMISSION_DEFAULT).toLocaleString()}</div>
                <div className="text-blue-600 font-semibold">Land: KES {(transaction.transaction_land_officer_share || transaction.land_officer_commission || LAND_COMMISSION_DEFAULT).toLocaleString()}</div>
              </div>
            )}
          </td>
        ) : (
          <td className="p-4 text-emerald-600 font-semibold">
            KES {getOfficerCommissionAmount(transaction, user.role)?.toLocaleString() || "0"}
          </td>
        )}
        <td className="p-4 text-slate-500">
          {formatDate(transaction.transaction_created_at || transaction.created_at)}
        </td>
        <td className="p-4">
          <span
            className={`px-2 py-1 text-xs font-semibold rounded-full ${
              (transaction.transaction_legal_approval_status === "approved" || 
               transaction.legal_approval_status === "approved" ||
               isVerification)
                ? "bg-emerald-100 text-emerald-700"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            {isVerification ? "COMPLETED" : 
             (transaction.transaction_legal_approval_status || 
              transaction.legal_approval_status || "pending").toUpperCase()}
          </span>
        </td>
      </tr>
    );
  };


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Revenue & Commissions</h1>
          <p className="text-slate-600 mt-1">
            {getRoleDisplay()} - {getCountyDisplayName()}
          </p>
        </div>
        <button
          onClick={handleDownloadReport}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <FileDown className="w-5 h-5" />
          <span>Download Report</span>
        </button>
      </div>

      {/* County and Filter Section */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Admin County Selection */}
          {isAdmin && (
            <div className="flex items-center gap-3">
              <Building2 className="w-5 h-5 text-slate-600" />
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Select County
                </label>
                <select
                  value={selectedCounty}
                  onChange={(e) => setSelectedCounty(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="all">All Counties</option>
                  
                  {/* Unknown County Filter */}
                  <option value="unknown">Unknown County</option> 

                  {counties.map(county => (
                    <option key={county.value} value={getCountyKey(county.value)}>
                      {county.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
          
          {/* Officer County Display */}
          {isOfficer && (
            <div className="flex items-center gap-3">
              <Building2 className="w-5 h-5 text-slate-600" />
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  County Filter 
                </label>
                <input
                    type="text"
                    value={getCountyDisplayName()}
                    readOnly
                    className="w-full px-3 py-2 border border-slate-300 bg-slate-50 rounded-lg text-slate-600"
                />
              </div>
            </div>
          )}

          {/* Period Filter */}
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-slate-600" />
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Filter by period
              </label>
              <div className="flex gap-2">
                {["all", "this_month", "last_month"].map((filterOption) => (
                  <button
                    key={filterOption}
                    onClick={() => setFilter(filterOption)}
                    className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                      filter === filterOption
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {filterOption === "all" && "All Time"}
                    {filterOption === "this_month" && "This Month"}
                    {filterOption === "last_month" && "Last Month"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ADMIN SUMMARY CARDS - Show Breakdown */}
      {isAdmin ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Total Revenue</p>
                <p className="text-2xl font-bold text-slate-800">
                  KES {revenueData.total_earnings?.toLocaleString() || "0"}
                </p>
              </div>
              <div className="p-3 rounded-full bg-emerald-100">
                <DollarSign className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              {revenueData.transaction_count} total transactions
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Verification Fees</p>
                <p className="text-2xl font-bold text-slate-800">
                  KES {revenueData.verification_revenue?.toLocaleString() || "0"}
                </p>  
              </div>
              <div className="p-3 rounded-full bg-red-100">
                <Users className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              Verifications included in current view
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Legal Commissions</p>
                <p className="text-2xl font-bold text-slate-800">
                  KES {revenueData.legal_commissions?.toLocaleString() || "0"}
                </p>
              </div>
              <div className="p-3 rounded-full bg-amber-100">
                <Users className="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              Legal officer earnings (KES {LEGAL_COMMISSION_DEFAULT}/transfer)
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Land Commissions</p>
                <p className="text-2xl font-bold text-slate-800">
                  KES {revenueData.land_commissions?.toLocaleString() || "0"}
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              Land officer earnings (KES {LAND_COMMISSION_DEFAULT}/transfer)
            </p>
          </div>
        </div>
      ) : (
        // Officer Summary Cards 
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Total Earnings</p>
                <p className="text-2xl font-bold text-slate-800">
                  KES {revenueData.total_earnings?.toLocaleString() || "0"}
                </p>
              </div>
              <div className="p-3 rounded-full bg-emerald-100">
                <DollarSign className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              {revenueData.transaction_count} approved transfers in {getCountyDisplayName()}
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">Commission Rate</p>
                <h2 className="text-xl font-bold text-slate-800 mt-2">
                  {getCommissionRate()}
                </h2>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              Fixed amount per transfer
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-600">County & Period</p>
                <h2 className="text-lg font-bold text-slate-800 mt-2">
                  {getCountyDisplayName()}
                </h2>
                <p className="text-sm text-slate-600 mt-1 capitalize">
                  {filter.replace('_', ' ')}
                </p>
              </div>
              <div className="p-3 rounded-full bg-purple-100">
                <MapPin className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-sm text-slate-500 mt-2">
              Showing {revenueData.transaction_count} transactions
            </p>
          </div>
        </div>
      )}

      {/* Revenue Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-800">
                {isAdmin ? "Revenue Details" : "Commission Details"} - {getCountyDisplayName()}
              </h3>
              <p className="text-sm text-slate-600 mt-1">
                {isAdmin
                  ? "Showing all revenue sources (Commissions and Verifications) for the selected county/filter."
                  : `Breakdown of earnings from approved land transfers in ${getCountyDisplayName()}`
                }
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Users className="w-4 h-4" />
              <span>{revenueData.transaction_count} transactions</span>
            </div>
          </div>
        </div>
        
        {revenueData.transactions && revenueData.transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-slate-100 border-b border-slate-200">
                <tr className="text-left text-sm font-medium text-slate-600">
                  <th className="p-4">#</th>
                  <th className="p-4">Transaction ID</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Parcel Number</th>
                  <th className="p-4">County</th>
                  <th className="p-4">Amount</th>
                  {isAdmin && <th className="p-4">Revenue Type</th>}
                  {!isAdmin && <th className="p-4">Your Commission</th>}
                  <th className="p-4">Date</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {revenueData.transactions.map(renderRevenueRow)}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-slate-500 mb-2">No revenue records found</p>
            <p className="text-sm text-slate-400">
              {`No transactions found for ${getCountyDisplayName()} in the selected period.`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}