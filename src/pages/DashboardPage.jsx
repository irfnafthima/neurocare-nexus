import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import Sidebar from '../components/common/Sidebar';
import StatCard from '../components/dashboard/StatCard';
import ChartPlaceholder from '../components/dashboard/ChartPlaceholder';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import { 
  mockPatients, 
  mockHospitals, 
  mockDevices, 
  mockAccessList, 
  seedAuditLogs, 
  seedAlarms 
} from '../data/mockData';
import { 
  Bell, 
  LogOut, 
  Activity, 
  Users, 
  AlertTriangle, 
  Cpu, 
  Heart,
  TrendingUp,
  ShieldCheck,
  Check,
  Sparkles,
  Pill,
  Search,
  Settings as SettingsIcon,
  Wifi,
  Battery,
  Database,
  Radio,
  FileText,
  UserCheck,
  Menu
} from 'lucide-react';

export const DashboardPage = () => {
  const { user, logout, authFetch } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'doctor';
  const userName = user?.name || 'Dr. Jane Doe';

  // React state databases representing active streams
  const [patients, setPatients] = useState(mockPatients);
  const [alarms, setAlarms] = useState(seedAlarms);
  const [auditLogs, setAuditLogs] = useState(seedAuditLogs);
  const [devices, setDevices] = useState(mockDevices);
  const [adminStats, setAdminStats] = useState({
    totalPatients: 0,
    totalClinicians: 1,
    totalDevices: 6,
    criticalAlarms: 0
  });

  const [doctorsList, setDoctorsList] = useState([]);
  const [viewAllPatients, setViewAllPatients] = useState(false);
  const [adminUsers, setAdminUsers] = useState([]);

  // Active navigation settings
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Telemetry filters
  const [searchQuery, setSearchQuery] = useState('');

  // Derive the initial patient ID from the logged-in user's role:
  //   - 'patient': use deviceId, converting NP-XXX prefix → P-XXX
  //   - 'family':  use patientId directly (already in P-XXX format)
  //   - other roles: default to 'P-102' (doctor/admin selects via UI)
  const deriveInitialPatientId = () => {
    if (userRole === 'patient' && user?.deviceId) {
      return user.deviceId.replace(/^NP-/i, 'P-');
    }
    if (userRole === 'family' && user?.patientId) {
      return user.patientId;
    }
    return 'P-102';
  };

  const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId);
  const [activeAlarmFilter, setActiveAlarmFilter] = useState('all');

  // Input states
  const [clinicalNoteInput, setClinicalNoteInput] = useState('');
  const [patientNotesMap, setPatientNotesMap] = useState({
    'P-102': 'Patient stable. MAX30102 shows healthy BPM. No postural issues.',
    'P-204': 'Patient monitoring closely. Arrhythmia noted.',
    'P-108': 'Mild temperature elevation. Temp tracking active.'
  });

  const [settingsForm, setSettingsForm] = useState({
    minSpo2: '92',
    maxHR: '125',
    maxTemp: '38.5',
    alertSms: true,
    alertEmail: true
  });

  // Track active diagnostic updates (simulated EHR sync timer)
  const [ehrSyncTime, setEhrSyncTime] = useState('Just Now');

  // Load telemetry data from backend on mount and configure polling
  useEffect(() => {
    if (!user?.token) return;

    const fetchData = async () => {
      try {
        // 1. Fetch patients (with NPI filter if doctor & not viewing all)
        let patientsUrl = 'http://localhost:5000/api/patients';
        if (userRole === 'doctor' && user.npi && !viewAllPatients) {
          patientsUrl += `?doctorNpi=${user.npi}`;
        }
        const resPatients = await authFetch(patientsUrl);
        if (resPatients.ok) {
          const data = await resPatients.json();
          setPatients(data);
        }

        // 2. Fetch care notes
        const resNotes = await authFetch('http://localhost:5000/api/patients/notes');
        if (resNotes.ok) {
          const notesData = await resNotes.json();
          setPatientNotesMap(notesData);
        }

        // 3. Fetch audit logs
        const resLogs = await authFetch('http://localhost:5000/api/audit-logs');
        if (resLogs.ok) {
          const logsData = await resLogs.json();
          setAuditLogs(logsData);
        }

        // 4. Fetch admin stats
        if (userRole === 'admin') {
          const resStats = await authFetch('http://localhost:5000/api/admin/stats');
          if (resStats.ok) {
            const stats = await resStats.json();
            setAdminStats(stats);
          }

          // Fetch all users list for admin
          const resUsers = await authFetch('http://localhost:5000/api/admin/users');
          if (resUsers.ok) {
            const usersData = await resUsers.json();
            setAdminUsers(usersData);
          }
        }

        // 5. Fetch verified doctors list for patient
        if (userRole === 'patient') {
          const resDocs = await authFetch('http://localhost:5000/api/doctors');
          if (resDocs.ok) {
            const docsData = await resDocs.json();
            setDoctorsList(docsData);
          }
        }

      } catch (error) {
        console.error('Error fetching clinical registry database:', error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 4000); // 4s active polling
    return () => clearInterval(interval);
  }, [userRole, user?.token, user?.npi, viewAllPatients]);

  // Sync tab when userRole changes
  useEffect(() => {
    setActiveTab('Dashboard');
  }, [userRole]);

  // Helper: Commit a new log entry to PostgreSQL audit log
  const addAuditLog = async (action, target) => {
    try {
      await authFetch('http://localhost:5000/api/audit-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: userName, action, target })
      });
      
      const resLogs = await authFetch('http://localhost:5000/api/audit-logs');
      if (resLogs.ok) {
        const logsData = await resLogs.json();
        setAuditLogs(logsData);
      }
    } catch (error) {
      console.error('Failed to commit compliance audit log:', error);
    }
  };

  const handleTabChange = (tabName) => {
    setActiveTab(tabName);
    addAuditLog(`Navigated to ${tabName} tab`, 'Oversight Console');
  };

  const handleLogout = () => {
    addAuditLog('User Session Terminated', 'Security Auth Portal');
    logout();
    addToast('Logged out successfully.', 'info');
    navigate('/');
  };

  // -------------------------------------------------------------
  // SIMULATION ACTIONS (PostgreSQL Telemetry Ingestion)
  // -------------------------------------------------------------
  const triggerTelemetrySimulation = async (vitalsPatch, riskScore, statusState, auditAction) => {
    const baseVitals = selectedPatientObj.vitals;
    const payload = {
      patientId: selectedPatientId,
      riskScore,
      statusState,
      auditAction,
      userName,
      vitals: {
        max30102: {
          heartRate: vitalsPatch.heartRate !== undefined ? vitalsPatch.heartRate : baseVitals.max30102.heartRate,
          spo2: vitalsPatch.spo2 !== undefined ? vitalsPatch.spo2 : baseVitals.max30102.spo2
        },
        ds18b20: {
          temperature: vitalsPatch.temperature !== undefined ? vitalsPatch.temperature : baseVitals.ds18b20.temperature
        },
        mpu6050: {
          accelX: vitalsPatch.accelX !== undefined ? vitalsPatch.accelX : baseVitals.mpu6050.accelX,
          accelY: vitalsPatch.accelY !== undefined ? vitalsPatch.accelY : baseVitals.mpu6050.accelY,
          accelZ: vitalsPatch.accelZ !== undefined ? vitalsPatch.accelZ : baseVitals.mpu6050.accelZ,
          gyroX: vitalsPatch.gyroX !== undefined ? vitalsPatch.gyroX : baseVitals.mpu6050.gyroX,
          gyroY: vitalsPatch.gyroY !== undefined ? vitalsPatch.gyroY : baseVitals.mpu6050.gyroY,
          gyroZ: vitalsPatch.gyroZ !== undefined ? vitalsPatch.gyroZ : baseVitals.mpu6050.gyroZ,
          fallDetected: vitalsPatch.fallDetected !== undefined ? vitalsPatch.fallDetected : baseVitals.mpu6050.fallDetected
        },
        esp32: {
          connected: vitalsPatch.esp32Connected !== undefined ? vitalsPatch.esp32Connected : baseVitals.esp32.connected,
          battery: vitalsPatch.esp32Battery !== undefined ? vitalsPatch.esp32Battery : baseVitals.esp32.battery,
          rssi: vitalsPatch.esp32Rssi !== undefined ? vitalsPatch.esp32Rssi : baseVitals.esp32.rssi
        }
      }
    };

    try {
      const res = await authFetch('http://localhost:5000/api/simulation/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        let patientsUrl = 'http://localhost:5000/api/patients';
        if (userRole === 'doctor' && user.npi && !viewAllPatients) {
          patientsUrl += `?doctorNpi=${user.npi}`;
        }
        const resPatients = await authFetch(patientsUrl);
        if (resPatients.ok) {
          const data = await resPatients.json();
          setPatients(data);
        }
      }
    } catch (error) {
      console.error('Failed to trigger telemetry simulation:', error);
    }
  };

  const simulateNormal = () => {
    triggerTelemetrySimulation(
      { heartRate: 72, spo2: 98, temperature: 36.8, fallDetected: false, esp32Connected: true },
      10,
      'Normal',
      'Clinical telemetry normalized'
    );
    addToast('Patient telemetry normalized.', 'success');
  };

  const simulateFall = () => {
    triggerTelemetrySimulation(
      { heartRate: 110, fallDetected: true },
      95,
      'Emergency',
      'MPU6050 Fall Vector Alert Triggered'
    );

    const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
    const newAlarm = {
      id: Date.now(),
      type: 'critical',
      desc: `MPU6050: Accel vector spike detected. Fall event registered for ${pName}.`,
      time: 'Just Now',
      patient: pName,
      isCritical: true
    };
    setAlarms(prev => [newAlarm, ...prev]);
    addToast(`EMERGENCY: Fall detected for ${pName}!`, 'error');
  };

  const simulateHypoxia = () => {
    triggerTelemetrySimulation(
      { spo2: 84 },
      80,
      'Critical',
      'MAX30102 Low SpO2 Alarm Triggered'
    );

    const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
    const newAlarm = {
      id: Date.now(),
      type: 'critical',
      desc: `MAX30102: SpO2 oxygen saturation dropped to 84% for ${pName}.`,
      time: 'Just Now',
      patient: pName,
      isCritical: true
    };
    setAlarms(prev => [newAlarm, ...prev]);
    addToast(`WARNING: Low oxygen saturation for ${pName}!`, 'error');
  };

  const simulateFever = () => {
    triggerTelemetrySimulation(
      { temperature: 39.1 },
      50,
      'Warning',
      'DS18B20 High Temperature Logged'
    );

    const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
    const newAlarm = {
      id: Date.now(),
      type: 'warning',
      desc: `DS18B20: Elevated body temperature (39.1°C) registered for ${pName}.`,
      time: 'Just Now',
      patient: pName,
      isCritical: false
    };
    setAlarms(prev => [newAlarm, ...prev]);
    addToast(`Warning: High temperature for ${pName}.`, 'warning');
  };

  const simulateESP32Disconnect = () => {
    triggerTelemetrySimulation(
      { esp32Connected: false },
      selectedPatientObj.risk,
      selectedPatientObj.status,
      'ESP32 Node Disconnect Flagged'
    );

    const pName = selectedPatientObj ? selectedPatientObj.name : selectedPatientId;
    const newAlarm = {
      id: Date.now(),
      type: 'warning',
      desc: `ESP32: Wireless connection lost for ${pName}'s NeuroPatch wearable.`,
      time: 'Just Now',
      patient: pName,
      isCritical: false
    };
    setAlarms(prev => [newAlarm, ...prev]);
    addToast(`Warning: ESP32 node disconnected for ${pName}!`, 'warning');
  };

  // -------------------------------------------------------------
  // DATA OPERATIONS (PostgreSQL EHR sync)
  // -------------------------------------------------------------
  const saveClinicalNotes = async () => {
    if (!clinicalNoteInput.trim()) return;
    try {
      const res = await authFetch(`http://localhost:5000/api/patients/${selectedPatientId}/notes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: clinicalNoteInput, clinicianName: userName })
      });

      if (res.ok) {
        setPatientNotesMap(prev => ({
          ...prev,
          [selectedPatientId]: clinicalNoteInput
        }));
        setClinicalNoteInput('');
        addToast('EHR care notes synced successfully.', 'success');
      }
    } catch (error) {
      console.error('Failed to sync EHR clinical notes:', error);
      addToast('Connection failed: EHR records not synced.', 'error');
    }
  };

  const handleUpdateDoctor = async (doctorNpi) => {
    try {
      const res = await authFetch(`http://localhost:5000/api/patients/${selectedPatientId}/doctor`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctorNpi, clinicianName: userName })
      });

      if (res.ok) {
        addToast(doctorNpi ? 'Successfully associated with consulting doctor!' : 'De-associated from doctor.', 'success');
        
        // Re-fetch patients list to update local state
        let patientsUrl = 'http://localhost:5000/api/patients';
        if (userRole === 'doctor' && user.npi && !viewAllPatients) {
          patientsUrl += `?doctorNpi=${user.npi}`;
        }
        const resPatients = await authFetch(patientsUrl);
        if (resPatients.ok) {
          const data = await resPatients.json();
          setPatients(data);
        }
      }
    } catch (error) {
      console.error('Failed to link consulting doctor:', error);
      addToast('Connection failed: Doctor association not synced.', 'error');
    }
  };

  const syncExternalEhr = () => {
    setEhrSyncTime('Loading...');
    setTimeout(() => {
      setEhrSyncTime('Just Now');
      addToast('External Health Record Sync completed (Simulated).', 'success');
      addAuditLog('Initiated External Health Record synchronization (Simulated)', 'EHR Sync Endpoint');
    }, 1000);
  };

  const handleSaveSettings = (e) => {
    e.preventDefault();
    addToast('Global clinical thresholds saved.', 'success');
    addAuditLog('Modified Global Compliance Thresholds', 'Platform Configurations');
  };

  const revokeAccess = async (userId, userNameStr, userRoleStr) => {
    try {
      const res = await authFetch(`http://localhost:5000/api/admin/users/${userId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        addToast(`Successfully revoked access for ${userNameStr} [${userRoleStr.toUpperCase()}].`, 'success');
        
        // Re-fetch users
        const resUsers = await authFetch('http://localhost:5000/api/admin/users');
        if (resUsers.ok) {
          const data = await resUsers.json();
          setAdminUsers(data);
        }
      }
    } catch (error) {
      console.error('Failed to revoke access:', error);
      addToast('Connection failed: User access not revoked.', 'error');
    }
  };

  // -------------------------------------------------------------
  // FILTERS AND COMPUTED VALUES
  // -------------------------------------------------------------
  // Sort patients by risk DESCENDING (Clinical standard prioritizing high-risk)
  const sortedPatients = [...patients].sort((a, b) => b.risk - a.risk);

  const filteredPatients = sortedPatients.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.condition.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Guard against empty patients array (e.g. API failure before mock hydrates)
  const selectedPatientObj = patients.length > 0
    ? (patients.find(p => p.id === selectedPatientId) || patients[0])
    : null;

  const filteredAlarms = alarms.filter(a => {
    if (activeAlarmFilter === 'critical') return a.isCritical;
    if (activeAlarmFilter === 'warning') return !a.isCritical && a.type !== 'normal';
    return true;
  });

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-sans" style={{ fontFamily: "'Inter', sans-serif" }}>
      
      {/* Sidebar - Dynamically configured per role */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={handleTabChange}
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
                onClick={() => { setIsNotificationOpen(!isNotificationOpen); setIsProfileOpen(false); }}
                className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all duration-200 relative cursor-pointer ${
                  isNotificationOpen 
                    ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900 text-blue-650 dark:text-blue-400' 
                    : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400'
                }`}
              >
                <Bell className="w-[18px] h-[18px]" />
                {alarms.some(a => a.type === 'critical' || a.type === 'warning') && (
                  <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
                )}
              </button>

              {isNotificationOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-lg z-50 overflow-hidden text-left">
                  <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 font-black text-xs text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                    Notifications Log
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {alarms.slice(0, 5).map(alarm => (
                      <div key={alarm.id} className="p-3.5 border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-900/50 text-[11px] font-semibold text-slate-700 dark:text-slate-350">
                        <p>{alarm.desc}</p>
                        <span className="text-[9px] text-slate-455 dark:text-slate-500 font-black mt-1 block uppercase">{alarm.time}</span>
                      </div>
                    ))}
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
                  {user?.npi && <div className="px-3 py-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">NPI: {user.npi}</div>}
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

        {/* Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Greeting panel with slogan space */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-6 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-left">
            <div>
              <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight">
                {userRole === 'admin' && 'Administrator Operations Center'}
                {userRole === 'doctor' && `Welcome, ${userName}`}
                {userRole === 'caregiver' && `Operational Portal: ${userName}`}
                {userRole === 'patient' && `Hello, ${userName}`}
                {userRole === 'family' && `Welcome Back, ${userName}`}
              </h1>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-455 mt-1 leading-relaxed">
                {userRole === 'admin' && 'Monitoring secure system integration nodes, device diagnostics, and root HIPAA audit logs.'}
                {userRole === 'doctor' && 'Monitoring medical telemetry inputs & physical hardware diagnostics.'}
                {userRole === 'caregiver' && 'Coordinating clinical checkups & telemetry patient logs.'}
                {userRole === 'patient' && 'NeuroCare is monitoring your health securely. Slogan: We are with you always.'}
                {userRole === 'family' && 'Active health status for Sarah Johnson (Bed 102). Slogan: Care that never sleeps.'}
              </p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 px-3.5 py-1.5 rounded-full inline-flex items-center gap-1.5 self-start text-xs font-black text-blue-700 dark:text-blue-300 select-none">
              <Sparkles className="w-3.5 h-3.5" />
              <span>System Core Active</span>
            </div>
          </div>

          {/* ==================== ROOT ADMIN DASHBOARD ==================== */}
          {userRole === 'admin' && (
            <>
              {activeTab === 'Dashboard' && (
                <>
                  {/* Stats grids */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-left">
                    <StatCard title="Total Connected Patients" icon={<Users className="w-5 h-5 text-blue-500" />} value={adminStats.totalPatients.toString()} trend="Active" trendLabel="in local database" />
                    <StatCard title="Attending Clinicians" icon={<UserCheck className="w-5 h-5 text-purple-500" />} value={adminStats.totalClinicians.toString()} trend="Active" trendLabel="verified credentials" />
                    <StatCard title="IoT Wearables Inventory" icon={<Cpu className="w-5 h-5 text-emerald-500" />} value={adminStats.totalDevices.toString()} trend="Pre-registered" trendLabel="NPPES linked" />
                    <StatCard title="Critical Alarms Dispatch" icon={<AlertTriangle className="w-5 h-5 text-red-500" />} value={adminStats.criticalAlarms.toString()} trend="Active" trendLabel="HIPAA strict audit" />
                  </div>

                  {/* Diagnostic logs */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card title="System Node Diagnostics" subtitle="Active pings from hardware integration servers">
                      <div className="space-y-3.5 mt-4 text-left text-xs font-black text-slate-700 dark:text-slate-300">
                        {[
                          { node: 'ECG Pulse Processor Node #1', ping: '12ms', status: 'Operational' },
                          { node: 'External Health Record Sync Webhook (Simulated)', ping: '45ms', status: 'Operational' },
                          { node: 'HL7 Medical Legacy Broker Service', ping: '110ms', status: 'Operational' },
                          { node: 'ESP32 Device Encryption Key Rotator', status: 'Rotated 2h ago' }
                        ].map((node, i) => (
                          <div key={i} className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800 rounded-xl flex justify-between">
                            <span>💻 {node.node}</span>
                            <span className="text-emerald-500 dark:text-emerald-400 font-extrabold text-[10px] uppercase">{node.ping || node.status}</span>
                          </div>
                        ))}
                      </div>
                    </Card>

                    <Card title="Platform Actions Audit" subtitle="Automatic pings from platform actions logs">
                      <div className="space-y-3.5 mt-4 text-left text-xs font-black text-slate-700 dark:text-slate-350">
                        {auditLogs.slice(0, 3).map((a, i) => (
                          <div key={i} className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800 rounded-xl flex justify-between items-center">
                            <span className="truncate pr-2">🔑 {a.user}: {a.action}</span>
                            <span className="text-slate-455 dark:text-slate-500 text-[10px] shrink-0 ml-2">{a.time}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  </div>
                </>
              )}

              {/* Hospitals connected directory tab */}
              {activeTab === 'Hospitals' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm text-left">
                  <div className="p-5 border-b border-slate-100 dark:border-slate-800">
                    <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Hospital Nodes Directory</h2>
                    <p className="text-xs text-slate-455 dark:text-slate-500 mt-1 font-semibold">Active clinical integrations and users statistics</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-xs md:text-sm">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                          <th className="py-4 px-6">ID</th>
                          <th className="py-4 px-6">Hospital Facility</th>
                          <th className="py-4 px-6">Location</th>
                          <th className="py-4 px-6">EHR System type</th>
                          <th className="py-4 px-6 text-center">Active Physicians</th>
                          <th className="py-4 px-6">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-350">
                        {mockHospitals.map((h, i) => (
                          <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                            <td className="py-4 px-6 font-mono text-slate-400 dark:text-slate-500 font-bold">{h.id}</td>
                            <td className="py-4 px-6 font-black text-slate-950 dark:text-slate-100">{h.name}</td>
                            <td className="py-4 px-6">{h.location}</td>
                            <td className="py-4 px-6 font-mono text-slate-500 dark:text-slate-400">{h.systems}</td>
                            <td className="py-4 px-6 text-center text-blue-600 dark:text-blue-400 font-extrabold">{h.usersCount}</td>
                            <td className="py-4 px-6">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider ${
                                h.status.includes('Online') ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' : 'bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                              }`}>{h.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Devices inventory and diagnostics tab */}
              {activeTab === 'Devices' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm text-left">
                  <div className="p-5 border-b border-slate-100 dark:border-slate-800">
                    <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Wearables Hardware Inventory</h2>
                    <p className="text-xs text-slate-455 dark:text-slate-500 mt-1 font-semibold">ESP32 Device Status, Battery Level, and Wi-Fi RSSI</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-xs md:text-sm">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                          <th className="py-4 px-6">Device Serial (ESP32)</th>
                          <th className="py-4 px-6">Linked Patient</th>
                          <th className="py-4 px-6 text-center">Battery Level</th>
                          <th className="py-4 px-6 text-center">WiFi Signal (RSSI)</th>
                          <th className="py-4 px-6">Device Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-350">
                        {devices.map((d, i) => (
                          <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                            <td className="py-4 px-6 font-mono text-xs text-slate-950 dark:text-slate-200 font-extrabold">{d.id}</td>
                            <td className="py-4 px-6 text-slate-655 dark:text-slate-300 font-bold">{d.patient}</td>
                            <td className="py-4 px-6 text-center font-bold text-slate-900 dark:text-slate-100">
                              <span className="inline-flex items-center gap-1">
                                <Battery className="w-3.5 h-3.5 text-slate-400" /> {d.battery}
                              </span>
                            </td>
                            <td className="py-4 px-6 text-center font-mono text-slate-500 dark:text-slate-400">
                              <span className="inline-flex items-center gap-1">
                                <Wifi className="w-3.5 h-3.5 text-slate-400" /> {d.rssi}
                              </span>
                            </td>
                            <td className="py-4 px-6">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider ${
                                d.status === 'Synced' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400' : 'bg-red-50 dark:bg-red-950/20 text-red-655 dark:text-red-400'
                              }`}>{d.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* User management and directory tab */}
              {activeTab === 'Users' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm text-left">
                  <div className="p-5 border-b border-slate-100 dark:border-slate-800">
                    <h2 className="text-base font-black text-slate-950 dark:text-slate-50">User Accounts Directory</h2>
                    <p className="text-xs text-slate-455 dark:text-slate-500 mt-1 font-semibold">Administrate all registered clinical and patient profiles in the system.</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-xs md:text-sm">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                          <th className="py-4 px-6 text-left">User Name</th>
                          <th className="py-4 px-6 text-left">Email Address</th>
                          <th className="py-4 px-6 text-left">User Role</th>
                          <th className="py-4 px-6 text-left">Verification Key / ID</th>
                          <th className="py-4 px-6 text-left">Registered On</th>
                          <th className="py-4 px-6 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-350">
                        {adminUsers.map((u) => (
                          <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                            <td className="py-4 px-6 font-black text-slate-950 dark:text-slate-100">{u.fullName}</td>
                            <td className="py-4 px-6">{u.email}</td>
                            <td className="py-4 px-6">
                              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider ${
                                u.role === 'admin' ? 'bg-red-55/60 dark:bg-red-950/20 text-red-600 dark:text-red-400 border border-red-500/20' :
                                u.role === 'doctor' ? 'bg-blue-50 dark:bg-blue-950/20 text-blue-600 dark:text-blue-400 border border-blue-500/20' :
                                u.role === 'caregiver' ? 'bg-purple-50 dark:bg-purple-950/20 text-purple-600 dark:text-purple-400 border border-purple-500/20' :
                                u.role === 'patient' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                                'bg-slate-50 dark:bg-slate-950 text-slate-655 dark:text-slate-400 border border-slate-500/20'
                              }`}>{u.role}</span>
                            </td>
                            <td className="py-4 px-6 font-mono text-xs text-slate-500 dark:text-slate-455">
                              {u.role === 'admin' && `Key: ${u.accessKey}`}
                              {u.role === 'doctor' && `NPI: ${u.npi}`}
                              {u.role === 'caregiver' && `Agency: ${u.agencyId}`}
                              {u.role === 'patient' && `Device: ${u.deviceId}`}
                              {u.role === 'family' && `Patient: ${u.patientId}`}
                            </td>
                            <td className="py-4 px-6 text-slate-455 dark:text-slate-500 text-xs">
                              {new Date(u.createdAt).toLocaleDateString()}
                            </td>
                            <td className="py-4 px-6 text-center">
                              {u.role !== 'admin' ? (
                                <button 
                                  onClick={() => revokeAccess(u.id, u.fullName, u.role)} 
                                  className="px-3 py-1.5 bg-slate-50 dark:bg-slate-950 text-slate-655 dark:text-slate-350 hover:bg-red-50 dark:hover:bg-red-950/30 hover:text-red-600 dark:hover:text-red-400 border border-slate-250 dark:border-slate-800 rounded-xl cursor-pointer font-bold text-[10px] uppercase tracking-wider transition-colors"
                                >
                                  Revoke
                                </button>
                              ) : (
                                <span className="text-[10px] text-slate-400 dark:text-slate-600 uppercase tracking-widest font-black">Immutable</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* HIPAA audit logs tab */}
              {activeTab === 'Audit Logs' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm text-left">
                  <div className="p-5 border-b border-slate-100 dark:border-slate-800">
                    <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Security Audit Logs (HIPAA Compliance)</h2>
                    <p className="text-xs text-slate-455 dark:text-slate-500 mt-1 font-semibold">Strict audit logging tracking all active operations and data sync triggers</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-xs md:text-sm">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                          <th className="py-4 px-6">Audit ID</th>
                          <th className="py-4 px-6">Timestamp</th>
                          <th className="py-4 px-6">Access User</th>
                          <th className="py-4 px-6">Operation details</th>
                          <th className="py-4 px-6">Target Resource</th>
                          <th className="py-4 px-6">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-350">
                        {auditLogs.map((log, i) => (
                          <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                            <td className="py-4 px-6 font-mono text-xs text-slate-400 dark:text-slate-500 font-bold">{log.id}</td>
                            <td className="py-4 px-6 text-xs text-slate-500 dark:text-slate-400">{log.time}</td>
                            <td className="py-4 px-6 font-black text-slate-950 dark:text-slate-100">{log.user}</td>
                            <td className="py-4 px-6 text-slate-655 dark:text-slate-300 font-bold">{log.action}</td>
                            <td className="py-4 px-6 font-semibold text-slate-900 dark:text-slate-200">{log.target}</td>
                            <td className="py-4 px-6">
                              <span className="px-2.5 py-0.5 rounded-full text-[9px] bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-black uppercase tracking-wider">{log.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Admin settings */}
              {activeTab === 'Settings' && (
                <div className="max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-sm text-left space-y-4">
                  <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Platform Diagnostics Settings</h2>
                  <div className="space-y-3 font-semibold text-slate-650 dark:text-slate-455 text-xs">
                    <label className="flex items-center gap-2.5 cursor-pointer">
                      <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-slate-200 dark:border-slate-800 accent-blue-600" />
                      <span>Enforce strict NPI authentication domain validation filters</span>
                    </label>
                    <label className="flex items-center gap-2.5 cursor-pointer">
                      <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-slate-200 dark:border-slate-800 accent-blue-600" />
                      <span>Log all ESP32 device raw packets payload for 30 days retention</span>
                    </label>
                  </div>
                  <button onClick={() => addToast('Diagnostics settings updated.', 'success')} className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
                    Save Global Diagnostics Parameters
                  </button>
                </div>
              )}
            </>
          )}

          {/* ==================== CLINIC DOCTOR / CAREGIVER DASHBOARD ==================== */}
          {(userRole === 'doctor' || userRole === 'caregiver') && (
            <>
              {activeTab === 'Dashboard' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard title="Total Monitored" icon={<Users className="w-5 h-5 text-blue-500" />} value={patients.length.toString()} trend="Active" trendLabel="under clinic care" />
                    <StatCard title="Active Alarms" icon={<AlertTriangle className="w-5 h-5 text-red-500" />} value={alarms.length.toString()} trend="-3%" trendLabel="from yesterday" />
                    <StatCard title="Devices Online (ESP32)" icon={<Cpu className="w-5 h-5 text-emerald-500" />} value={patients.filter(p => p.vitals.esp32.connected).length.toString()} trend="100%" trendLabel="link quality stable" />
                    <StatCard title="EHR Synced Nodes" icon={<Database className="w-5 h-5 text-indigo-500" />} value="EHR Sync" trend="Active" trendLabel="simulated link" />
                  </div>
                  <ChartPlaceholder
                    heartRate={selectedPatientObj?.vitals?.max30102?.heartRate ?? null}
                    spo2={selectedPatientObj?.vitals?.max30102?.spo2 ?? null}
                  />

                  {/* Alarms Dashboard widget */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm text-left space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h2 className="text-base font-black text-slate-950 dark:text-slate-55">Active Alarms Log (Sensor-Driven)</h2>
                        <span className="text-[11px] text-slate-455 dark:text-slate-500 font-semibold block mt-0.5">Showing warnings triggered by MAX30102, DS18B20, or MPU6050</span>
                      </div>
                      <div className="flex gap-1.5 p-0.5 bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800 rounded-xl">
                        {['all', 'critical', 'warning'].map(filter => (
                          <button
                            key={filter}
                            onClick={() => setActiveAlarmFilter(filter)}
                            className={`px-3 py-1 text-[10px] font-black uppercase tracking-wider rounded-lg cursor-pointer border-none ${
                              activeAlarmFilter === filter 
                                ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200/40' 
                                : 'text-slate-400 dark:text-slate-500 hover:text-slate-700 bg-transparent'
                            }`}
                          >
                            {filter}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="divide-y divide-slate-100 dark:divide-slate-850 max-h-80 overflow-y-auto">
                      {filteredAlarms.map((a, i) => (
                        <div key={i} className="py-3.5 flex justify-between items-center">
                          <div>
                            <span className="text-[9px] text-slate-400 dark:text-slate-500 font-black block uppercase tracking-wider">{a.time} • Patient: {a.patient}</span>
                            <p className="text-xs font-bold text-slate-850 dark:text-slate-300 mt-1">{a.desc}</p>
                          </div>
                          <span className={`px-2.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider ${
                            a.isCritical ? 'bg-red-50 dark:bg-red-950/20 text-red-500 border border-red-500/20' : 'bg-amber-50 dark:bg-amber-950/20 text-amber-500 border border-amber-500/20'
                          }`}>
                            {a.isCritical ? 'CRITICAL' : 'WARNING'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* ICU Oversight grid */}
              {activeTab === 'Live Monitoring' && (
                <div className="space-y-6">
                  <div className="flex justify-between items-center text-left">
                    <div>
                      <h2 className="text-xl font-black text-slate-900 dark:text-slate-50 tracking-tight">ICU Multi-Patient Diagnostics</h2>
                      <span className="text-xs text-slate-455 dark:text-slate-500 font-semibold block mt-1">Real-time waveforms from MAX30102 cardios and MPU6050 movements</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {patients.map(pat => (
                      <div key={pat.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4 text-left">
                        <div className="flex justify-between items-center">
                          <div>
                            <h3 className="font-black text-slate-950 dark:text-slate-100 text-sm leading-none">{pat.name}</h3>
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-bold block mt-1.5 leading-none">Bed {pat.room} • {pat.condition}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: pat.color }} />
                            <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: pat.color }}>{pat.status}</span>
                          </div>
                        </div>

                        {/* Scrolling ECG waveform */}
                        <div className="rounded-xl p-3 bg-slate-950 relative overflow-hidden">
                          <div className="text-[8px] text-slate-500 font-black uppercase tracking-widest mb-1.5 select-none">MAX30102 Cardios • Lead II</div>
                          <svg className="w-full" viewBox="0 0 300 30" preserveAspectRatio="none" style={{ height: 26, color: pat.color }}>
                            <path d="M0 15 L25 15 L35 12 L40 2 L45 28 L50 15 L80 15 L95 12 L100 2 L105 28 L110 15 L140 15 L155 12 L160 2 L165 28 L170 15 L200 15 L215 12 L220 2 L225 28 L230 15 L260 15 L275 12 L280 2 L285 28 L290 15 L300 15"
                              stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                          </svg>
                        </div>

                        {/* Patient vitals */}
                        <div className="grid grid-cols-3 gap-2 text-center font-bold text-xs select-none">
                          <div className="bg-slate-50 dark:bg-slate-950 rounded-xl p-2.5">
                            <span className="text-[8px] text-slate-400 dark:text-slate-500 block uppercase tracking-wider font-black">MAX30102 HR</span>
                            <span className="text-red-500 font-black block mt-1">{pat.vitals.max30102.heartRate} BPM</span>
                          </div>
                          <div className="bg-slate-50 dark:bg-slate-950 rounded-xl p-2.5">
                            <span className="text-[8px] text-slate-400 dark:text-slate-500 block uppercase tracking-wider font-black">MAX30102 SpO2</span>
                            <span className="text-blue-600 dark:text-blue-400 font-black block mt-1">{pat.vitals.max30102.spo2}%</span>
                          </div>
                          <div className="bg-slate-50 dark:bg-slate-950 rounded-xl p-2.5">
                            <span className="text-[8px] text-slate-400 dark:text-slate-500 block uppercase tracking-wider font-black">DS18B20 TEMP</span>
                            <span className="text-amber-500 font-black block mt-1">{pat.vitals.ds18b20.temperature}°C</span>
                          </div>
                        </div>

                        <button 
                          onClick={() => { setSelectedPatientId(pat.id); setActiveTab('Patient Detail'); addAuditLog(`Opened Patient File`, pat.name); }}
                          className="w-full py-2 bg-slate-50 dark:bg-slate-950 hover:bg-blue-50 dark:hover:bg-slate-900 text-slate-655 dark:text-slate-350 hover:text-blue-600 dark:hover:text-blue-400 font-black text-[10px] uppercase tracking-wider rounded-xl border border-slate-250 dark:border-slate-800 hover:border-blue-200 transition-all cursor-pointer"
                        >
                          Open Patient Diagnostics
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Patient directory tab */}
              {activeTab === 'Patients' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm">
                  <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-left">
                    <div className="space-y-2">
                      <h2 className="text-base font-black text-slate-950 dark:text-slate-50 tracking-tight">Active Patients Registry</h2>
                      <p className="text-xs text-slate-455 dark:text-slate-500 font-semibold leading-none">
                        {userRole === 'doctor' 
                          ? (viewAllPatients ? 'Emergency Override: Showing all patients registered in the clinical database.' : 'Showing only patients assigned to your consulting NPI.')
                          : 'Priority sorted: high-risk patient nodes automatically display first.'
                        }
                      </p>
                      {userRole === 'doctor' && (
                        <label className="flex items-center gap-2 text-xs font-black text-slate-550 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800 px-3 py-1.5 rounded-xl cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors w-fit">
                          <input
                            type="checkbox"
                            checked={viewAllPatients}
                            onChange={(e) => {
                              const val = e.target.checked;
                              setViewAllPatients(val);
                              if (val) {
                                addAuditLog('Emergency Override: Requested All Patients Registry access', 'Clinical Patients Registry');
                                addToast('Viewing all clinical patients in registry (Emergency mode).', 'warning');
                              } else {
                                addAuditLog('Restored standard attending patients filter', 'Oversight Console');
                                addToast('ATTENDING FILTER: Restored consulting patients list.', 'info');
                              }
                            }}
                            className="w-4 h-4 rounded border-slate-200 dark:border-slate-800 accent-blue-600 cursor-pointer"
                          />
                          <span>Show All Registry Patients (Emergency Override)</span>
                        </label>
                      )}
                    </div>
                    <div className="relative max-w-xs w-full">
                      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input 
                        type="text" 
                        placeholder="Search diagnosis or name..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-slate-205 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-950 text-xs font-semibold focus:bg-white dark:focus:bg-slate-950 focus:border-blue-400 outline-none transition-colors text-slate-800 dark:text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-left text-xs md:text-sm">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-500 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850 tracking-wider">
                          <th className="py-4 px-6">ID</th>
                          <th className="py-4 px-6">Patient Name</th>
                          <th className="py-4 px-6">Demographics</th>
                          <th className="py-4 px-6">Primary Diagnosis</th>
                          <th className="py-4 px-6 text-center">MAX30102 HR</th>
                          <th className="py-4 px-6 text-center">MAX30102 SpO2</th>
                          <th className="py-4 px-6 text-center">MPU6050 Fall Alert</th>
                          <th className="py-4 px-6 text-center">Risk Factor</th>
                          <th className="py-4 px-6 text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-350">
                        {filteredPatients.map(pat => {
                          const isHighRisk = pat.risk >= 60;
                          return (
                            <tr key={pat.id} className={`transition-colors hover:bg-slate-50/50 dark:hover:bg-slate-950/50 ${isHighRisk ? 'bg-red-500/[0.02] dark:bg-red-500/[0.01]' : ''}`}>
                              <td className="py-4 px-6 font-mono text-slate-400 dark:text-slate-500 font-bold">{pat.id}</td>
                              <td className="py-4 px-6 font-black text-slate-950 dark:text-slate-100">{pat.name}</td>
                              <td className="py-4 px-6">{pat.age}y / {pat.gender}</td>
                              <td className="py-4 px-6 text-slate-600 dark:text-slate-400">{pat.condition}</td>
                              <td className="py-4 px-6 text-center font-bold text-red-500">{pat.vitals.max30102.heartRate} BPM</td>
                              <td className="py-4 px-6 text-center font-bold text-blue-600 dark:text-blue-400">{pat.vitals.max30102.spo2}%</td>
                              <td className="py-4 px-6 text-center">
                                <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${pat.vitals.mpu6050.fallDetected ? 'bg-red-100 dark:bg-red-950/30 text-red-655 dark:text-red-400 animate-pulse' : 'bg-slate-50 dark:bg-slate-950 text-slate-400'}`}>
                                  {pat.vitals.mpu6050.fallDetected ? 'Fall Alert' : 'No Fall'}
                                </span>
                              </td>
                              <td className="py-4 px-6 text-center">
                                <span className={`px-2.5 py-1 rounded-lg text-[10px] font-black ${
                                  pat.risk >= 70 
                                    ? 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 border border-red-500/20' 
                                    : pat.risk >= 40 
                                    ? 'bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-500/20' 
                                    : 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                                }`}>
                                  {pat.risk}%
                                </span>
                              </td>
                              <td className="py-4 px-6 text-center">
                                <button 
                                  onClick={() => { setSelectedPatientId(pat.id); setActiveTab('Patient Detail'); addAuditLog(`Opened Patient File`, pat.name); }}
                                  className="px-3.5 py-1.5 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/60 font-black text-[10px] uppercase tracking-wider rounded-xl border-none cursor-pointer transition-colors"
                                >
                                  Open
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ---- DOCTOR/CAREGIVER: Alerts tab ---- */}
              {activeTab === 'Alerts' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-sm text-left space-y-3">
                  <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Active Alarms Log</h2>
                  <p className="text-xs text-slate-455 dark:text-slate-500 font-semibold">Navigate to the Dashboard tab to view the full sensor-driven alarms panel.</p>
                </div>
              )}
              {activeTab === 'Patient Detail' && (

                <div className="space-y-6 text-left">
                  <div className="flex items-center justify-between">
                    <button 
                      onClick={() => setActiveTab('Patients')} 
                      className="text-xs font-black text-slate-500 dark:text-slate-455 hover:text-blue-600 dark:hover:text-blue-400 transition-colors bg-transparent border-none cursor-pointer uppercase tracking-wider"
                    >
                      ← Return to Registry
                    </button>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">Secure EHR Clinical Session</span>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                    
                    {/* Left Column (Anatomical Neurological Map with Hotspots) */}
                    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-5">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center font-black text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
                          {selectedPatientObj.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                          <h2 className="text-base font-black text-slate-950 dark:text-slate-100 leading-none">{selectedPatientObj.name}</h2>
                          <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500 block mt-1.5 leading-none">
                            Bed {selectedPatientObj.room} • Patient ID {selectedPatientObj.id}
                          </span>
                        </div>
                      </div>
                      <div className="h-px bg-slate-100 dark:bg-slate-800" />
                           {/* Stylized Neurological brain and spine SVG outline */}
                      <div className="relative border border-slate-100 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-950/30 rounded-2xl p-4 flex items-center justify-center h-80">
                        <svg className="w-full h-full max-h-72 opacity-95 dark:opacity-85 text-slate-355 dark:text-slate-700" viewBox="0 0 100 200" fill="none">
                          {/* Left Cerebral Hemisphere */}
                          <path d="M48 20 C42 20, 36 22, 33 26 C30 30, 27 35, 27 40 C27 45, 29 50, 32 54 C35 58, 38 60, 42 62 C45 63, 47 62, 48 60 Z" 
                            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                          {/* Right Cerebral Hemisphere */}
                          <path d="M52 20 C58 20, 64 22, 67 26 C70 30, 73 35, 73 40 C73 45, 71 50, 68 54 C65 58, 62 60, 58 62 C55 63, 53 62, 52 60 Z" 
                            stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                          
                          {/* Brain Internal Gyri / Fissures Details */}
                          <path d="M33 34 C36 32, 40 35, 43 35 M30 45 C35 44, 40 47, 45 42 M38 52 C42 49, 44 54, 46 54" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
                          <path d="M67 34 C64 32, 60 35, 57 35 M70 45 C65 44, 60 47, 55 42 M62 52 C58 49, 56 54, 54 54" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />

                          {/* Cerebellum Left */}
                          <path d="M35 62 C32 65, 32 72, 38 75 C42 77, 46 75, 48 70" stroke="currentColor" strokeWidth="1.8" />
                          {/* Cerebellum Right */}
                          <path d="M65 62 C68 65, 68 72, 62 75 C58 77, 54 75, 52 70" stroke="currentColor" strokeWidth="1.8" />
                          
                          {/* Spinal Cord (Dual line structure representing vertebrae column) */}
                          <line x1="47" y1="72" x2="47" y2="185" stroke="currentColor" strokeWidth="1.5" />
                          <line x1="53" y1="72" x2="53" y2="185" stroke="currentColor" strokeWidth="1.5" />
                          
                          {/* Vertebrae segments horizontal ribs */}
                          <path d="M47 85 L53 85 M47 98 L53 98 M47 111 L53 111 M47 124 L53 124 M47 137 L53 137 M47 150 L53 150 M47 163 L53 163 M47 176 L53 176" 
                            stroke="currentColor" strokeWidth="1.2" opacity="0.75" />

                          {/* Spinal Nerve Root Branches extending symmetrically */}
                          <path d="M47 80 C36 82, 26 86, 20 92 M53 80 C64 82, 74 86, 80 92" stroke="currentColor" strokeWidth="1.2" opacity="0.8" />
                          <path d="M47 105 C33 110, 24 117, 18 126 M53 105 C67 110, 76 117, 82 126" stroke="currentColor" strokeWidth="1.2" opacity="0.8" />
                          <path d="M47 130 C30 137, 22 146, 16 158 M53 130 C70 137, 78 146, 84 158" stroke="currentColor" strokeWidth="1.2" opacity="0.8" />
                          <path d="M47 155 C28 163, 19 174, 15 188 M53 155 C72 163, 81 174, 85 188" stroke="currentColor" strokeWidth="1.2" opacity="0.8" />
                        </svg>

                        {/* Interactive Sensor Hotspots */}
                        {/* Hotspot 1: MPU6050 Gyro (Head/Brain) */}
                        <div className="absolute top-[28%] left-[50%] -translate-x-1/2 -translate-y-1/2 group">
                          <span className="absolute -inset-2.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 animate-ping pointer-events-none" />
                          <div className="w-3.5 h-3.5 rounded-full bg-indigo-600 border border-white cursor-pointer shadow relative z-10" />
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-5 hidden group-hover:block bg-slate-950 text-white font-extrabold text-[9px] p-2 rounded-lg whitespace-nowrap shadow-xl z-20 border border-slate-800">
                            MPU6050 Gyro: {selectedPatientObj.vitals.mpu6050.gyroX.toFixed(1)}°/s
                          </div>
                        </div>

                        {/* Hotspot 2: DS18B20 Temp (Neck/Core) */}
                        <div className="absolute top-[48%] left-[50%] -translate-x-1/2 -translate-y-1/2 group">
                          <span className="absolute -inset-2.5 rounded-full bg-amber-500/20 border border-amber-500/40 animate-ping pointer-events-none" />
                          <div className="w-3.5 h-3.5 rounded-full bg-amber-500 border border-white cursor-pointer shadow relative z-10" />
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-5 hidden group-hover:block bg-slate-950 text-white font-extrabold text-[9px] p-2 rounded-lg whitespace-nowrap shadow-xl z-20 border border-slate-800">
                            DS18B20 Temp: {selectedPatientObj.vitals.ds18b20.temperature}°C
                          </div>
                        </div>

                        {/* Hotspot 3: MPU6050 Accel / Fall (Hip/Core) */}
                        <div className="absolute top-[68%] left-[50%] -translate-x-1/2 -translate-y-1/2 group">
                          <span className={`absolute -inset-2.5 rounded-full border pointer-events-none ${selectedPatientObj.vitals.mpu6050.fallDetected ? 'bg-red-500/30 border-red-500 animate-ping' : 'bg-emerald-500/20 border-emerald-500/40 animate-ping'}`} />
                          <div className={`w-3.5 h-3.5 rounded-full border border-white cursor-pointer shadow relative z-10 ${selectedPatientObj.vitals.mpu6050.fallDetected ? 'bg-red-600 animate-bounce' : 'bg-emerald-500'}`} />
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-5 hidden group-hover:block bg-slate-950 text-white font-extrabold text-[9px] p-2 rounded-lg whitespace-nowrap shadow-xl z-20 border border-slate-800">
                            MPU6050 Accel Y: {selectedPatientObj.vitals.mpu6050.accelY.toFixed(2)}g
                          </div>
                        </div>

                        {/* Hotspot 4: MAX30102 Cardios (Left Arm/Wrist) */}
                        <div className="absolute top-[58%] left-[30%] -translate-x-1/2 -translate-y-1/2 group">
                          <span className="absolute -inset-2.5 rounded-full bg-red-500/20 border border-red-500/40 animate-ping pointer-events-none" />
                          <div className="w-3.5 h-3.5 rounded-full bg-red-500 border border-white cursor-pointer shadow relative z-10" />
                          <div className="absolute left-1/2 -translate-x-1/2 bottom-5 hidden group-hover:block bg-slate-950 text-white font-extrabold text-[9px] p-2 rounded-lg whitespace-nowrap shadow-xl z-20 border border-slate-800">
                            MAX30102 HR: {selectedPatientObj.vitals.max30102.heartRate} BPM
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3.5 text-xs font-semibold text-slate-655 dark:text-slate-350">
                        <div className="flex justify-between">
                          <span className="text-slate-400 dark:text-slate-500">Clinical Diagnosis:</span>
                          <span className="text-slate-950 dark:text-slate-100 font-extrabold">{selectedPatientObj.condition}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400 dark:text-slate-500">Attending EHR Node:</span>
                          <span className="text-slate-950 dark:text-slate-100 font-extrabold">Room {selectedPatientObj.room} Link</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400 dark:text-slate-500">ESP32 Battery Link:</span>
                          <span className={`font-black ${selectedPatientObj.vitals.esp32.connected ? 'text-emerald-500' : 'text-red-500'}`}>
                            {selectedPatientObj.vitals.esp32.connected ? `${selectedPatientObj.vitals.esp32.battery}% Connected` : 'Offline'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Right Columns (Sensor Cards, Diagnostics, EHR Notes) */}
                    <div className="lg:col-span-2 space-y-6">
                      
                      {/* Sensor telemetry widgets */}
                      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
                        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2">
                          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">IoT Sensor Packet Readings</span>
                          <div className="flex items-center gap-1">
                        <span className="text-[10px] text-slate-400 dark:text-slate-500 font-semibold">EHR Sync: {ehrSyncTime}</span>
                            <button onClick={syncExternalEhr} className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-blue-600 border-none bg-transparent cursor-pointer font-bold text-[10px] uppercase">Sync</button>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* MAX30102 Card */}
                          <div className="border border-slate-150 dark:border-slate-800 rounded-2xl p-4 text-left space-y-2 bg-slate-50/20 dark:bg-slate-950/20">
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider block">MAX30102 Blood Vitals</span>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Heart Rate</span>
                              <span className="text-sm font-black text-red-500">{selectedPatientObj.vitals.max30102.heartRate} BPM</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">SpO2 Oxygen</span>
                              <span className="text-sm font-black text-blue-600 dark:text-blue-400">{selectedPatientObj.vitals.max30102.spo2}%</span>
                            </div>
                          </div>

                          {/* MPU6050 Movements */}
                          <div className="border border-slate-150 dark:border-slate-800 rounded-2xl p-4 text-left space-y-2 bg-slate-50/20 dark:bg-slate-950/20">
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider block">MPU6050 Motion Signals</span>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Posture Vectors (Y)</span>
                              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-205">{selectedPatientObj.vitals.mpu6050.accelY.toFixed(2)}g</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Fall Event Log</span>
                              <span className={`text-xs font-black uppercase tracking-wider ${selectedPatientObj.vitals.mpu6050.fallDetected ? 'text-red-500' : 'text-slate-400'}`}>
                                {selectedPatientObj.vitals.mpu6050.fallDetected ? 'FALL DISPATCH' : 'Normal'}
                              </span>
                            </div>
                          </div>

                          {/* DS18B20 Temp */}
                          <div className="border border-slate-150 dark:border-slate-800 rounded-2xl p-4 text-left space-y-2 bg-slate-50/20 dark:bg-slate-950/20">
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider block">DS18B20 Temperature</span>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Body Core Temp</span>
                              <span className="text-sm font-black text-amber-500">{selectedPatientObj.vitals.ds18b20.temperature}°C</span>
                            </div>
                          </div>

                          {/* ESP32 Diagnostics */}
                          <div className="border border-slate-150 dark:border-slate-800 rounded-2xl p-4 text-left space-y-2 bg-slate-50/20 dark:bg-slate-950/20">
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider block">ESP32 Link Diagnostics</span>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Wi-Fi RSSI</span>
                              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-205">{selectedPatientObj.vitals.esp32.rssi} dBm</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-xs font-bold text-slate-600 dark:text-slate-350">Battery State</span>
                              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-205">{selectedPatientObj.vitals.esp32.battery}%</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* EHR checkup notes */}
                      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-855 rounded-2xl p-5 shadow-sm space-y-4">
                        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Active EHR Log (Simulated)</span>
                        <div className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-xl">
                          <p className="text-xs text-slate-600 dark:text-slate-350 leading-relaxed italic">
                            "{patientNotesMap[selectedPatientId] || 'No notes currently registered for this active file.'}"
                          </p>
                        </div>
                        <div className="space-y-3">
                          <textarea 
                            placeholder="Add clinical coordination checkup comments..." 
                            value={clinicalNoteInput}
                            onChange={(e) => setClinicalNoteInput(e.target.value)}
                            className="w-full h-20 p-3 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold outline-none bg-slate-50 dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 focus:border-blue-400 text-slate-800 dark:text-slate-200" 
                          />
                          <button 
                            onClick={saveClinicalNotes} 
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer"
                          >
                            Sync notes with hospital records
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Clinical telemetry simulation control console (only on Patient Detail/Clinical Tab) */}
                  <div className="p-5 bg-slate-950 border border-slate-800 rounded-2xl text-left space-y-4 shadow-xl">
                    <div className="flex items-center gap-1.5 text-indigo-400">
                      <Radio className="w-5 h-5 animate-pulse" />
                      <span className="text-xs font-black uppercase tracking-wider">Clinical Telemetry Simulation Console (Audits & Testing)</span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-semibold leading-relaxed">
                      Toggle active sensor updates for <strong>{selectedPatientObj.name}</strong> to test dynamic layout triggers, flashing alarms, and automated HIPAA logs:
                    </p>
                    <div className="flex flex-wrap gap-2.5 select-none">
                      <button onClick={simulateNormal} className="px-4 py-2 bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 hover:bg-emerald-900/30 font-bold text-xs rounded-xl cursor-pointer transition-colors">
                        ✅ Normalize Vitals
                      </button>
                      <button onClick={simulateFall} className="px-4 py-2 bg-red-950/40 text-red-400 border border-red-900/50 hover:bg-red-900/30 font-bold text-xs rounded-xl cursor-pointer transition-colors">
                        🚨 Trigger MPU6050 Fall Alert
                      </button>
                      <button onClick={simulateHypoxia} className="px-4 py-2 bg-red-950/40 text-red-450 border border-red-900/50 hover:bg-red-900/30 font-bold text-xs rounded-xl cursor-pointer transition-colors">
                        🫁 Trigger MAX30102 Hypoxia
                      </button>
                      <button onClick={simulateFever} className="px-4 py-2 bg-amber-950/40 text-amber-400 border border-amber-900/50 hover:bg-amber-900/30 font-bold text-xs rounded-xl cursor-pointer transition-colors">
                        🌡️ Trigger DS18B20 Fever
                      </button>
                      <button onClick={simulateESP32Disconnect} className="px-4 py-2 bg-slate-900 text-slate-350 border border-slate-805 hover:bg-slate-800 font-bold text-xs rounded-xl cursor-pointer transition-colors">
                        🔌 Disconnect ESP32 Node
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Reports and Settings tabs */}
              {activeTab === 'Reports' && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 text-left space-y-4 shadow-sm">
                  <h2 className="text-base font-black text-slate-950 dark:text-slate-50">External Health Record Sync Report (Simulated)</h2>
                  <p className="text-xs text-slate-550 dark:text-slate-400 leading-relaxed font-semibold">
                    NeuroCare Nexus simulates an external health record sync for academic demonstration. Vitals from patient nodes sync automatically every 10 seconds. Audit logs are generated for all access operations to ensure compliance.
                  </p>
                  <button onClick={() => addToast('EHR connection verified (Simulated).', 'success')} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
                    Verify Health Record Sync (Simulated)
                  </button>
                </div>
              )}

              {activeTab === 'Settings' && (
                <div className="max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-sm text-left">
                  <h2 className="text-base font-black text-slate-950 dark:text-slate-50 mb-4">Attending Threshold Configurations</h2>
                  <form onSubmit={handleSaveSettings} className="space-y-4 text-xs font-semibold text-slate-700 dark:text-slate-300">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <label className="block text-[11px] font-black text-slate-400 uppercase tracking-wider">Min SpO2 Threshold (%)</label>
                        <input type="number" value={settingsForm.minSpo2} onChange={e => setSettingsForm({...settingsForm, minSpo2: e.target.value})} className="w-full p-2.5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-950 text-xs text-slate-800 dark:text-slate-200 outline-none focus:border-blue-400" />
                      </div>
                      <div className="space-y-1">
                        <label className="block text-[11px] font-black text-slate-400 uppercase tracking-wider">Max Heart Rate (BPM)</label>
                        <input type="number" value={settingsForm.maxHR} onChange={e => setSettingsForm({...settingsForm, maxHR: e.target.value})} className="w-full p-2.5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-950 text-xs text-slate-800 dark:text-slate-200 outline-none focus:border-blue-400" />
                      </div>
                    </div>
                    <button type="submit" className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
                      Save Threshold Adjustments
                    </button>
                  </form>
                </div>
              )}
            </>
          )}

          {/* ==================== PATIENT / FAMILY MONITOR ==================== */}
          {(userRole === 'patient' || userRole === 'family') && selectedPatientObj && (
            <div className="space-y-6 text-left max-w-4xl mx-auto">
              


              {/* Vitals grids */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                
                {/* MAX30102 Vitals */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">MAX30102 Sensor</span>
                    <span className="text-[9px] text-emerald-500 dark:text-emerald-400 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Stable</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Heart Rate</span>
                      <span className="text-xl font-black text-red-500">{selectedPatientObj.vitals.max30102.heartRate} BPM</span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">SpO2 Oxygen</span>
                      <span className="text-xl font-black text-blue-600 dark:text-blue-400">{selectedPatientObj.vitals.max30102.spo2}%</span>
                    </div>
                  </div>
                </div>

                {/* DS18B20 Temp */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">DS18B20 Thermal</span>
                    <span className="text-[9px] text-emerald-500 dark:text-emerald-400 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Stable</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Body Temp</span>
                      <span className="text-xl font-black text-amber-500">{selectedPatientObj.vitals.ds18b20.temperature}°C</span>
                    </div>
                  </div>
                </div>

                {/* MPU6050 Fall Vector */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">MPU6050 Motion</span>
                    <span className="text-[9px] text-emerald-500 dark:text-emerald-400 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Secure</span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Fall State</span>
                      <span className="text-sm font-black text-slate-800 dark:text-slate-200">NO FALL DETECTED</span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-slate-500 dark:text-slate-400">Posture Angle</span>
                      <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">Stable Vectors</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Attending Consulting Doctor Section */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4 text-left">
                <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
                  <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block font-sans">Attending Consulting Doctor</span>
                  <span className="text-[9px] px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-650 dark:text-blue-400 border border-blue-100 dark:border-blue-900/30 font-black uppercase tracking-wider">Clinical Care</span>
                </div>
                
                {selectedPatientObj?.doctorNpi ? (
                  (() => {
                    const doctorObj = doctorsList.find(d => d.npi === selectedPatientObj.doctorNpi);
                    return (
                      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-xs font-semibold">
                        <div className="space-y-1">
                          <p className="text-sm font-black text-slate-950 dark:text-slate-100">{doctorObj?.name || 'Assigned Clinician'}</p>
                          <p className="text-slate-400 dark:text-slate-500">{doctorObj?.hospital || 'Associated Hospital Facility'} • Verified NPI: <span className="font-mono">{selectedPatientObj.doctorNpi}</span></p>
                        </div>
                        <button
                          onClick={() => handleUpdateDoctor(null)}
                          className="px-3.5 py-1.5 bg-slate-50 dark:bg-slate-950 text-slate-655 dark:text-slate-350 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-655 dark:hover:text-red-400 border border-slate-200 dark:border-slate-800 rounded-xl cursor-pointer font-bold text-[10px] uppercase tracking-wider transition-colors self-start sm:self-auto"
                        >
                          Change Doctor Link
                        </button>
                      </div>
                    );
                  })()
                ) : (
                  <div className="space-y-3.5">
                    <p className="text-xs text-slate-500 dark:text-slate-455 font-semibold">
                      You are not currently linked to a consulting physician. To share your telemetry streams with an attending doctor, select a clinician below:
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <select
                        id="doctor-select"
                        className="flex-1 p-2.5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-950 text-xs font-semibold outline-none focus:border-blue-400 text-slate-800 dark:text-slate-200"
                      >
                        <option value="">-- Choose verified consulting doctor --</option>
                        {doctorsList.map(doc => (
                          <option key={doc.npi} value={doc.npi}>
                            {doc.name} ({doc.hospital})
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => {
                          const selectEl = document.getElementById('doctor-select');
                          if (selectEl && selectEl.value) {
                            handleUpdateDoctor(selectEl.value);
                          } else {
                            addToast('Please select a verified doctor first.', 'warning');
                          }
                        }}
                        className="px-4 py-2.5 bg-blue-600 hover:bg-blue-750 text-white font-bold text-xs rounded-xl border-none cursor-pointer"
                      >
                        Confirm Doctor Selection
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Attending Live Telemetry ECG Sweep */}
              <ChartPlaceholder
                heartRate={selectedPatientObj?.vitals?.max30102?.heartRate ?? null}
                spo2={selectedPatientObj?.vitals?.max30102?.spo2 ?? null}
              />

              {/* Attending Care Notes widget */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-855 rounded-2xl p-5 shadow-sm space-y-4">
                <span className="text-xs font-black text-slate-950 dark:text-slate-50 uppercase tracking-wider block">Clinical Notes from Attending Physician</span>
                <div className="p-4 bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-850 rounded-2xl">
                  <p className="text-xs text-slate-655 dark:text-slate-350 leading-relaxed font-semibold">
                    "{patientNotesMap[selectedPatientId] || 'No clinical notes on file for your current record.'}"
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Patient/Family: empty state guard */}
          {(userRole === 'patient' || userRole === 'family') && !selectedPatientObj && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-8 text-center shadow-sm text-slate-400 dark:text-slate-500 font-semibold text-sm">
              Connecting to telemetry... please wait.
            </div>
          )}

          {/* Patient/Family: My Vitals / Relative Vitals tab */}
          {(userRole === 'patient' || userRole === 'family') && (activeTab === 'My Vitals' || activeTab === 'Relative Vitals') && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 text-left shadow-sm space-y-2">
              <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Detailed Vitals</h2>
              <p className="text-xs text-slate-455 dark:text-slate-500 font-semibold">Full vitals history and trend charts are coming soon. Your live readings are visible on the Dashboard tab.</p>
            </div>
          )}

          {/* Patient/Family: Prescriptions tab */}
          {(userRole === 'patient' || userRole === 'family') && activeTab === 'Prescriptions' && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 text-left shadow-sm space-y-2">
              <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Prescription Registry</h2>
              <p className="text-xs text-slate-455 dark:text-slate-500 font-semibold">Medication schedules and adherence tracking are coming soon.</p>
            </div>
          )}

          {/* Patient/Family: Settings tab */}
          {(userRole === 'patient' || userRole === 'family') && activeTab === 'Settings' && (
            <div className="max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-sm text-left space-y-4">
              <h2 className="text-base font-black text-slate-950 dark:text-slate-50">Account Settings</h2>
              <p className="text-xs text-slate-455 dark:text-slate-500 font-semibold">Notification preferences and profile settings are coming soon.</p>
            </div>
          )}

        </main>
      </div>
    </div>
  );
};

export default DashboardPage;
