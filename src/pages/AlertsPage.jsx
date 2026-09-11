import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  RefreshCw,
  Check
} from 'lucide-react';
import { PatientContextSelector } from '../components/common/PatientContextSelector';

export const AlertsPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const isClinician = userRole === 'doctor' || userRole === 'caregiver';

  const queryPatientId = searchParams.get('patientId');

  const deriveInitialPatientId = () => {
    if (queryPatientId) {
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
      return queryPatientId;
    }
    const stored = sessionStorage.getItem('nexus_selected_patient_id');
    if (stored && isClinician) {
      return stored;
    }
    if (userRole === 'patient' && user?.deviceId) {
      return user.deviceId.replace(/^NP-/i, 'P-');
    }
    if (userRole === 'family' && user?.patientId) {
      return user.patientId;
    }
    return '';
  };

  const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isResolvingId, setIsResolvingId] = useState(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Sync state if query parameter changes
  useEffect(() => {
    if (queryPatientId && queryPatientId !== selectedPatientId) {
      setSelectedPatientId(queryPatientId);
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
    }
  }, [queryPatientId]);

  const fetchAlerts = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (selectedPatientId) {
        params.append('patientId', selectedPatientId);
      }
      if (severityFilter && severityFilter !== 'ALL') {
        params.append('severity', severityFilter);
      }
      if (statusFilter && statusFilter !== 'ALL') {
        params.append('status', statusFilter);
      }

      const res = await authFetch(getApiUrl(`/alerts?${params.toString()}`));
      if (res.ok) {
        const data = await res.json();
        setAlerts(Array.isArray(data) ? data : []);
      } else {
        const errData = await res.json().catch(() => ({}));
        if (res.status === 403) {
          addToast(errData.error || 'Unauthorized access to patient alerts.', 'error');
        }
        setAlerts([]);
      }
    } catch (err) {
      console.error('Error fetching clinical alerts:', err);
      addToast('Failed to load clinical alerts.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, [selectedPatientId, severityFilter, statusFilter]);

  const handleResolveAlert = async (alertId) => {
    try {
      setIsResolvingId(alertId);
      const res = await authFetch(getApiUrl(`/alerts/${alertId}/resolve`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Resolved' })
      });

      if (res.ok) {
        addToast('Alert marked as Resolved.', 'success');
        setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'Resolved' } : a));
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.error || 'Failed to resolve alert.', 'error');
      }
    } catch (err) {
      console.error('Error resolving alert:', err);
      addToast('Network error resolving alert.', 'error');
    } finally {
      setIsResolvingId(null);
    }
  };

  const getSeverityBadge = (severity) => {
    const sev = (severity || '').toUpperCase();
    if (sev === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-200 dark:border-red-900/60">
          <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />
          Critical
        </span>
      );
    }
    if (sev === 'WARNING') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-900/60">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
          Warning
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-900/60">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
        Info
      </span>
    );
  };

  const formatTimestamp = (ts) => {
    if (!ts) return 'Unknown';
    try {
      const d = new Date(ts);
      return `${d.toLocaleDateString()} - ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
    } catch {
      return ts;
    }
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-6 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-left">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200/60 dark:border-red-900/60 flex items-center justify-center text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight">
                Clinical Alerts
              </h1>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-0.5">
                Monitor physiological warnings and emergency events
              </p>
            </div>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex flex-wrap items-center gap-3 self-start sm:self-auto">
          {isClinician && (
            <PatientContextSelector 
              activePatientId={selectedPatientId}
              onSelectPatient={(pid) => {
                setSelectedPatientId(pid);
                sessionStorage.setItem('nexus_selected_patient_id', pid);
              }}
            />
          )}
          <button
            onClick={fetchAlerts}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-600 dark:text-slate-300 transition-colors border-none cursor-pointer"
            title="Refresh Alerts"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        {/* Severity Filters */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider mr-1">
            Severity:
          </span>
          {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => {
            const isSelected = severityFilter === sev;
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all border-none cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-750'
                }`}
              >
                {sev === 'ALL' ? 'All' : sev.charAt(0) + sev.slice(1).toLowerCase()}
              </button>
            );
          })}
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider mr-1">
            Status:
          </span>
          {['ALL', 'Active', 'Resolved'].map((st) => {
            const isSelected = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all border-none cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-750'
                }`}
              >
                {st}
              </button>
            );
          })}
        </div>
      </div>

      {/* Alerts Stream List */}
      <div className="space-y-3">
        {isLoading && alerts.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-12 text-center text-slate-400 text-xs font-semibold">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
            Loading clinical alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-12 text-center text-slate-400 space-y-2">
            <ShieldAlert className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600" />
            <p className="text-sm font-bold text-slate-600 dark:text-slate-300">
              No clinical alerts found.
            </p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              All vital telemetry and biometric readings are within acceptable physiological limits.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const isCritical = (alert.severity || '').toUpperCase() === 'CRITICAL';
            const isActive = (alert.status || '').toLowerCase() === 'active';

            return (
              <div
                key={alert.id}
                className={`bg-white dark:bg-slate-900 rounded-2xl border p-5 shadow-sm transition-all flex flex-col sm:flex-row justify-between sm:items-center gap-4 ${
                  isCritical && isActive
                    ? 'border-red-300 dark:border-red-900/60 bg-red-50/15 dark:bg-red-950/20'
                    : 'border-slate-200 dark:border-slate-850'
                }`}
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    {getSeverityBadge(alert.severity)}
                    <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                      {alert.type || 'Clinical Warning'}
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      Patient: {alert.patient_name || alert.patient_id || 'Unknown'} {alert.patient_id ? `(${alert.patient_id})` : ''}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 font-semibold">
                      Source: {alert.source || 'System'}
                    </span>
                  </div>

                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-snug">
                    {alert.message}
                  </p>

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 font-medium">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {formatTimestamp(alert.timestamp)}
                    </span>
                    <span className="flex items-center gap-1 font-bold">
                      Status: 
                      <span className={isActive ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}>
                        {alert.status || 'Active'}
                      </span>
                    </span>
                  </div>
                </div>

                {/* Action Button */}
                <div className="shrink-0 flex items-center gap-2 self-start sm:self-center">
                  {isActive ? (
                    <button
                      onClick={() => handleResolveAlert(alert.id)}
                      disabled={isResolvingId === alert.id}
                      className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 rounded-xl text-xs font-bold transition-all border-none cursor-pointer shadow-xs disabled:opacity-50"
                    >
                      {isResolvingId === alert.id ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      )}
                      <span>Resolve Alert</span>
                    </button>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/40">
                      <Check className="w-3.5 h-3.5" />
                      <span>Resolved</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default AlertsPage;
