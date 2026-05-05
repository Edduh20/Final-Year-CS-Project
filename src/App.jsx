import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegistrationPage from "./pages/RegistrationPage";
import DashboardPage from "./pages/DashboardPage";
import LandRecordsPage from "./pages/LandRecordsPage";
import VerificationPage from "./pages/VerificationPage";
import UserManagementPage from "./pages/UserManagementPage";
import NotificationsPage from "./pages/NotificationsPage";
import TransactionsPage from "./pages/TransactionsPage";
import OTPVerificationPage from "./pages/OTPVerificationPage";
import SearchLandRecordsPage from "./pages/SearchLandRecordsPage";
import RevenuePage from "./pages/RevenuePage";  
import LegalCasesPage from "./pages/LegalCasePage";
import SettingsPage from "./pages/SettingsPage";


function ProtectedRoute({ children }) {
  const { user, loading, checkAuth } = useAuth();

  React.useEffect(() => {
    if (!user) {
      checkAuth();
    }
  }, []); 

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading TitleGuard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}


function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <RegistrationPage />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/verify-otp" 
          element={
            <PublicRoute>
              <OTPVerificationPage />
            </PublicRoute>
          } 
        />
        

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout currentPage="dashboard">
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/search-land"
          element={
            <ProtectedRoute>
              <Layout currentPage="search-land">
                <SearchLandRecordsPage />
              </Layout>
            </ProtectedRoute>
          }
        />


        <Route
          path="/land-records"
          element={
            <ProtectedRoute>
              <Layout currentPage="land-records">
                <LandRecordsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/verification"
          element={
            <ProtectedRoute>
              <Layout currentPage="verification">
                <VerificationPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route 
          path="/revenue" 
          element={
            <ProtectedRoute>
              <Layout currentPage="revenue">
                <RevenuePage/>
              </Layout>
            </ProtectedRoute>
          } 
        />

        <Route
          path="/transactions"
          element={
            <ProtectedRoute>
              <Layout currentPage="transactions">
                <TransactionsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout currentPage="users">
                <UserManagementPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <Layout currentPage="notifications">
                <NotificationsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/legal-cases"
          element={
            <ProtectedRoute>
              <Layout currentPage="legal-cases">
                <LegalCasesPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Layout currentPage="settings">
                <SettingsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;