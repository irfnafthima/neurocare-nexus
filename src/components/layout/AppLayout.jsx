import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../common/Toast';
import Sidebar from '../common/Sidebar';
import { getApiUrl } from '../../services/api';
import {
  Bell,
  LogOut,
  Menu,
  Sparkles
} from 'lucide-react';

/**
 * AppLayout — Unified authenticated workspace layout.
 * Wraps Topbar, Sidebar, Notification center, and renders isolated Page content.
 */
export const AppLayout = () => {
  const { user, logout, authFetch } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'doctor';
  const userName = user?.name || user?.full_name || 'User';

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Real Database Notifications State
  const [dbNotifications, setDbNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const formatTimeAgo = (timestampStr) => {
    if (!timestampStr) return 'Just now';
    const diffMs = new Date() - new Date(timestampStr);
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const fetchNotifications = async () => {
    try {
      const res = await authFetch(getApiUrl('/notifications/'));
      if (res.ok) {
        const data = await res.json();
        setDbNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (e) {
      console.error('Error fetching notifications:', e);
    }
  };

  useEffect(() => {
    if (user?.token) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [user?.token]);

  const handleMarkNotificationRead = async (notif) => {
    try {
      await authFetch(getApiUrl(`/notifications/${notif.id}/read/`), { method: 'POST' });
      setDbNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
      if (notif.category === 'chat') {
        navigate('/care-team-chat');
      } else if (notif.category === 'alarm' || notif.category === 'vital') {
        navigate('/vitals');
      }
    } catch (e) {
      console.error('Error marking notification as read:', e);
    }
  };

  const handleMarkAllNotificationsRead = async () => {
    try {
      await authFetch(getApiUrl('/notifications/read-all/'), { method: 'POST' });
      setDbNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      addToast('All notifications marked as read', 'success');
    } catch (e) {
      console.error('Error marking all notifications as read:', e);
    }
  };

  const handleLogout = () => {
    logout();
    addToast('Signed out of secure session.', 'info');
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-sans" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar - Dynamically configured per role */}
      <Sidebar 
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        role={userRole}
      />

      <div className="flex-grow flex flex-col min-w-0">
        {/* Sticky Header */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 shrink-0 sticky top-0 z-30 gap-4 select-none">
          <button 
            onClick={() => setIsMobileSidebarOpen(true)} 
            className="md:hidden p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 mr-2 border-none bg-transparent cursor-pointer"
            aria-label="Open Navigation Menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Role specific header labels */}
          <div className="text-left">
            <div className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider leading-none">Security Portal</div>
            <div className="text-sm font-black text-slate-900 dark:text-slate-100 mt-1 leading-none">
              {userRole === 'admin' && 'Root System Administration'}
              {userRole === 'doctor' && 'Clinician Oversight Workspace'}
              {userRole === 'caregiver' && 'Caregiver Operations Workspace'}
              {userRole === 'patient' && 'Patient Health Dashboard'}
              {userRole === 'family' && 'Relative Care Monitor'}
            </div>
          </div>

          <div className="flex items-center gap-4 ml-auto">
            {/* Live compliance stamp */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_#10B981] animate-pulse" />
              <span className="text-[9px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">HIPAA Secure Channel</span>
            </div>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => {
                  const nextState = !isNotificationOpen;
                  setIsNotificationOpen(nextState);
                  setIsProfileOpen(false);
                  if (nextState) fetchNotifications();
                }}
                className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all duration-200 relative cursor-pointer ${
                  isNotificationOpen 
                    ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900 text-blue-650 dark:text-blue-400' 
                    : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400'
                }`}
                aria-label="Toggle notifications"
              >
                <Bell className="w-[18px] h-[18px]" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full text-[9px] font-black bg-blue-600 text-white border border-white dark:border-slate-900 min-w-[16px] text-center leading-none">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              {isNotificationOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl z-50 overflow-hidden text-left animate-fade-in">
                  <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-950/40">
                    <span className="font-black text-xs text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                      Notifications Log
                    </span>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllNotificationsRead}
                        className="text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline bg-transparent border-none cursor-pointer"
                      >
                        Mark all as read
                      </button>
                    )}
                  </div>
                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-850">
                    {dbNotifications.length === 0 ? (
                      <div className="p-6 text-center text-xs font-semibold text-slate-400 dark:text-slate-500">
                        No new notifications
                      </div>
                    ) : (
                      dbNotifications.map(notif => (
                        <div
                          key={notif.id}
                          onClick={() => handleMarkNotificationRead(notif)}
                          className={`p-3.5 transition-colors cursor-pointer text-left space-y-1 ${
                            !notif.is_read
                              ? 'bg-blue-50/60 dark:bg-blue-950/30 hover:bg-blue-100/50 dark:hover:bg-blue-900/40'
                              : 'hover:bg-slate-50/60 dark:hover:bg-slate-950/40 opacity-80'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className={`text-xs ${!notif.is_read ? 'font-black text-slate-900 dark:text-slate-100' : 'font-bold text-slate-700 dark:text-slate-300'}`}>
                              {notif.title}
                            </span>
                            {!notif.is_read && (
                              <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0 mt-1" />
                            )}
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-350 leading-snug">
                            {notif.message}
                          </p>
                          <span className="text-[9px] text-slate-400 font-bold block uppercase tracking-wider pt-0.5">
                            {formatTimeAgo(notif.timestamp)}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => { setIsProfileOpen(!isProfileOpen); setIsNotificationOpen(false); }}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-xl border transition-all duration-200 cursor-pointer ${
                  isProfileOpen 
                    ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900' 
                    : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-850'
                }`}
                aria-label="User Profile"
              >
                <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center font-black text-xs text-blue-700 dark:text-blue-300">
                  {userName.split(' ').map(n => n[0]).join('')}
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-xs font-black text-slate-900 dark:text-slate-100 leading-none">{userName}</p>
                  <p className="text-[9px] text-slate-400 dark:text-slate-500 font-extrabold mt-1 leading-none uppercase">{userRole}</p>
                </div>
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-lg z-50 overflow-hidden p-2 text-left space-y-1">
                  <div className="px-3 py-1.5 text-[9px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider border-b border-slate-50 dark:border-slate-800">Session Details</div>
                  {user?.npi && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">Reg No: {user.npi}</div>}
                  {user?.deviceId && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">Dev: {user.deviceId}</div>}
                  {user?.patientId && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">Pat: {user.patientId}</div>}
                  {user?.agencyId && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">Agency: {user.agencyId}</div>}
                  {user?.accessKey && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">Key: {user.accessKey}</div>}
                  <div className="h-px bg-slate-100 dark:bg-slate-800 my-1" />
                  <button onClick={handleLogout} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 text-xs font-black border-none bg-transparent cursor-pointer text-left">
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Dynamic Isolated Page Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
