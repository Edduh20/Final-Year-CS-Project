import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../lib/api";
import {
  MapPin,
  FileCheck,
  AlertTriangle,
  Users,
  TrendingUp,
  Clock,
  CheckCircle,
  Gavel,
  Search,
  Upload,
  FileText,
  User,
  DollarSign,
  UserCog,
  UserPlus,
  ArrowRightCircle,
  X,
  Shield,
  Settings,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalLandRecords: 0,
    verifiedRecords: 0,
    pendingVerifications: 0,
    pendingLegalApprovals: 0,
    flaggedRecords: 0,
    totalUsers: 0,
    recentTransactions: 0,
    totalRevenue: 0,
    userPendingFees: 0,
    countyRevenue: 0,
    userLegalCases: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showProfileEdit, setShowProfileEdit] = useState(false);

  useEffect(() => {
    fetchStats();
  }, [user]);

  const fetchStats = async () => {
    try {
      const data = await apiClient.getDashboardStats();

      const baseStats = {
        totalLandRecords: data.total_land_records || data.totalLandRecords || 0,
        verifiedRecords: data.verified_records || data.verifiedRecords || 0,
        pendingVerifications: data.pending_verifications || data.pendingVerifications || 0,
        pendingLegalApprovals: data.pending_legal_approvals || data.pendingLegalApprovals || 0,
        flaggedRecords: data.flagged_records || data.flaggedRecords || 0,
        totalUsers: data.total_users || data.totalUsers || 0,
        recentTransactions: data.recent_transactions || data.recentTransactions || 0,
        totalRevenue: data.total_revenue || data.totalRevenue || data.countyRevenue || 0,
        userPendingFees: data.user_pending_fees || data.userPendingFees || 0,
        countyRevenue: data.county_revenue || data.countyRevenue || data.total_revenue || data.totalRevenue || 0,
        userLegalCases: data.overall_legal_cases || data.user_legal_cases || 0,
      };

      setStats(baseStats);
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
      setStats({
        totalLandRecords: 0,
        verifiedRecords: 0,
        pendingVerifications: 0,
        pendingLegalApprovals: 0,
        flaggedRecords: 0,
        totalUsers: 0,
        recentTransactions: 0,
        totalRevenue: 0,
        countyRevenue: 0,
        userLegalCases: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const StatCard = ({ icon: Icon, title, value, color, subtitle, onClick }) => (
    <div
      className={`bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow ${
        onClick ? "cursor-pointer hover:border-emerald-300" : ""
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="text-3xl font-bold text-slate-800 mt-2">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  const QuickActionButton = ({ icon: Icon, title, subtitle, color, onClick }) => (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 text-left border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
    >
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="font-medium text-slate-800">{title}</p>
        <p className="text-xs text-slate-500">{subtitle}</p>
      </div>
    </button>
  );

  // Profile Edit Modal Component
  const ProfileEditModal = () => {
    const [formData, setFormData] = useState({
      full_name: user?.full_name || "",
      phone_number: user?.phone_number || "",
      id_number: user?.id_number || "",
      password: "",
    });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e) => {
      e.preventDefault();
      setSubmitting(true);
      setError("");

      try {
        const updateData = {
          full_name: formData.full_name,
          phone_number: formData.phone_number || undefined,
        };
        
        if (formData.password.trim()) {
          updateData.password = formData.password;
        }

        await apiClient.updateCurrentUser(updateData);
        
        setShowProfileEdit(false);
        window.location.reload();
        
      } catch (error) {
        console.error("Profile update failed:", error);
        setError(error.message || "Failed to update profile. Please try again.");
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-2xl max-w-lg w-full shadow-xl border border-slate-200">
          <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-white">
            <h2 className="text-xl font-semibold text-slate-800">Edit Profile</h2>
            <button
              onClick={() => setShowProfileEdit(false)}
              className="text-slate-400 hover:text-slate-600 transition-colors"
              disabled={submitting}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email (read-only)
              </label>
              <input
                type="email"
                disabled
                value={user?.email || ""}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 bg-slate-50 text-slate-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="John Doe"
                disabled={submitting}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="+254..."
                disabled={submitting}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                ID Number (read-only)
              </label>
              <input
                type="text"
                disabled
                value={user?.id_number || ""}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 bg-slate-50 text-slate-500"
                placeholder="12345678"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                New Password (optional)
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="Leave blank to keep current password"
                disabled={submitting}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowProfileEdit(false)}
                disabled={submitting}
                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {submitting ? "Updating..." : "Update Profile"}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // --- ROLE-SPECIFIC DASHBOARD RENDERERS ---

  const renderAdminDashboard = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard
      icon={Users}
      title="Total Users"
      value={stats.totalUsers || 0}
      color="bg-purple-600"
      onClick={() => navigate("/users")}
    />
    <StatCard
      icon={DollarSign}
      title="Total Transfer Revenue"
      value={`KES ${(stats.totalRevenue || 0).toLocaleString()}`}
      color="bg-green-600"
      subtitle="All completed transactions"
      onClick={() => navigate("/revenue")}
    />
    <StatCard
      icon={MapPin}
      title="Total Land Records"
      value={stats.totalLandRecords}
      color="bg-emerald-600"
      onClick={() => navigate("/land-records")}
    />
    <StatCard
      icon={Gavel}
      title="Overall Legal Cases" 
      value={stats.userLegalCases}
      color="bg-red-600"
      subtitle="All active or resolved cases"
      onClick={() => navigate("/legal-cases")}
    />
  </div>
);

  const renderLandOfficerDashboard = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        icon={MapPin}
        title="County Land Records"
        value={stats.totalLandRecords}
        color="bg-emerald-600"
        subtitle={user?.county ? `In ${user.county}` : "Your county"}
        onClick={() => navigate("/land-records")}
      />
      <StatCard
      icon={Gavel}
      title="County Legal Cases"
      value={stats.userLegalCases} 
      color="bg-red-600"
      subtitle={user?.county ? `All in ${user.county}` : "Your county"}
      onClick={() => navigate("/legal-cases")}
    />
      <StatCard
        icon={DollarSign}
        title="County Revenue"
        value={`KES ${(stats.countyRevenue || 0).toLocaleString()}`}
        color="bg-green-600"
        subtitle="Your commission earnings"
        onClick={() => navigate("/revenue")}
      />
      <StatCard
      icon={TrendingUp}
      title="County Transactions"
      value={stats.recentTransactions}
      color="bg-indigo-600"
      subtitle={user?.county ? `In ${user.county}` : "Your county"}
      onClick={() => navigate("/transactions")}
    />
    </div>
  );

  const renderLegalOfficerDashboard = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard
      icon={Gavel}
      title="County Legal Cases" 
      value={stats.userLegalCases}
      color="bg-blue-600"
      subtitle={user?.county ? `All in ${user.county}` : "Your county"}
      onClick={() => navigate("/legal-cases")}
    />
    <StatCard
      icon={AlertTriangle}
      title="Flagged Lands"
      value={stats.flaggedRecords}
      color="bg-red-600"
      subtitle={user?.county ? `In ${user.county}` : "Your county"}
      onClick={() => navigate("/land-records?filter=flagged")}
    />
    <StatCard
      icon={TrendingUp}
      title="County Transactions"
      value={stats.recentTransactions}
      color="bg-indigo-600"
      subtitle={user?.county ? `In ${user.county}` : "Your county"}
      onClick={() => navigate("/transactions")}
    />
    <StatCard
      icon={DollarSign}
      title="County Revenue"
      value={`KES ${(stats.countyRevenue || 0).toLocaleString()}`}
      color="bg-green-600"
      subtitle="Your commission earnings"
      onClick={() => navigate("/revenue")}
    />
  </div>
);

  const renderUserDashboard = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        icon={MapPin}
        title="Your Land Records"
        value={stats.totalLandRecords}
        color="bg-emerald-600"
        onClick={() => navigate("/land-records")}
      />
      <StatCard
        icon={FileCheck}
        title="Pending Verifications"
        value={stats.pendingVerifications}
        color="bg-blue-600"
        onClick={() => navigate("/verification")}
      />
      <StatCard
        icon={DollarSign}
        title="Money Paid"
        value={`KES ${(stats.userMoneyPaid || stats.totalRevenue || 0).toLocaleString()}`}
        color="bg-green-600"
        subtitle="Total money paid"
        onClick={() => navigate("/transactions")}
      />
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-800">
          {getGreeting()}, {user.full_name}
        </h1>
      </div>

      {/* Dynamic Dashboard */}
      {user?.role === "admin" && renderAdminDashboard()}
      {user?.role === "land_officer" && renderLandOfficerDashboard()}
      {user?.role === "legal_officer" && renderLegalOfficerDashboard()}
      {user?.role === "user" && renderUserDashboard()}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">
            Quick Access
          </h3>
          <div className="space-y-3">
            {user?.role === "admin" && (
              <>
                <QuickActionButton
                  icon={UserCog}
                  title="Manage Users"
                  subtitle="View, create, and manage system users."
                  color="text-purple-600"
                  onClick={() => navigate("/users")}
                />
                <QuickActionButton
                  icon={UserPlus}
                  title="Create Officer Account"
                  subtitle="Add Land or Legal Officer"
                  color="text-blue-600"
                  onClick={() => navigate("/users?action=add")}
                />
              </>
            )}

            {user?.role === "user" && (
              <>
                <QuickActionButton
                  icon={FileCheck}
                  title="Upload Document for Verification"
                  subtitle="Submit deed or related documents."
                  color="text-blue-600"
                  onClick={() => navigate("/verification?action=upload")}
                />
                <QuickActionButton
                  icon={Search}
                  title="Search for Lands"
                  subtitle="Find and verify land records"
                  color="text-purple-600"
                  onClick={() => navigate("/search-land")}
                />
                <QuickActionButton
                  icon={Gavel}
                  title="View My Legal Cases"
                  subtitle="Check status of your legal cases"
                  color="text-red-600"
                  onClick={() => navigate("/legal-cases")}
                />
              </>
            )}

            {user?.role === "land_officer" && (
              <>
                <QuickActionButton
                  icon={AlertTriangle}
                  title="View Flagged Lands"
                  subtitle="Inspect disputed or case-bound lands."
                  color="text-red-600"
                  onClick={() => navigate("/land-records")}
                />
                <QuickActionButton
                  icon={Gavel}
                  title="Review Legal Cases"
                  subtitle="Handle legal cases in your county"
                  color="text-red-600"
                  onClick={() => navigate("/legal-cases")}
                />
              </>
            )}

            {user?.role === "legal_officer" && (
              <>
                <QuickActionButton
                  icon={Gavel}
                  title="Submit Cases"
                  subtitle="Submit Land Parcel cases for action."
                  color="text-blue-600"
                  onClick={() => navigate("/legal-cases")}
                />
                <QuickActionButton
                  icon={AlertTriangle}
                  title="View Flagged Lands"
                  subtitle="Inspect disputed or case-bound lands."
                  color="text-red-600"
                  onClick={() => navigate("/land-records")}
                />
              </>
            )}

            <QuickActionButton
              icon={Settings}
              title="Account Settings"
              subtitle="Update your profile and password."
              color="text-slate-600"
              onClick={() => navigate("/settings")}
            />
          </div>
        </div>

        {/* System Overview */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">
            System Overview
          </h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-slate-800">
                  All systems operational
                </p>
                <p className="text-xs text-slate-500">
                  Services running smoothly
                </p>
              </div>
            </div>
            
            {/* Legal Cases Alert for Officers and Admin */}
            {(user?.role === 'admin' || user?.role === 'land_officer' || user?.role === 'legal_officer' ) && stats.flaggedRecords > 0 && (
              <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                <Gavel className="w-5 h-5 text-red-600" />
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Active Legal Cases
                  </p>
                  <p className="text-xs text-slate-500">
                    {stats.flaggedRecords} land record(s) under legal review
                  </p>
                </div>
              </div>
            )}

            {/* General Flagged Lands Alert */}
            {stats.flaggedRecords > 0 && (
              <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Flagged Lands Detected
                  </p>
                  <p className="text-xs text-slate-500">
                    {stats.flaggedRecords} records under legal review
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Profile Edit Modal */}
      {showProfileEdit && <ProfileEditModal />}
    </div>
  );
}
