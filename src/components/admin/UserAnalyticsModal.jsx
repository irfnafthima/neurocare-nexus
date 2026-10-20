import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { apiService } from '../../services/api';
import { formatDuration, formatFullDateTime, formatRelativeTime } from '../../utils/analyticsFormatters';
import {
  X,
  User,
  Clock,
  Activity,
  Calendar,
  Shield,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

/**
 * UserAnalyticsModal — Slide-over detail panel for individual user platform usage.
 * Strictly presents platform activity and session metrics; zero clinical/medical data.
 */
export const UserAnalyticsModal = ({ userId, isOpen, onClose }) => {
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !userId) {
      setData(null);
      setError(null);
      return;
    }

    const fetchUserStats = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await apiService.getAnalyticsUserDetail(authFetch, userId);
        if (!res.ok) {
          if (res.status === 403) {
            throw new Error('Administrative authorization is required.');
          }
          if (res.status === 404) {
            throw new Error('User not found.');
          }
          throw new Error('Failed to load user analytics data.');
        }
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err.message || 'Error fetching user metrics.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserStats();
  }, [isOpen, userId]);

  if (!isOpen) return null;

  const presenceBadge = (presence) => {
    if (presence === 'ACTIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          ACTIVE
        </span>
      );
    }
    if (presence === 'IDLE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          IDLE
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
        <span className="w-2 h-2 rounded-full bg-slate-400" />
        OFFLINE
      </span>
    );
  };

  const roleBadge = (role) => {
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-analytics-title"
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400 font-black">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 id="user-analytics-title" className="text-base font-black text-slate-950 dark:text-slate-50">
                User Platform Engagement
              </h2>
              <p className="text-xs text-slate-400 font-medium">
                Detailed session duration, login timeline, and presence history
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border-none bg-transparent cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-left">
          {isLoading && (
            <div className="py-16 text-center space-y-3">
              <RefreshCw className="w-7 h-7 text-blue-600 animate-spin mx-auto" />
              <p className="text-xs font-bold text-slate-400">Loading platform metrics...</p>
            </div>
          )}

          {error && !isLoading && (
            <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-300 text-xs font-bold">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {data && !isLoading && (
            <>
              {/* User Identity Banner */}
              <div className="p-4 bg-slate-50 dark:bg-slate-850/60 rounded-2xl border border-slate-200/80 dark:border-slate-800 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-black text-slate-900 dark:text-slate-100">
                      {data.displayName}
                    </span>
                    {roleBadge(data.role)}
                    {presenceBadge(data.currentPresence)}
                  </div>
                  <p className="text-xs text-slate-500 font-mono">
                    {data.email} • ID: #{data.userId}
                  </p>
                </div>
                <div className="text-right text-xs text-slate-400 space-y-0.5">
                  <p>Registered: <span className="font-semibold text-slate-700 dark:text-slate-300">{formatFullDateTime(data.createdAt)}</span></p>
                  <p>Last Login: <span className="font-semibold text-slate-700 dark:text-slate-300">{formatRelativeTime(data.lastLogin)}</span></p>
                </div>
              </div>

              {/* Active Session Callout (if active/idle) */}
              {data.activeSession && (
                <div className="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/60 rounded-2xl space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black uppercase text-emerald-600 dark:text-emerald-400 tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                      Ongoing Browser Session
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-500">
                      Duration: <strong className="text-emerald-700 dark:text-emerald-300">{formatDuration(data.activeSession.durationSeconds)}</strong>
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs pt-1 border-t border-emerald-100 dark:border-emerald-900/40">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Started</span>
                      <span className="font-bold text-slate-700 dark:text-slate-300">{formatRelativeTime(data.activeSession.startedAt)}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Last Heartbeat</span>
                      <span className="font-bold text-slate-700 dark:text-slate-300">{formatRelativeTime(data.activeSession.lastHeartbeatAt)}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Last Activity</span>
                      <span className="font-bold text-slate-700 dark:text-slate-300">{formatRelativeTime(data.activeSession.lastActivityAt)}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Frequency Stats Grid */}
              <div className="space-y-2">
                <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                  Session Distribution
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center">
                    <span className="text-[10px] font-black uppercase text-slate-400 block">Total Sessions</span>
                    <span className="text-xl font-black text-slate-900 dark:text-slate-100">{data.totalSessions}</span>
                  </div>
                  <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center">
                    <span className="text-[10px] font-black uppercase text-slate-400 block">Today</span>
                    <span className="text-xl font-black text-blue-600 dark:text-blue-400">{data.sessionsToday}</span>
                  </div>
                  <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center">
                    <span className="text-[10px] font-black uppercase text-slate-400 block">Last 7 Days</span>
                    <span className="text-xl font-black text-indigo-600 dark:text-indigo-400">{data.sessionsLast7Days}</span>
                  </div>
                  <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center">
                    <span className="text-[10px] font-black uppercase text-slate-400 block">Last 30 Days</span>
                    <span className="text-xl font-black text-purple-600 dark:text-purple-400">{data.sessionsLast30Days}</span>
                  </div>
                </div>
              </div>

              {/* Duration Metrics Grid */}
              <div className="space-y-2">
                <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                  Engagement & Duration Metrics
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-4 bg-slate-50 dark:bg-slate-850/40 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-xs text-slate-400">
                      <span className="font-bold">Total Platform Time</span>
                      <Clock className="w-4 h-4 text-blue-500" />
                    </div>
                    <p className="text-xl font-black text-slate-900 dark:text-slate-100">
                      {formatDuration(data.totalUsageSeconds)}
                    </p>
                    <span className="text-[10px] text-slate-400 font-medium">Cumulative active & completed sessions</span>
                  </div>

                  <div className="p-4 bg-slate-50 dark:bg-slate-850/40 rounded-2xl border border-slate-200 dark:border-slate-850 space-y-1">
                    <div className="flex justify-between items-center text-xs text-slate-400">
                      <span className="font-bold">Average Session Length</span>
                      <Layers className="w-4 h-4 text-emerald-500" />
                    </div>
                    <p className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                      {formatDuration(data.averageSessionDurationSeconds)}
                    </p>
                    <span className="text-[10px] text-slate-400 font-medium">Mean duration across all sessions</span>
                  </div>

                  <div className="p-4 bg-slate-50 dark:bg-slate-850/40 rounded-2xl border border-slate-200 dark:border-slate-850 space-y-1">
                    <div className="flex justify-between items-center text-xs text-slate-400">
                      <span className="font-bold">Longest Session</span>
                      <Activity className="w-4 h-4 text-purple-500" />
                    </div>
                    <p className="text-lg font-black text-slate-800 dark:text-slate-200">
                      {formatDuration(data.longestSessionDurationSeconds)}
                    </p>
                    <span className="text-[10px] text-slate-400 font-medium">Peak single-session duration</span>
                  </div>

                  <div className="p-4 bg-slate-50 dark:bg-slate-850/40 rounded-2xl border border-slate-200 dark:border-slate-850 space-y-1">
                    <div className="flex justify-between items-center text-xs text-slate-400">
                      <span className="font-bold">Shortest Completed</span>
                      <Clock className="w-4 h-4 text-amber-500" />
                    </div>
                    <p className="text-lg font-black text-slate-800 dark:text-slate-200">
                      {data.shortestCompletedSessionDurationSeconds ? formatDuration(data.shortestCompletedSessionDurationSeconds) : 'No closed sessions'}
                    </p>
                    <span className="text-[10px] text-slate-400 font-medium">Minimum closed session duration</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-colors border-none cursor-pointer"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserAnalyticsModal;
