import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Bell, 
  Sun, 
  Moon, 
  Monitor,
  User,
  Shield,
  KeyRound,
  CheckCircle2,
  FileCheck,
  Cpu,
  ScrollText,
  Lock
} from 'lucide-react';

export const SettingsPage = () => {
  const { user } = useAuth();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const userName = user?.name || user?.full_name || 'User';
  const isAdmin = userRole === 'admin';

  // Admin specific notification preferences
  const [adminNotificationPrefs, setAdminNotificationPrefs] = useState({
    doctorVerificationRequests: true,
    securityAuditEvents: true,
    deviceConnectivityAlerts: true
  });

  // Clinical / non-admin notification preferences
  const [clinicalNotificationPrefs, setClinicalNotificationPrefs] = useState({
    emailAlerts: true,
    pushAlerts: true
  });

  const [activeTheme, setActiveTheme] = useState(() => {
    return localStorage.getItem('nexus_theme') || 'system';
  });

  const handleThemeChange = (newTheme) => {
    setActiveTheme(newTheme);
    localStorage.setItem('nexus_theme', newTheme);
    const root = window.document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else if (newTheme === 'light') {
      root.classList.remove('dark');
    } else {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
    addToast(`Theme set to ${newTheme.toUpperCase()}`, 'info');
  };

  const handleSaveAdminSettings = (e) => {
    e.preventDefault();
    addToast('Administrative notification preferences updated successfully.', 'success');
  };

  const handleSaveClinicalSettings = (e) => {
    e.preventDefault();
    addToast('Notification preferences saved successfully.', 'success');
  };

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          {isAdmin ? 'System & Administrative Settings' : 'Account & Notification Settings'}
        </h1>
        <p className="text-xs font-semibold text-slate-500 mt-1">
          {isAdmin 
            ? 'Manage administrative profile, system governance preferences, and platform security options.' 
            : 'Manage account profile, communication preferences, and display options.'}
        </p>
      </div>

      {/* Account Profile Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
          Active Account Profile
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Name</span>
            <p className="font-bold text-slate-900 dark:text-slate-100 mt-0.5">{userName}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Role</span>
            <p className={`font-bold uppercase mt-0.5 ${isAdmin ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}`}>
              {userRole}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Email / Username</span>
            <p className="font-mono text-slate-700 dark:text-slate-300 mt-0.5">{user?.email || 'Authenticated'}</p>
          </div>
        </div>
      </div>

      {/* ADMIN SPECIFIC SETTINGS */}
      {isAdmin && (
        <>
          {/* Admin Notification Preferences Form */}
          <form onSubmit={handleSaveAdminSettings} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
            <div>
              <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
                Administrative Notification Preferences
              </span>
              <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
                Configure notifications for administrative workflow events and security audits.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.doctorVerificationRequests}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    doctorVerificationRequests: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Doctor Credential Verification Requests
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive notifications when a new doctor application is submitted and requires State Medical Council verification.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.securityAuditEvents}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    securityAuditEvents: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Security & System Audit Notifications
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive alerts for critical security incidents, user access revocations, and system governance events.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.deviceConnectivityAlerts}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    deviceConnectivityAlerts: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Device Gateway & IoT Telemetry Health
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive operational alerts if a biomedical wearable streaming node or synthetic gateway experiences disconnects.
                  </span>
                </div>
              </label>
            </div>

            {/* Governance Ownership Note */}
            <div className="bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800/80 rounded-xl p-3.5 flex items-start gap-3 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div className="text-[11px] text-slate-600 dark:text-slate-300 font-semibold leading-relaxed">
                <span className="font-bold text-slate-900 dark:text-slate-100 block mb-0.5">
                  Clinical Alert Governance Notice
                </span>
                Patient telemetry alarms and physiological threshold notifications are routed directly to authorized consulting clinicians and care teams. The System Administrator manages infrastructure security and role access.
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-850">
              <button
                type="submit"
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer shadow-xs transition-colors"
              >
                Save Notification Preferences
              </button>
            </div>
          </form>

          {/* System Status & Platform Governance */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
              System Status & Platform Governance
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ScrollText className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Audit Logging Engine</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  Active
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-blue-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Doctor Verification Registry</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  5,000 Records Active
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Device Telemetry Fleet</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  Operational
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-amber-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">RBAC & Authentication</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  JWT Enforced
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* NON-ADMIN CLINICAL NOTIFICATION SETTINGS */}
      {!isAdmin && (
        <form onSubmit={handleSaveClinicalSettings} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
            Notification Delivery Preferences
          </span>
          <div className="flex flex-col sm:flex-row gap-6 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={clinicalNotificationPrefs.emailAlerts}
                onChange={e => setClinicalNotificationPrefs({
                  ...clinicalNotificationPrefs, 
                  emailAlerts: e.target.checked
                })}
                className="rounded text-blue-600 focus:ring-0"
              />
              <span className="font-bold text-slate-800 dark:text-slate-200">Email Notifications for Updates</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={clinicalNotificationPrefs.pushAlerts}
                onChange={e => setClinicalNotificationPrefs({
                  ...clinicalNotificationPrefs, 
                  pushAlerts: e.target.checked
                })}
                className="rounded text-blue-600 focus:ring-0"
              />
              <span className="font-bold text-slate-800 dark:text-slate-200">In-App & Push Alerts</span>
            </label>
          </div>

          <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-850">
            <button
              type="submit"
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer shadow-xs"
            >
              Save Preferences
            </button>
          </div>
        </form>
      )}

      {/* Theme Selection Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
          Theme & Display Mode
        </span>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleThemeChange('light')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'light'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Sun className="w-5 h-5 text-amber-500" />
            <span>Light Mode</span>
          </button>

          <button
            onClick={() => handleThemeChange('dark')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'dark'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Moon className="w-5 h-5 text-indigo-400" />
            <span>Dark Mode</span>
          </button>

          <button
            onClick={() => handleThemeChange('system')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'system'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Monitor className="w-5 h-5 text-slate-400" />
            <span>System Default</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
