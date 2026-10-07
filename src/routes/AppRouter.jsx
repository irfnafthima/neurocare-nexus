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
import MedicinesPage from '../pages/MedicinesPage';
import CareTeamChatPage from '../pages/CareTeamChatPage';
import ChatbotPage from '../pages/ChatbotPage';
import SettingsPage from '../pages/SettingsPage';
import PatientsPage from '../pages/PatientsPage';
import AlertsPage from '../pages/AlertsPage';
import DevicesPage from '../pages/DevicesPage';
import AuditLogsPage from '../pages/AuditLogsPage';
import DoctorVerificationDashboardPage from '../pages/DoctorVerificationDashboardPage';
import AppLayout from '../components/layout/AppLayout';
import { RPMProvider } from '../context/RPMContext';

/**
 * Route protection wrapper.
 * Redirects unauthenticated users attempting to access protected pages to login page.
 * Redirects restricted/unverified doctors away from clinical pages to verification dashboard.
 */
const ProtectedRoute = ({ children, allowRestrictedDoctor = false }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const isRestrictedDoctor =
    user?.role === 'doctor' &&
    (user?.is_restricted || user?.isRestricted || (user?.verification_status && user?.verification_status !== 'VERIFIED'));

  if (isRestrictedDoctor && !allowRestrictedDoctor) {
    return <Navigate to="/doctor/verification-dashboard" replace />;
  }

  return children;
};

/**
 * Restricted Doctor Verification Route protection wrapper.
 */
const DoctorVerificationRoute = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role !== 'doctor') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

/**
 * Guest route protection wrapper.
 * Prevents logged-in users from accessing login or registration forms.
 */
const GuestRoute = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return children;
  }

  const isRestrictedDoctor =
    user?.role === 'doctor' &&
    (user?.is_restricted || user?.isRestricted || (user?.verification_status && user?.verification_status !== 'VERIFIED'));

  if (isRestrictedDoctor) {
    return <Navigate to="/doctor/verification-dashboard" replace />;
  }

  return <Navigate to="/dashboard" replace />;
};

/**
 * Main application router linking isolated routes under AppLayout.
 */
export const AppRouter = () => {
  return (
    <BrowserRouter>
      <RPMProvider>
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
            <Route path="/doctor-verification" element={<AccessControlsPage />} />
            <Route path="/users" element={<AccessControlsPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
            <Route path="/prescriptions" element={<PrescriptionsPage />} />
            <Route path="/medicines" element={<MedicinesPage />} />
            <Route path="/care-team-chat" element={<CareTeamChatPage />} />
            <Route path="/ai-chatbot" element={<ChatbotPage />} />
            <Route path="/patients" element={<PatientsPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          {/* Restricted Doctor Verification Dashboard */}
          <Route
            path="/doctor/verification-dashboard"
            element={
              <DoctorVerificationRoute>
                <DoctorVerificationDashboardPage />
              </DoctorVerificationRoute>
            }
          />

          {/* Fallback redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </RPMProvider>
    </BrowserRouter>
  );
};


export default AppRouter;
