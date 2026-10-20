import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AdminAnalyticsDashboard from '../components/admin/AdminAnalyticsDashboard';
import { ShieldAlert } from 'lucide-react';

/**
 * AdminAnalyticsPage — Route entry point for /admin/analytics.
 * Strictly verifies role='admin' before rendering dashboard.
 */
export const AdminAnalyticsPage = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const role = (user?.role || '').toLowerCase();
  if (role !== 'admin') {
    return (
      <div className="p-8 max-w-xl mx-auto text-left space-y-4">
        <div className="p-6 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-3xl space-y-3">
          <div className="flex items-center gap-2.5 text-red-700 dark:text-red-300">
            <ShieldAlert className="w-6 h-6" />
            <h3 className="text-base font-black">Administrative Access Restricted</h3>
          </div>
          <p className="text-xs text-red-600 dark:text-red-400 font-semibold leading-relaxed">
            Your current account role ({role.toUpperCase()}) does not have clearance to view platform usage analytics. Only administrators can access this workspace.
          </p>
        </div>
      </div>
    );
  }

  return <AdminAnalyticsDashboard />;
};

export default AdminAnalyticsPage;
