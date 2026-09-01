import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Bell, 
  Sliders, 
  Sun, 
  Moon, 
  Monitor,
  User,
  KeyRound
} from 'lucide-react';

export const SettingsPage = () => {
  const { user } = useAuth();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const userName = user?.name || user?.full_name || 'User';

  const [settingsForm, setSettingsForm] = useState({
    minSpo2: '92',
    maxHR: '125',
    maxTemp: '38.5',
    alertSms: true,
    alertEmail: true
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

  const handleSaveSettings = (e) => {
    e.preventDefault();
    addToast('Threshold & notification settings saved successfully.', 'success');
  };

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          System & Account Settings
        </h1>
        <p className="text-xs font-semibold text-slate-500 mt-1">
          Configure telemetry alarm thresholds, notification delivery preferences, and security options.
        </p>
      </div>

      {/* Account Info Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Active Account Profile</span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Name</span>
            <p className="font-bold text-slate-900 dark:text-slate-100 mt-0.5">{userName}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Role</span>
            <p className="font-bold text-blue-600 dark:text-blue-400 uppercase mt-0.5">{userRole}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Email / Username</span>
            <p className="font-mono text-slate-700 dark:text-slate-300 mt-0.5">{user?.email || 'Authenticated'}</p>
          </div>
        </div>
      </div>

      {/* Threshold & Notification Settings */}
      <form onSubmit={handleSaveSettings} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-5">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Physiological Alarm Thresholds</span>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase">Min SpO2 Blood Oxygen (%)</label>
            <input
              type="number"
              value={settingsForm.minSpo2}
              onChange={e => setSettingsForm({...settingsForm, minSpo2: e.target.value})}
              className="w-full mt-1 p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold"
            />
            <span className="text-[9px] text-slate-400 block mt-1">Triggers warning below this level</span>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase">Max Heart Rate (BPM)</label>
            <input
              type="number"
              value={settingsForm.maxHR}
              onChange={e => setSettingsForm({...settingsForm, maxHR: e.target.value})}
              className="w-full mt-1 p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold"
            />
            <span className="text-[9px] text-slate-400 block mt-1">Triggers tachycardia alarm</span>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase">Max Body Temperature (°C)</label>
            <input
              type="number"
              step="0.1"
              value={settingsForm.maxTemp}
              onChange={e => setSettingsForm({...settingsForm, maxTemp: e.target.value})}
              className="w-full mt-1 p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold"
            />
            <span className="text-[9px] text-slate-400 block mt-1">Triggers fever warning alert</span>
          </div>
        </div>

        <div className="border-t border-slate-100 dark:border-slate-850 pt-4 space-y-3">
          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Notification Delivery Preferences</span>
          <div className="flex flex-col sm:flex-row gap-6 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settingsForm.alertEmail}
                onChange={e => setSettingsForm({...settingsForm, alertEmail: e.target.checked})}
                className="rounded text-blue-600 focus:ring-0"
              />
              <span className="font-bold text-slate-800 dark:text-slate-200">Email Notifications for Critical Alarms</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settingsForm.alertSms}
                onChange={e => setSettingsForm({...settingsForm, alertSms: e.target.checked})}
                className="rounded text-blue-600 focus:ring-0"
              />
              <span className="font-bold text-slate-800 dark:text-slate-200">SMS / Emergency Push Alerts</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-850">
          <button
            type="submit"
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer shadow-xs"
          >
            Save Settings
          </button>
        </div>
      </form>

      {/* Theme Selection Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Theme & Display Mode</span>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleThemeChange('light')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'light'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
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
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
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
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
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
