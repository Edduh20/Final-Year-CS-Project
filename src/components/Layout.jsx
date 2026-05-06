import { ReactNode, useState, useEffect } from "react";
import {
  LayoutDashboard,
  HomeIcon,
  Users,
  ClipboardCheck,
  Bell,
  Menu,
  Settings,
  X,
  FileText,
  LogOut,
  MapPin,
  FileCheck2,
  Gavel,
  DollarSign,
  ShieldAlert,
  Search,
  TrendingUp,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL;
export default function Layout({ children, currentPage }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [user, setUser] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchUser();
    fetchUnreadNotifications();
  }, []);

  const fetchUser = async () => {
    try {
      const token = JSON.parse(localStorage.getItem("auth_tokens") || "{}").access;
      const response = await fetch(`${API_URL}/auth/me/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (error) {
      console.error("Failed to fetch user:", error);
    }
  };

  const fetchUnreadNotifications = async () => {
    try {
      const token = JSON.parse(localStorage.getItem("auth_tokens") || "{}").access;
      const response = await fetch(`${API_URL}/notifications/unread_count/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.unread_count || 0);
      }
    } catch (error) {
      console.error("Failed to fetch unread count:", error);
    }
  };

  const handleNavigate = (path) => {
    window.location.href = path;
  };

  const handleSignOut = async () => {
    try {
      const token = JSON.parse(localStorage.getItem("auth_tokens") || "{}").access;
      await fetch(`${API_URL}/auth/logout/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("auth_tokens");
      window.location.href = "/login";
    }
  };

  const role = user?.role?.toLowerCase();


  const navigation = [
    {
      name: "Dashboard",
      icon: HomeIcon,
      page: "dashboard",
      path: "/dashboard",
      roles: ["admin", "land_officer", "legal_officer", "user"],
    },
    {
      name: "User Management",
      icon: Users,
      page: "users",
      path: "/users",
      roles: ["admin"],
    },
    {
      name: "Search Records",
      icon: Search,
      page: "search-land",
      path: "/search-land",
      roles: ["user"],
    },
    {
      name: "Land Records",
      icon: MapPin,
      page: "land-records",
      path: "/land-records",
      roles: ["admin", "land_officer", "user"],
    },
    {
      name: "Legal Cases",
      icon: Gavel,  
      page: "legal-cases",
      path: "/legal-cases", 
      roles: ["legal_officer", "land_officer", "admin", "user"],
    },
    {
      name: "Verification",
      icon: ClipboardCheck,
      page: "verification",
      path: "/verification",
      roles: ["user"],
    },
    {
      name: "Transactions",
      icon: TrendingUp,
      page: "transactions",
      path: "/transactions",
      roles: ["admin", "user", "land_officer", "legal_officer"],
    },
    {
      name: "Revenue",
      icon: DollarSign,
      page: "commissions",
      path: "/revenue",
      roles: ["land_officer", "legal_officer", "admin"],
    },
    {
      name: "Flagged Lands",
      icon: ShieldAlert,
      page: "flagged-lands",
      path: "/land-records?filter=flagged",
      roles: ["legal_officer", "land_officer", "admin"],
    },
    
    {
    name: "Settings",
    icon: Settings,
    page: "settings",
    path: "/settings",
    roles: ["admin", "land_officer", "legal_officer", "user"],
  },
    {
      name: "Notifications",
      icon: Bell,
      page: "notifications",
      path: "/notifications",
      roles: ["admin", "land_officer", "legal_officer", "user"],
      badge: unreadCount > 0 ? unreadCount : undefined,
    },
  ];

  const visibleNav = navigation.filter((n) => n.roles.includes(role || ""));

  const getRoleBadge = (role) => {
    const roles = {
      admin: { color: "bg-red-100 text-red-700", label: "Admin" },
      land_officer: { color: "bg-blue-100 text-blue-700", label: "Land Officer" },
      legal_officer: { color: "bg-amber-100 text-amber-700", label: "Legal Officer" },
      user: { color: "bg-slate-100 text-slate-700", label: "User" },
    };
    return roles[role || "user"];
  };

  const badge = getRoleBadge(role);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Fixed Sidebar */}
      <div 
        className={`bg-white shadow-lg transition-all duration-300 flex flex-col fixed h-screen z-40 ${
          sidebarOpen ? "w-64" : "w-20"
        }`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-3">
            {sidebarOpen && (
              <span className="text-2xl font-bold text-emerald-700">
                TitleGuard
              </span>
            )}
          </div>
        </div>

        {/* Navigation*/}
        <nav className="flex-1 overflow-y-auto p-4 space-y-2">
          {visibleNav.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.page;
            return (
              <button
                key={item.name}
                onClick={() => handleNavigate(item.path)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && (
                  <div className="flex items-center justify-between flex-1">
                    <span className="font-medium">{item.name}</span>
                    {item.badge && (
                      <span className="px-2 py-1 text-xs font-bold bg-red-500 text-white rounded-full">
                        {item.badge > 99 ? "99+" : item.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-slate-200 flex-shrink-0">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
              {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">
                  {user?.full_name || "Loading..."}
                </p>
                <p className="text-xs text-slate-500">
                  {user?.email || "user@example.com"}
                </p>
                <span
                  className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${badge.color}`}
                >
                  {badge.label}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={handleSignOut}
            className="w-full flex items-center space-x-3 px-3 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <LogOut className="h-5 w-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">Sign Out</span>}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div 
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          sidebarOpen ? "ml-64" : "ml-20"
        }`}
      >
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-slate-200 fixed top-0 right-0 left-0 z-30 transition-all duration-300"
          style={{ 
            left: sidebarOpen ? '16rem' : '5rem',
            width: sidebarOpen ? 'calc(100% - 16rem)' : 'calc(100% - 5rem)'
          }}
        >
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                {sidebarOpen ? (
                  <X className="h-5 w-5 text-slate-600" />
                ) : (
                  <Menu className="h-5 w-5 text-slate-600" />
                )}
              </button>
              <h1 className="text-2xl font-bold text-slate-800 capitalize">
                {currentPage?.replace("-", " ") || "Dashboard"}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <button
                onClick={() => handleNavigate("/notifications")}
                className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <Bell className="h-5 w-5 text-slate-600" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </button>

              {/* User Profile */}
              {!sidebarOpen && (
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-slate-800">
                      {user?.full_name || "Loading..."}
                    </p>
                    <p className="text-xs text-slate-500 capitalize">
                      {role || "User"}
                    </p>
                  </div>
                  <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Scrollable Page Content */}
        <main 
          className="flex-1 overflow-auto p-6 mt-16"
          style={{ marginTop: '4rem' }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}