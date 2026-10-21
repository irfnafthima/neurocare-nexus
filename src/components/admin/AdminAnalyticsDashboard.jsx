import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { apiService } from '../../services/api';
import {
  formatDuration,
  formatDateLabel,
  formatRelativeTime,
  formatFullDateTime
} from '../../utils/analyticsFormatters';
import UserAnalyticsModal from './UserAnalyticsModal';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import {
  Users,
  Activity,
  Clock,
  UserCheck,
  TrendingUp,
  LayoutDashboard,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Eye,
  Shield,
  Layers,
  Calendar,
  CheckCircle2,
  Server
} from 'lucide-react';

/**
 * AdminAnalyticsDashboard — Professional Platform Engagement & Session Analytics.
 * Strictly consumes Phase C backend analytics APIs. Zero clinical data.
 */
export const AdminAnalyticsDashboard = () => {
  const { authFetch, logout } = useAuth();
  const navigate = useNavigate();

  // Core Data States
  const [overview, setOverview] = useState(null);
  const [roles, setRoles] = useState([]);
  const [sessions, setSessions] = useState(null);
  const [trends, setTrends] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);

  // Range Selectors
  const [trendRange, setTrendRange] = useState('7d');
  const [sessionRange, setSessionRange] = useState('7d');

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);

  // Selected User Modal
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  /**
   * Fetches all analytics data concurrently from Phase C endpoints.
   */
  const fetchAllAnalytics = useCallback(async (isSilentRefresh = false) => {
    if (!isSilentRefresh) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }
    setError(null);

    try {
      const [
        overviewRes,
        rolesRes,
        sessionsRes,
        trendsRes,
        onlineUsersRes
      ] = await Promise.all([
        apiService.getAnalyticsOverview(authFetch),
        apiService.getAnalyticsRoles(authFetch),
        apiService.getAnalyticsSessions(authFetch, sessionRange),
        apiService.getAnalyticsTrends(authFetch, trendRange),
        apiService.getAnalyticsOnlineUsers(authFetch)
      ]);

      if (
        overviewRes.status === 401 ||
        rolesRes.status === 401 ||
        sessionsRes.status === 401 ||
        trendsRes.status === 401 ||
        onlineUsersRes.status === 401
      ) {
        throw new Error('Your session has expired. Please log in again to access administrative platform analytics.');
      }

      if (
        overviewRes.status === 403 ||
        rolesRes.status === 403 ||
        sessionsRes.status === 403 ||
        trendsRes.status === 403 ||
        onlineUsersRes.status === 403
      ) {
        throw new Error('Administrative authorization required to access platform analytics.');
      }

      if (!overviewRes.ok || !rolesRes.ok || !sessionsRes.ok || !trendsRes.ok || !onlineUsersRes.ok) {
        throw new Error('Failed to synchronize one or more analytics services.');
      }

      const [overviewData, rolesData, sessionsData, trendsData, onlineUsersData] = await Promise.all([
        overviewRes.json(),
        rolesRes.json(),
        sessionsRes.json(),
        trendsRes.json(),
        onlineUsersRes.json()
      ]);

      setOverview(overviewData);
      setRoles(rolesData);
      setSessions(sessionsData);
      setTrends(trendsData);
      setOnlineUsers(onlineUsersData);
      setLastRefreshedAt(new Date());
    } catch (err) {
      console.error('[AdminAnalytics] Fetch error:', err);
      setError(err.message || 'An error occurred while loading analytics metrics.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [authFetch, sessionRange, trendRange]);

  // Initial load and range-dependent re-fetching
  useEffect(() => {
    fetchAllAnalytics(false);
  }, [fetchAllAnalytics]);

  // Periodic controlled polling every 45 seconds (avoids excessive continuous polling)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAllAnalytics(true);
    }, 45000);
    return () => clearInterval(interval);
  }, [fetchAllAnalytics]);

  const handleOpenUserDetail = (userId) => {
    setSelectedUserId(userId);
    setIsModalOpen(true);
  };

  // Helper for presence badges
  const renderPresenceBadge = (presence) => {
    if (presence === 'ACTIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          ACTIVE
        </span>
      );
    }
    if (presence === 'IDLE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          IDLE
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
        OFFLINE
      </span>
    );
  };

  const renderRoleBadge = (role) => {
    const r = (role || '').toLowerCase();
    const colors = {
      doctor: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900',
      patient: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-900',
      caregiver: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900',
      family: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-900',
      admin: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900'
    };
    return (
      <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${colors[r] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
        {role}
      </span>
    );
  };

  // Error Banner
  if (error && !overview) {
    const isSessionExpired = error.toLowerCase().includes('expired') || error.toLowerCase().includes('authorization');

    return (
      <div className="p-8 max-w-5xl mx-auto text-left space-y-4">
        <div className="p-6 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-3xl space-y-3">
          <div className="flex items-center gap-3 text-red-700 dark:text-red-300">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <h3 className="text-base font-black">
              {isSessionExpired ? 'Session Expired' : 'Analytics Connection Error'}
            </h3>
          </div>
          <p className="text-xs text-red-600 dark:text-red-400 font-semibold">{error}</p>
          <div className="flex items-center gap-3 pt-1">
            {isSessionExpired && (
              <button
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors border-none cursor-pointer inline-flex items-center gap-2"
              >
                <span>Log In Again</span>
              </button>
            )}
            <button
              onClick={() => fetchAllAnalytics(false)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-colors border-none cursor-pointer inline-flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Connection</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left max-w-6xl mx-auto font-sans select-none pb-12">
      {/* Top Header & Refresh Strip */}
      <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight">
              Platform Activity & Analytics
            </h1>
            <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-900">
              Admin Telemetry
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-1">
            Real-time user presence, active sessions, platform usage duration, and login trends.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {lastRefreshedAt && (
            <span className="text-[11px] text-slate-400 font-medium">
              Updated: {lastRefreshedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => fetchAllAnalytics(true)}
            disabled={isRefreshing || isLoading}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold transition-colors border-none cursor-pointer inline-flex items-center gap-1.5 disabled:opacity-50"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-blue-600' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* STEP 4: TOP KPI SECTION */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Total Users */}
        <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs space-y-1">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Total Users</span>
            <Users className="w-4 h-4 text-slate-500" />
          </div>
          <p className="text-2xl font-black text-slate-900 dark:text-slate-100">
            {isLoading ? '...' : (overview?.total_users ?? 0)}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">Registered accounts</span>
        </div>

        {/* Online Users */}
        <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs space-y-1">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Online Now</span>
            <Activity className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {isLoading ? '...' : (overview?.online_users ?? 0)}
          </p>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
            {overview?.active_users ?? 0} Active • {overview?.idle_users ?? 0} Idle
          </span>
        </div>

        {/* Sessions Today */}
        <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs space-y-1">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Sessions Today</span>
            <LayoutDashboard className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-black text-blue-600 dark:text-blue-400">
            {isLoading ? '...' : (overview?.sessions_today ?? 0)}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">
            {overview?.active_today ?? 0} active users today
          </span>
        </div>

        {/* Total Platform Usage */}
        <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs space-y-1">
          <div className="flex justify-between items-center text-slate-400">
            <span className="text-[10px] font-black uppercase tracking-wider">Total Usage</span>
            <TrendingUp className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-black text-purple-600 dark:text-purple-400">
            {isLoading ? '...' : formatDuration(overview?.total_platform_usage_seconds)}
          </p>
          <span className="text-[10px] text-slate-400 font-semibold">
            Avg: {formatDuration(overview?.average_session_duration_seconds)}
          </span>
        </div>
      </div>

      {/* STEP 5: LIVE PRESENCE & ACTIVITY SPLIT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Presence Distribution Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-xs space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
            <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              Live Presence Breakdown
            </h2>
            <span className="text-[10px] font-extrabold text-slate-400 uppercase">Real-Time</span>
          </div>

          {/* Metric Bar */}
          {overview && (
            <div className="space-y-3">
              <div className="h-3.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${overview.total_users > 0 ? (overview.active_users / overview.total_users) * 100 : 0}%` }}
                  className="bg-emerald-500 h-full transition-all"
                  title={`Active: ${overview.active_users}`}
                />
                <div
                  style={{ width: `${overview.total_users > 0 ? (overview.idle_users / overview.total_users) * 100 : 0}%` }}
                  className="bg-amber-400 h-full transition-all"
                  title={`Idle: ${overview.idle_users}`}
                />
                <div
                  style={{ width: `${overview.total_users > 0 ? (overview.offline_users / overview.total_users) * 100 : 0}%` }}
                  className="bg-slate-300 dark:bg-slate-700 h-full transition-all"
                  title={`Offline: ${overview.offline_users}`}
                />
              </div>

              {/* Presence Legend Cards */}
              <div className="grid grid-cols-3 gap-2 text-center pt-2">
                <div className="p-3 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 rounded-2xl">
                  <span className="text-[10px] font-black uppercase text-emerald-600 dark:text-emerald-400 block">Active</span>
                  <span className="text-xl font-black text-emerald-700 dark:text-emerald-300">{overview.active_users}</span>
                  <span className="text-[9px] text-emerald-600/80 block mt-0.5">
                    {overview.total_users > 0 ? Math.round((overview.active_users / overview.total_users) * 100) : 0}%
                  </span>
                </div>
                <div className="p-3 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/40 rounded-2xl">
                  <span className="text-[10px] font-black uppercase text-amber-600 dark:text-amber-400 block">Idle</span>
                  <span className="text-xl font-black text-amber-700 dark:text-amber-300">{overview.idle_users}</span>
                  <span className="text-[9px] text-amber-600/80 block mt-0.5">
                    {overview.total_users > 0 ? Math.round((overview.idle_users / overview.total_users) * 100) : 0}%
                  </span>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 rounded-2xl">
                  <span className="text-[10px] font-black uppercase text-slate-500 block">Offline</span>
                  <span className="text-xl font-black text-slate-700 dark:text-slate-300">{overview.offline_users}</span>
                  <span className="text-[9px] text-slate-400 block mt-0.5">
                    {overview.total_users > 0 ? Math.round((overview.offline_users / overview.total_users) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="text-[11px] text-slate-400 font-medium space-y-1 pt-1 border-t border-slate-100 dark:border-slate-800">
            <p>• <strong>Active:</strong> Heartbeat &le; 2m and interaction &le; 5m</p>
            <p>• <strong>Idle:</strong> Heartbeat &le; 2m but no interaction &gt; 5m</p>
            <p>• <strong>Offline:</strong> Session closed or heartbeat &gt; 2m</p>
          </div>
        </div>

        {/* STEP 8: LOGIN & ACTIVITY TRENDS CHART */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Platform Activity & Login Trends
              </h2>
              <p className="text-[11px] text-slate-400 font-semibold">Real login sessions and user activity timeline</p>
            </div>

            {/* Range Toggle */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start sm:self-auto">
              {['today', '7d', '30d'].map((r) => (
                <button
                  key={r}
                  onClick={() => setTrendRange(r)}
                  className={`px-3 py-1 rounded-lg text-xs font-black transition-all border-none cursor-pointer uppercase ${
                    trendRange === r
                      ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 bg-transparent'
                  }`}
                >
                  {r === 'today' ? 'Today' : r === '7d' ? '7 Days' : '30 Days'}
                </button>
              ))}
            </div>
          </div>

          {/* Chart Canvas */}
          <div className="h-64 w-full">
            {trends?.data && trends.data.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends.data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="sessionsGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="loginsGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDateLabel}
                    stroke="#94a3b8"
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '12px',
                      color: '#f8fafc',
                      fontSize: '12px',
                      fontWeight: 600
                    }}
                    labelFormatter={(l) => `Date: ${l}`}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Area
                    type="monotone"
                    dataKey="sessions_started"
                    name="Sessions"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#sessionsGrad)"
                  />
                  <Area
                    type="monotone"
                    dataKey="logins"
                    name="Logins"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#loginsGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs font-semibold text-slate-400">
                No activity records logged in this timeframe.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* STEP 7 & 9: ROLE COMPARISON & SESSION ANALYTICS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Role Analytics Bar Chart */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-xs space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Role-Wise Platform Engagement
              </h2>
              <p className="text-[11px] text-slate-400 font-semibold">User base and active presence across roles</p>
            </div>
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
              5 Roles
            </span>
          </div>

          <div className="h-64 w-full">
            {roles && roles.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={roles} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="role" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '12px',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="total_users" name="Total" fill="#64748b" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="active_now" name="Active Now" fill="#10b981" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="idle_now" name="Idle Now" fill="#f59e0b" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs font-semibold text-slate-400">
                No role metrics recorded.
              </div>
            )}
          </div>
        </div>

        {/* Session Analytics Metrics Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Session Analytics & Durations
              </h2>
              <p className="text-[11px] text-slate-400 font-semibold">Duration distribution and session completion stats</p>
            </div>

            {/* Session Range Toggle */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl self-start sm:self-auto">
              {['today', '7d', '30d'].map((r) => (
                <button
                  key={r}
                  onClick={() => setSessionRange(r)}
                  className={`px-3 py-1 rounded-lg text-xs font-black transition-all border-none cursor-pointer uppercase ${
                    sessionRange === r
                      ? 'bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 bg-transparent'
                  }`}
                >
                  {r === 'today' ? 'Today' : r === '7d' ? '7 Days' : '30 Days'}
                </button>
              ))}
            </div>
          </div>

          {/* Session Metrics Grid */}
          {sessions ? (
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="p-3.5 bg-slate-50 dark:bg-slate-850/50 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-0.5">
                <span className="text-[10px] font-black uppercase text-slate-400 block">Total Volume</span>
                <span className="text-xl font-black text-slate-900 dark:text-slate-100">{sessions.session_count}</span>
                <span className="text-[10px] text-slate-400 block">
                  {sessions.completed_sessions} closed • {sessions.active_sessions} ongoing
                </span>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-850/50 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-0.5">
                <span className="text-[10px] font-black uppercase text-slate-400 block">Total Time</span>
                <span className="text-xl font-black text-blue-600 dark:text-blue-400">
                  {formatDuration(sessions.total_usage_seconds)}
                </span>
                <span className="text-[10px] text-slate-400 block">Cumulative period usage</span>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-850/50 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-0.5">
                <span className="text-[10px] font-black uppercase text-slate-400 block">Average Duration</span>
                <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                  {formatDuration(sessions.average_duration_seconds)}
                </span>
                <span className="text-[10px] text-slate-400 block">
                  Median: {formatDuration(sessions.median_duration_seconds)}
                </span>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-850/50 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-0.5">
                <span className="text-[10px] font-black uppercase text-slate-400 block">Session Extremes</span>
                <span className="text-sm font-black text-slate-900 dark:text-slate-100 block">
                  Max: {formatDuration(sessions.longest_duration_seconds)}
                </span>
                <span className="text-[10px] text-slate-400 block">
                  Min: {sessions.shortest_duration_seconds ? formatDuration(sessions.shortest_duration_seconds) : 'N/A'}
                </span>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-xs font-semibold text-slate-400">
              Loading session duration analytics...
            </div>
          )}
        </div>
      </div>

      {/* STEP 6: LIVE ONLINE USERS TABLE */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
          <div>
            <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
              Live Active & Idle Sessions
            </h2>
            <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
              Real-time authenticated browser sessions transmitting heartbeat telemetry
            </p>
          </div>
          <span className="text-xs font-black text-slate-500 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
            {onlineUsers.length} Online
          </span>
        </div>

        {/* Table / Empty State */}
        <div className="overflow-x-auto">
          {onlineUsers && onlineUsers.length > 0 ? (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/70 dark:bg-slate-850/50 text-[10px] font-black text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                  <th className="py-3 px-5">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Presence</th>
                  <th className="py-3 px-4">Session Duration</th>
                  <th className="py-3 px-4">Last Activity</th>
                  <th className="py-3 px-4">Last Heartbeat</th>
                  <th className="py-3 px-5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-semibold">
                {onlineUsers.map((u) => (
                  <tr key={u.sessionId} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/30 transition-colors">
                    <td className="py-3.5 px-5">
                      <div className="space-y-0.5">
                        <span className="font-black text-slate-900 dark:text-slate-100 block">
                          {u.displayName}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono block">
                          {u.email}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">{renderRoleBadge(u.role)}</td>
                    <td className="py-3.5 px-4">{renderPresenceBadge(u.presence)}</td>
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-700 dark:text-slate-300">
                      {formatDuration(u.durationSeconds)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {formatRelativeTime(u.lastActivityAt)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                      {formatRelativeTime(u.lastHeartbeatAt)}
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={() => handleOpenUserDetail(u.userId)}
                        className="px-3 py-1.5 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white rounded-xl text-[11px] font-bold transition-all border border-blue-200 dark:border-blue-900 cursor-pointer inline-flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center space-y-2">
              <Server className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">No Active Sessions Right Now</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                All registered accounts are currently offline. When users authenticate, their presence and activity telemetry will stream here automatically.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Individual User Analytics Modal */}
      <UserAnalyticsModal
        userId={selectedUserId}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedUserId(null);
        }}
      />
    </div>
  );
};

export default AdminAnalyticsDashboard;
