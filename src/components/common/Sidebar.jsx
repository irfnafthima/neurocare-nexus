import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Activity, 
  Users, 
  AlertTriangle, 
  FileText, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  X,
  Hospital,
  Cpu,
  ShieldAlert,
  ScrollText,
  KeyRound,
  Sun,
  Moon,
  Monitor
} from 'lucide-react';

/**
 * Sidebar navigation drawer for Dashboard panel.
 * Filters menu items based on the user role and features a global theme switcher.
 */
export const Sidebar = ({ 
  activeTab, 
  setActiveTab, 
  isCollapsed, 
  setIsCollapsed,
  isOpenMobile,
  onCloseMobile,
  role = 'doctor'
}) => {
  const cleanRole = typeof role === 'string' ? role.toLowerCase() : 'doctor';

  // Theme state: 'light' | 'dark' | 'system'
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('nexus_theme') || 'system';
  });

  // Apply theme to document element
  useEffect(() => {
    const root = window.document.documentElement;
    const applyTheme = (t) => {
      root.classList.remove('light', 'dark');
      if (t === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        root.classList.add(systemTheme);
      } else {
        root.classList.add(t);
      }
    };

    applyTheme(theme);
    localStorage.setItem('nexus_theme', theme);

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const listener = (e) => {
        root.classList.remove('light', 'dark');
        root.classList.add(e.matches ? 'dark' : 'light');
      };
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, [theme]);

  // Get menu items based on user role
  const getMenuItems = () => {
    switch (cleanRole) {
      case 'admin':
        return [
          { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
          { name: 'Hospitals', icon: <Hospital className="w-5 h-5" /> },
          { name: 'Devices', icon: <Cpu className="w-5 h-5" /> },
          { name: 'Users', icon: <KeyRound className="w-5 h-5" /> },
          { name: 'Audit Logs', icon: <ScrollText className="w-5 h-5" /> },
          { name: 'Settings', icon: <Settings className="w-5 h-5" /> },
        ];
      case 'patient':
        return [
          { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
          { name: 'My Vitals', icon: <Activity className="w-5 h-5" /> },
          { name: 'Prescriptions', icon: <FileText className="w-5 h-5" /> },
          { name: 'Settings', icon: <Settings className="w-5 h-5" /> },
        ];
      case 'family':
        return [
          { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
          { name: 'Relative Vitals', icon: <Activity className="w-5 h-5" /> },
          { name: 'Prescriptions', icon: <FileText className="w-5 h-5" /> },
          { name: 'Settings', icon: <Settings className="w-5 h-5" /> },
        ];
      case 'doctor':
      case 'caregiver':
      default:
        return [
          { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
          { name: 'Live Monitoring', icon: <Activity className="w-5 h-5" /> },
          { name: 'Patients', icon: <Users className="w-5 h-5" /> },
          { name: 'Alerts', icon: <AlertTriangle className="w-5 h-5" /> },
          { name: 'Reports', icon: <FileText className="w-5 h-5" /> },
          { name: 'Settings', icon: <Settings className="w-5 h-5" /> },
        ];
    }
  };

  const menuItems = getMenuItems();
  const isAdmin = cleanRole === 'admin';

  const sidebarContent = (
    <div className={`flex flex-col h-full border-r select-none ${
      isAdmin 
        ? 'bg-slate-950 border-slate-800 text-slate-200' 
        : 'bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-800 dark:text-slate-200'
    }`}>
      {/* Header */}
      <div className={`flex items-center justify-between h-16 px-4 border-b ${
        isAdmin ? 'border-slate-800' : 'border-slate-100 dark:border-slate-850'
      }`}>
        {!isCollapsed && (
          isAdmin ? (
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-red-900/60 border border-red-700 flex items-center justify-center animate-pulse">
                <ShieldAlert className="w-3 h-3 text-red-400" />
              </div>
              <span className="text-[10px] font-extrabold tracking-widest text-red-400 uppercase">Secure Admin</span>
            </div>
          ) : (
            <span className="text-xs font-black tracking-widest text-blue-600 dark:text-blue-400 uppercase">Nexus Portal</span>
          )
        )}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)} 
          className={`hidden md:flex p-1.5 rounded-lg transition-colors ml-auto border-none bg-transparent cursor-pointer ${
            isAdmin 
              ? 'hover:bg-slate-800 text-slate-500 hover:text-slate-300' 
              : 'hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
          aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
        <button 
          onClick={onCloseMobile}
          className={`md:hidden p-1.5 rounded-lg border-none bg-transparent cursor-pointer ${
            isAdmin ? 'hover:bg-slate-800 text-slate-500' : 'hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-400'
          }`}
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = activeTab === item.name;
          return (
            <button
              key={item.name}
              onClick={() => {
                setActiveTab(item.name);
                if (onCloseMobile) onCloseMobile();
              }}
              className={`
                w-full flex items-center gap-3.5 px-3 py-2.5 rounded-lg font-bold text-xs tracking-wider uppercase transition-all duration-200 border-none cursor-pointer
                ${isAdmin
                  ? isActive
                    ? 'bg-red-900/30 text-red-400 border-l-4 border-red-500 pl-2'
                    : 'text-slate-500 hover:bg-slate-800 hover:text-slate-200 bg-transparent'
                  : isActive
                    ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 border-l-4 border-blue-600 pl-2'
                    : 'text-slate-650 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-slate-200 bg-transparent'
                }
              `}
              title={isCollapsed ? item.name : ''}
            >
              <span className={isAdmin ? (isActive ? 'text-red-400' : 'text-slate-600') : (isActive ? 'text-blue-600' : 'text-slate-450 dark:text-slate-500')}>
                {item.icon}
              </span>
              {!isCollapsed && <span>{item.name}</span>}
            </button>
          );
        })}
      </nav>

      {/* Theme Switcher Footer widget */}
      <div className={`p-3 border-t ${isAdmin ? 'border-slate-800' : 'border-slate-100 dark:border-slate-850'}`}>
        {isCollapsed ? (
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light')}
            className={`w-10 h-10 mx-auto rounded-xl flex items-center justify-center transition-colors cursor-pointer border-none bg-transparent ${
              isAdmin ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-500'
            }`}
            title={`Active Theme: ${theme.toUpperCase()}`}
          >
            {theme === 'light' && <Sun className="w-5 h-5 text-amber-500" />}
            {theme === 'dark' && <Moon className="w-5 h-5 text-indigo-400" />}
            {theme === 'system' && <Monitor className="w-5 h-5 text-slate-400" />}
          </button>
        ) : (
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest text-left pl-1">Theme Config</span>
            <div className={`grid grid-cols-3 p-1 rounded-xl border ${
              isAdmin 
                ? 'bg-slate-900/50 border-slate-850' 
                : 'bg-slate-50 dark:bg-slate-900 border-slate-200/60 dark:border-slate-800'
            }`}>
              {[
                { id: 'light', icon: Sun, label: 'Light' },
                { id: 'dark', icon: Moon, label: 'Dark' },
                { id: 'system', icon: Monitor, label: 'Sys' }
              ].map((t) => {
                const Icon = t.icon;
                const isSelected = theme === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={`py-1.5 flex flex-col items-center justify-center rounded-lg cursor-pointer border-none transition-all duration-150 ${
                      isSelected
                        ? isAdmin
                          ? 'bg-red-950 text-red-400 shadow-sm border border-red-900/50'
                          : 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200/50 dark:border-slate-700/50'
                        : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 bg-transparent'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span className="text-[8px] font-extrabold mt-0.5">{t.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      <div 
        className={`
          fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300 md:hidden
          ${isOpenMobile ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
        `}
        onClick={onCloseMobile}
      />
      <div 
        className={`
          fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out md:hidden
          ${isOpenMobile ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {sidebarContent}
      </div>

      <aside 
        className={`
          hidden md:block transition-all duration-300 shrink-0 h-screen sticky top-0
          ${isCollapsed ? 'w-20' : 'w-64'}
        `}
      >
        {sidebarContent}
      </aside>
    </>
  );
};

export default Sidebar;
