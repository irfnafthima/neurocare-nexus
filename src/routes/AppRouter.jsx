import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LandingPage from '../pages/LandingPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import DashboardPage from '../pages/DashboardPage';
import VitalsPage from '../pages/VitalsPage';
import HealthRecordsPage from '../pages/HealthRecordsPage';
import AccessControlsPage from '../pages/AccessControlsPage';
import PrescriptionsPage from '../pages/PrescriptionsPage';
import CareTeamChatPage from '../pages/CareTeamChatPage';
import ChatbotPage from '../pages/ChatbotPage';
import SettingsPage from '../pages/SettingsPage';
import AppLayout from '../components/layout/AppLayout';

/**
 * Route protection wrapper.
 * Redirects unauthenticated users attempting to access protected pages to login page.
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

/**
 * Guest route protection wrapper.
 * Prevents logged-in users from accessing login or registration forms.
 */
const GuestRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />;
};

/**
 * Main application router linking isolated routes under AppLayout.
 */
export const AppRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Guest Authentication Routes */}
        <Route 
          path="/login" 
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          } 
        />

        {/* Protected Application Routes wrapped with AppLayout */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/vitals" element={<VitalsPage />} />
          <Route path="/health-records" element={<HealthRecordsPage />} />
          <Route path="/access-controls" element={<AccessControlsPage />} />
          <Route path="/prescriptions" element={<PrescriptionsPage />} />
          <Route path="/care-team-chat" element={<CareTeamChatPage />} />
          <Route path="/ai-chatbot" element={<ChatbotPage />} />
          <Route path="/settings" element={<SettingsPage />} />

          {/* Alias / Role Navigation paths mapped to isolated pages */}
          <Route path="/devices" element={<DashboardPage />} />
          <Route path="/users" element={<AccessControlsPage />} />
          <Route path="/audit-logs" element={<DashboardPage />} />
          <Route path="/patients" element={<DashboardPage />} />
          <Route path="/alerts" element={<VitalsPage />} />
        </Route>

        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
