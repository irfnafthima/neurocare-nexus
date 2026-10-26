import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { useRPM } from '../context/RPMContext';
import ChartPlaceholder from '../components/dashboard/ChartPlaceholder';
import { getApiUrl } from '../services/api';
import { 
  Activity, 
  Heart, 
  User, 
  Wifi, 
  WifiOff, 
  Cpu, 
  Compass, 
  Thermometer, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Radio, 
  AlertTriangle,
  Battery,
  Signal
} from 'lucide-react';
import { PatientContextSelector } from '../components/common/PatientContextSelector';
import { EmptyPatientState } from '../components/common/EmptyPatientState';

export const VitalsPage = () => {
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

  const { 
    telemetryWsStatus, 
    telemetryFreshness, 
    latestTelemetryPacket, 
    selectedPatientId: rpmSelectedPid, 
    setSelectedPatientId: setRpmSelectedPid,
    patients: rpmPatients 
  } = useRPM();

  const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId);
  const [patientData, setPatientData] = useState(null);
  const [manualVitals, setManualVitals] = useState([]);
  const [lastKnownPacket, setLastKnownPacket] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Sync selected patient with RPMContext
  useEffect(() => {
    if (selectedPatientId && setRpmSelectedPid) {
      setRpmSelectedPid(selectedPatientId);
    }
  }, [selectedPatientId, setRpmSelectedPid]);

  // Sync state when query parameter changes
  useEffect(() => {
    if (queryPatientId && queryPatientId !== selectedPatientId) {
      setSelectedPatientId(queryPatientId);
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
    }
  }, [queryPatientId]);

  // Patient Switch: Reset local last known packet to prevent cross-patient data leaking
  useEffect(() => {
    setLastKnownPacket(null);
  }, [selectedPatientId]);

  // Determine active telemetry packet matching selected patient
  const activePacket = useMemo(() => {
    if (latestTelemetryPacket && String(latestTelemetryPacket.patient_id) === String(selectedPatientId)) {
      return latestTelemetryPacket;
    }
    return null;
  }, [latestTelemetryPacket, selectedPatientId]);

  // Update last known packet whenever a valid packet arrives
  useEffect(() => {
    if (activePacket) {
      setLastKnownPacket(activePacket);
    }
  }, [activePacket]);

  // Resolve assigned physical device details
  const rosterPatient = useMemo(() => {
    return rpmPatients?.find(p => String(p.id) === String(selectedPatientId)) || null;
  }, [rpmPatients, selectedPatientId]);

  const assignedDevice = useMemo(() => {
    return patientData?.assignedDevice || rosterPatient?.assignedDevice || null;
  }, [patientData, rosterPatient]);

  const hasAssignedDevice = useMemo(() => {
    // If backend reports hasDevice or assignedDevice
    if (patientData?.hasDevice || rosterPatient?.hasDevice || assignedDevice) {
      return true;
    }
    // If active or cached telemetry comes from a real physical device
    if (activePacket?.source === 'REAL_DEVICE' || (activePacket?.device_id && !activePacket.device_id.startsWith('SIM-'))) {
      return true;
    }
    if (lastKnownPacket?.source === 'REAL_DEVICE' || (lastKnownPacket?.device_id && !lastKnownPacket.device_id.startsWith('SIM-'))) {
      return true;
    }
    return false;
  }, [patientData, rosterPatient, assignedDevice, activePacket, lastKnownPacket]);

  const deviceSerial = useMemo(() => {
    if (activePacket?.device_id && !activePacket.device_id.startsWith('SIM-')) {
      return activePacket.device_id;
    }
    if (lastKnownPacket?.device_id && !lastKnownPacket.device_id.startsWith('SIM-')) {
      return lastKnownPacket.device_id;
    }
    if (assignedDevice?.serial) {
      return assignedDevice.serial;
    }
    return hasAssignedDevice ? 'NCN-ESP32-001' : null;
  }, [activePacket, lastKnownPacket, assignedDevice, hasAssignedDevice]);

  const currentTelemetry = activePacket || lastKnownPacket;

  // Safe UTC timestamp parsing & age calculation in seconds
  const readingAgeSeconds = useMemo(() => {
    const rawTs = currentTelemetry?.received_at || currentTelemetry?.timestamp;
    if (!rawTs) return null;
    const readingMs = new Date(rawTs).getTime();
    if (isNaN(readingMs)) return null;
    return Math.max(0, (Date.now() - readingMs) / 1000);
  }, [currentTelemetry]);

  // Derived effective freshness
  const effectiveFreshness = useMemo(() => {
    if (!hasAssignedDevice) return 'NO_DEVICE';
    if (readingAgeSeconds !== null) {
      if (readingAgeSeconds <= 10) return 'LIVE';
      if (readingAgeSeconds <= 30) return 'STALE';
      return 'OFFLINE';
    }
    return telemetryFreshness;
  }, [hasAssignedDevice, readingAgeSeconds, telemetryFreshness]);

  // Determine effective telemetry state (live, stale, offline, no data)
  const isLive = effectiveFreshness === 'LIVE';
  const isStale = effectiveFreshness === 'STALE';
  const isOffline = effectiveFreshness === 'OFFLINE' || (!isLive && !isStale && Boolean(lastKnownPacket));
  const isNoData = (effectiveFreshness === 'NO_DATA' || !effectiveFreshness) && !lastKnownPacket;

  // Physical ESP32 Hardware Status
  const esp32Status = useMemo(() => {
    if (!hasAssignedDevice) return 'NO DEVICE';
    if (isLive) {
      return currentTelemetry?.esp32_connected !== false ? 'CONNECTED' : 'DISCONNECTED';
    }
    if (isStale) return 'STALE';
    if (isOffline) return 'OFFLINE';
    return 'NO DATA';
  }, [hasAssignedDevice, isLive, isStale, isOffline, currentTelemetry]);

  // Derived 6-axis acceleration magnitude: sqrt(ax^2 + ay^2 + az^2)
  const accelMagnitude = useMemo(() => {
    if (!currentTelemetry) return null;
    const ax = Number(currentTelemetry.accel_x);
    const ay = Number(currentTelemetry.accel_y);
    const az = Number(currentTelemetry.accel_z);
    if (isNaN(ax) || isNaN(ay) || isNaN(az)) return null;
    return Math.sqrt(ax * ax + ay * ay + az * az).toFixed(2);
  }, [currentTelemetry]);

  // Derived 6-axis gyroscope magnitude: sqrt(gx^2 + gy^2 + gz^2)
  const gyroMagnitude = useMemo(() => {
    if (!currentTelemetry) return null;
    const gx = Number(currentTelemetry.gyro_x);
    const gy = Number(currentTelemetry.gyro_y);
    const gz = Number(currentTelemetry.gyro_z);
    if (isNaN(gx) || isNaN(gy) || isNaN(gz)) return null;
    return Math.sqrt(gx * gx + gy * gy + gz * gz).toFixed(2);
  }, [currentTelemetry]);

  // Manual Vital Modal States
  const [isVitalModalOpen, setIsVitalModalOpen] = useState(false);
  const [vitalForm, setVitalForm] = useState({
    heartRate: '', spo2: '', temperature: '', respiratoryRate: '',
    systolicBp: '', diastolicBp: '', weight: '', bloodGlucose: '', notes: ''
  });

  const fetchVitalsData = async () => {
    if (!selectedPatientId) {
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      // 1. Health Records (conditions, allergies, manual vitals)
      const res = await authFetch(getApiUrl(`/health-records?patientId=${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        setPatientData(data.patient || (data.patientName ? { name: data.patientName, id: data.patientId } : null));
        if (data.manualVitals) {
          setManualVitals(data.manualVitals);
        }
      }

      // 2. Poll protected latest-telemetry endpoint
      const telRes = await authFetch(getApiUrl(`/monitoring/patient-telemetry/${selectedPatientId}/latest`));
      if (telRes.ok) {
        const telData = await telRes.json();
        if (telData.status === 'success' && String(telData.patient_id) === String(selectedPatientId)) {
          setLastKnownPacket(telData);
        }
      }
    } catch (err) {
      console.error('Error fetching vitals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVitalsData();
    const interval = setInterval(fetchVitalsData, 10000);
    return () => clearInterval(interval);
  }, [selectedPatientId]);

  const handleSaveManualVital = async () => {
    if (!selectedPatientId) {
      addToast('Select a patient before recording manual vitals.', 'error');
      return;
    }

    try {
      const payload = {
        patientId: selectedPatientId,
        heartRate: vitalForm.heartRate ? parseFloat(vitalForm.heartRate) : null,
        spo2: vitalForm.spo2 ? parseFloat(vitalForm.spo2) : null,
        temperature: vitalForm.temperature ? parseFloat(vitalForm.temperature) : null,
        respiratoryRate: vitalForm.respiratoryRate ? parseFloat(vitalForm.respiratoryRate) : null,
        systolicBp: vitalForm.systolicBp ? parseFloat(vitalForm.systolicBp) : null,
        diastolicBp: vitalForm.diastolicBp ? parseFloat(vitalForm.diastolicBp) : null,
        weight: vitalForm.weight ? parseFloat(vitalForm.weight) : null,
        bloodGlucose: vitalForm.bloodGlucose ? parseFloat(vitalForm.bloodGlucose) : null,
        notes: vitalForm.notes || ''
      };

      const res = await authFetch(getApiUrl('/health-records'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'vital', ...payload })
      });

      if (res.ok) {
        addToast('Manual vital measurement saved with source = MANUAL.', 'success');
        setIsVitalModalOpen(false);
        setVitalForm({
          heartRate: '', spo2: '', temperature: '', respiratoryRate: '',
          systolicBp: '', diastolicBp: '', weight: '', bloodGlucose: '', notes: ''
        });
        fetchVitalsData();
      } else {
        const err = await res.text();
        addToast(`Failed to save manual vital: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error saving manual vital measurement.', 'error');
    }
  };

  const handleDeleteManualVital = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/health-records/vital/${id}`), {
        method: 'DELETE'
      });
      if (res.ok) {
        addToast('Vital record deleted.', 'info');
        setManualVitals(prev => prev.filter(v => v.id !== id));
      } else {
        addToast('Failed to delete vital record.', 'error');
      }
    } catch (e) {
      addToast('Error deleting vital record.', 'error');
    }
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Vitals & Telemetry Monitoring
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Real-time IoT wearable telemetry stream and clinical manual measurement journal with strict hardware provenance.
          </p>
        </div>
        <div className="flex items-center gap-3 self-start sm:self-auto flex-wrap">
          {/* Patient Context: interactive selector for clinicians, badge for patients/family */}
          {isClinician ? (
            <PatientContextSelector
              activePatientId={selectedPatientId}
              selectedPatientId={selectedPatientId}
              onSelectPatient={(id) => {
                setSelectedPatientId(id);
                if (id) {
                  setSearchParams({ patientId: id });
                } else {
                  setSearchParams({});
                }
              }}
            />
          ) : (
            <div className="px-3.5 py-1.5 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/50 rounded-xl flex items-center gap-2">
              <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <div className="text-left">
                <span className="text-[9px] font-black uppercase tracking-wider text-slate-400 block">Patient Record</span>
                <span className="text-xs font-black text-slate-900 dark:text-slate-100">
                  {patientData?.name || (userRole === 'patient' ? user?.full_name : 'Authorized Patient')}
                  <span className="font-mono text-blue-600 dark:text-blue-400 ml-1.5">({selectedPatientId || 'Not Configured'})</span>
                </span>
              </div>
            </div>
          )}

          {/* WebSocket Transport State Badge */}
          {selectedPatientId && (
            <div className={`px-2.5 py-1.5 rounded-xl text-[10px] font-bold border flex items-center gap-1.5 ${
              telemetryWsStatus === 'CONNECTED'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50'
                : telemetryWsStatus === 'CONNECTING'
                ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900/50'
                : 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800'
            }`}>
              {telemetryWsStatus === 'CONNECTED' ? <Wifi className="w-3.5 h-3.5 animate-pulse" /> : <WifiOff className="w-3.5 h-3.5" />}
              <span className="uppercase tracking-wider">WS {telemetryWsStatus}</span>
            </div>
          )}

          {/* Dynamic Device & Freshness Badges */}
          {selectedPatientId && (
            <>
              {!hasAssignedDevice ? (
                <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-900/50">
                  MANUAL VITALS ONLY
                </div>
              ) : isLive ? (
                <div className="flex items-center gap-1.5">
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50 flex items-center gap-1">
                    <Radio className="w-3 h-3 text-emerald-600" />
                    <span>REAL DEVICE</span>
                  </div>
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-emerald-500 text-white border-emerald-600 animate-pulse">
                    LIVE
                  </div>
                </div>
              ) : isStale ? (
                <div className="flex items-center gap-1.5">
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900/50">
                    REAL DEVICE
                  </div>
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-amber-500 text-white border-amber-600">
                    STALE
                  </div>
                </div>
              ) : isOffline ? (
                <div className="flex items-center gap-1.5">
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-900/50">
                    DEVICE OFFLINE
                  </div>
                  <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300">
                    LAST KNOWN
                  </div>
                </div>
              ) : (
                <div className="px-2.5 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800">
                  NO DATA
                </div>
              )}
            </>
          )}

          {selectedPatientId && (
            <button
              onClick={() => setIsVitalModalOpen(true)}
              className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors border-none cursor-pointer flex items-center gap-1.5"
            >
              <Heart className="w-4 h-4" />
              <span>Record Manual Vitals</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Vitals & Telemetry Content */}
      {!selectedPatientId && isClinician ? (
        <EmptyPatientState pageName="Vitals & Telemetry Monitoring" isClinician={isClinician} />
      ) : (
        <>
          {/* Hardware Diagnostic Banner for Assigned Devices */}
          {hasAssignedDevice && (
            <div className="bg-slate-900 text-slate-100 rounded-2xl p-4 shadow-sm border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Wearable Node</span>
                    <span className="font-mono font-bold text-slate-200">{deviceSerial || 'Wearable Hardware'}</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Source: <strong className="text-emerald-400 font-mono">REAL DEVICE</strong>
                    {currentTelemetry?.timestamp && (
                      <span className="ml-2 text-slate-400">
                        • Last Packet: {new Date(currentTelemetry.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 text-[11px] font-mono">
                {/* Physical ESP32 State */}
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-400">ESP32 State:</span>
                  <span className={`px-2 py-0.5 rounded font-black uppercase text-[10px] ${
                    esp32Status === 'CONNECTED' 
                      ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                      : esp32Status === 'STALE'
                      ? 'bg-amber-950/80 text-amber-400 border border-amber-800'
                      : 'bg-rose-950/80 text-rose-400 border border-rose-800'
                  }`}>
                    {esp32Status}
                  </span>
                </div>

                {/* RSSI Signal */}
                <div className="flex items-center gap-1.5">
                  <Signal className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-400">RSSI:</span>
                  <span className="font-bold text-slate-200">
                    {currentTelemetry?.esp32_rssi !== null && currentTelemetry?.esp32_rssi !== undefined ? `${currentTelemetry.esp32_rssi} dBm` : '--'}
                  </span>
                </div>

                {/* Battery */}
                <div className="flex items-center gap-1.5">
                  <Battery className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-400">Battery:</span>
                  <span className="font-bold text-slate-200">
                    {currentTelemetry?.esp32_battery !== null && currentTelemetry?.esp32_battery !== undefined ? `${currentTelemetry.esp32_battery}%` : '--'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Stale / Offline / No Data Alert Notices */}
          {hasAssignedDevice && isOffline && lastKnownPacket && (
            <div className="p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/50 rounded-2xl flex items-center justify-between text-xs text-rose-800 dark:text-rose-200">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                <span className="font-black uppercase tracking-wider">DEVICE OFFLINE</span>
                <span className="text-slate-500 dark:text-slate-400">
                  Last reading received: {lastKnownPacket.timestamp ? new Date(lastKnownPacket.timestamp).toLocaleTimeString() : 'Previously recorded'}
                </span>
              </div>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-rose-100 dark:bg-rose-900 text-rose-700 dark:text-rose-300">
                Displaying Last Known Reading
              </span>
            </div>
          )}

          {hasAssignedDevice && isNoData && (
            <div className="p-3.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="font-black uppercase tracking-wider">NO REAL-TIME TELEMETRY PACKETS YET</span>
                <span>Awaiting live telemetry broadcast from ESP32 node ({deviceSerial}).</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                NO DATA
              </span>
            </div>
          )}

          {/* CASE 1: Patient has NO Wearable Device Assigned */}
          {!hasAssignedDevice ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 text-center space-y-4 shadow-sm">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-base font-black text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                  NO WEARABLE DEVICE ASSIGNED
                </h2>
                <p className="text-xs font-semibold text-slate-500 max-w-md mx-auto">
                  Manual vitals only. This patient does not have an active physical IoT wearable node assigned. No simulated telemetry is displayed.
                </p>
              </div>
              <div className="pt-2">
                <button
                  onClick={() => setIsVitalModalOpen(true)}
                  className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors border-none cursor-pointer inline-flex items-center gap-2"
                >
                  <Heart className="w-4 h-4" />
                  <span>Record Manual Vitals</span>
                </button>
              </div>
            </div>
          ) : (
            /* CASE 2: Patient has an Assigned Device -> Display Real IoT Sensors */
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {/* MAX30102 Card */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">
                    MAX30102 Optical PPG
                  </span>
                  <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded border flex items-center gap-1 ${
                    isLive 
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50'
                      : isOffline
                      ? 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400'
                      : 'bg-slate-50 text-slate-500 border-slate-200 dark:bg-slate-950 dark:text-slate-400'
                  }`}>
                    <Activity className="w-3 h-3" />
                    <span>{isLive ? 'REAL DEVICE' : isOffline ? 'Last Known' : 'NO DATA'}</span>
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-bold text-slate-500">Heart Rate</span>
                    <span className="text-2xl font-black text-red-500">
                      {currentTelemetry?.heart_rate !== null && currentTelemetry?.heart_rate !== undefined ? currentTelemetry.heart_rate : '--'}{' '}
                      <span className="text-xs font-bold">BPM</span>
                    </span>
                  </div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-bold text-slate-500">SpO2 Blood Oxygen</span>
                    <span className="text-2xl font-black text-blue-600 dark:text-blue-400">
                      {currentTelemetry?.spo2 !== null && currentTelemetry?.spo2 !== undefined ? currentTelemetry.spo2 : '--'}
                      <span className="text-xs font-bold">%</span>
                    </span>
                  </div>
                  <div className="flex justify-between items-baseline pt-1 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-[11px] font-semibold text-slate-400">Signal Quality</span>
                    <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                      {currentTelemetry?.signal_quality || (currentTelemetry ? 'GOOD' : '--')}
                    </span>
                  </div>
                </div>
              </div>

              {/* DS18B20 Card — Explicitly handled as Not Connected on this ESP32 hardware node */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">
                    DS18B20 Thermal Sensor
                  </span>
                  <span className="text-[9px] text-amber-700 dark:text-amber-400 font-extrabold uppercase bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-900/50 flex items-center gap-1">
                    <Thermometer className="w-3 h-3" />
                    <span>Not Connected</span>
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-bold text-slate-500">Body Temperature</span>
                    <span className="text-2xl font-black text-slate-400">
                      -- <span className="text-xs font-bold">°C</span>
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-tight">
                    * DS18B20 body sensor is not physically connected to this ESP32 node.
                  </p>
                  {currentTelemetry?.temperature !== null && currentTelemetry?.temperature !== undefined && (
                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-baseline">
                      <span className="text-[10px] font-semibold text-slate-400">MPU6050 Board Sensor</span>
                      <span className="text-xs font-mono font-bold text-slate-600 dark:text-slate-300">
                        {Number(currentTelemetry.temperature).toFixed(1)} °C
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* MPU6050 6-Axis Motion & Fall Detection Card */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">
                    MPU6050 6-Axis Motion
                  </span>
                  <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded border flex items-center gap-1 ${
                    currentTelemetry?.fall_detected
                      ? 'bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-900'
                      : isLive
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50'
                      : 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400'
                  }`}>
                    <Compass className="w-3 h-3" />
                    <span>{currentTelemetry?.fall_detected ? 'FALL ALERT' : (isLive ? 'REAL DEVICE' : isOffline ? 'Last Known' : 'NO DATA')}</span>
                  </span>
                </div>
                <div className="space-y-2.5">
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-bold text-slate-500">Fall Status</span>
                    <span className={`text-xs font-black uppercase px-2 py-0.5 rounded ${
                      currentTelemetry?.fall_detected
                        ? 'bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-200 animate-pulse'
                        : currentTelemetry
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-slate-400'
                    }`}>
                      {currentTelemetry?.fall_detected ? 'FALL DETECTED' : (currentTelemetry ? 'NORMAL / NO FALL' : '--')}
                    </span>
                  </div>

                  {/* 3-Axis Accelerometer */}
                  <div className="pt-1.5 border-t border-slate-100 dark:border-slate-800 space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="font-semibold text-slate-400">Accel (X, Y, Z)</span>
                      <span className="font-mono font-bold text-slate-700 dark:text-slate-200">
                        {currentTelemetry?.accel_x !== null && currentTelemetry?.accel_x !== undefined
                          ? `${Number(currentTelemetry.accel_x).toFixed(2)}, ${Number(currentTelemetry.accel_y).toFixed(2)}, ${Number(currentTelemetry.accel_z).toFixed(2)} g`
                          : '--'}
                      </span>
                    </div>
                    {accelMagnitude && (
                      <div className="flex justify-between text-[10px]">
                        <span className="text-slate-400">Accel Magnitude</span>
                        <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{accelMagnitude} g</span>
                      </div>
                    )}
                  </div>

                  {/* 3-Axis Gyroscope */}
                  <div className="pt-1.5 border-t border-slate-100 dark:border-slate-800 space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="font-semibold text-slate-400">Gyro (X, Y, Z)</span>
                      <span className="font-mono font-bold text-slate-700 dark:text-slate-200">
                        {currentTelemetry?.gyro_x !== null && currentTelemetry?.gyro_x !== undefined
                          ? `${Number(currentTelemetry.gyro_x).toFixed(1)}, ${Number(currentTelemetry.gyro_y).toFixed(1)}, ${Number(currentTelemetry.gyro_z).toFixed(1)} °/s`
                          : '--'}
                      </span>
                    </div>
                    {gyroMagnitude && (
                      <div className="flex justify-between text-[10px]">
                        <span className="text-slate-400">Gyro Magnitude</span>
                        <span className="font-mono font-bold text-purple-600 dark:text-purple-400">{gyroMagnitude} °/s</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Telemetry Trend Waveform Monitor */}
          {hasAssignedDevice && (
            <ChartPlaceholder 
              heartRate={currentTelemetry?.heart_rate ?? null}
              spo2={currentTelemetry?.spo2 ?? null}
            />
          )}

          {/* Manual Vital Measurements Journal */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4 text-left">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
              <div className="flex items-center gap-2">
                <Heart className="w-4 h-4 text-rose-500" />
                <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">
                  Recorded Vital Measurements History
                </span>
              </div>
              <span className="text-[10px] font-bold text-slate-400">
                Total Entries: {manualVitals.length}
              </span>
            </div>

            {manualVitals.length === 0 ? (
              <div className="p-6 text-center text-xs font-semibold text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-850">
                No historical vital measurements recorded yet. Click "Record Manual Vitals" above to log a clinical reading.
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-850 max-h-96 overflow-y-auto">
                {manualVitals.map(v => (
                  <div key={v.id} className="py-3.5 flex items-start justify-between gap-4 text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-900/50">
                          {v.source_label || (v.source === 'MANUAL' ? 'Manual entry' : 'Wearable Device')}
                        </span>
                        <span className="text-[10px] font-semibold text-slate-400">
                          {v.measurement_time ? new Date(v.measurement_time).toLocaleString() : 'Just Now'} • Recorded by: {v.entered_by_name || 'Clinician / Patient'}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-3 font-mono text-xs font-bold text-slate-800 dark:text-slate-200 mt-1">
                        {v.heart_rate !== null && <span>HR: {v.heart_rate} BPM</span>}
                        {v.spo2 !== null && <span>SpO2: {v.spo2}%</span>}
                        {v.temperature !== null && <span>Temp: {v.temperature}°C</span>}
                        {v.systolic_bp !== null && v.diastolic_bp !== null && <span>BP: {v.systolic_bp}/{v.diastolic_bp} mmHg</span>}
                        {v.respiratory_rate !== null && <span>Resp: {v.respiratory_rate}/min</span>}
                        {v.weight !== null && <span>Weight: {v.weight} kg</span>}
                        {v.blood_glucose !== null && <span>Glucose: {v.blood_glucose} mg/dL</span>}
                      </div>
                      {v.notes && <p className="text-[10px] text-slate-500 italic mt-0.5">Notes: {v.notes}</p>}
                    </div>
                    <button
                      onClick={() => handleDeleteManualVital(v.id)}
                      className="px-2 py-1 bg-red-50 text-red-600 hover:bg-red-600 hover:text-white font-bold rounded text-[10px] cursor-pointer border-none shrink-0 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Record Manual Vitals Modal */}
      {isVitalModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Record Manual Vital Measurement
              </h3>
              <button onClick={() => setIsVitalModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">
                ✕
              </button>
            </div>
            <p className="text-[11px] text-slate-500 italic">
              * Manual vital measurements are saved with <strong className="font-mono">source = MANUAL</strong> and labeled "Manual entry".
            </p>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Heart Rate (BPM)</label>
                <input type="number" placeholder="20-300" value={vitalForm.heartRate} onChange={e => setVitalForm({...vitalForm, heartRate: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">SpO2 Oxygen (%)</label>
                <input type="number" placeholder="30-100" value={vitalForm.spo2} onChange={e => setVitalForm({...vitalForm, spo2: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Body Temperature (°C)</label>
                <input type="number" step="0.1" placeholder="25.0-45.0" value={vitalForm.temperature} onChange={e => setVitalForm({...vitalForm, temperature: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Resp. Rate (/min)</label>
                <input type="number" placeholder="3-80" value={vitalForm.respiratoryRate} onChange={e => setVitalForm({...vitalForm, respiratoryRate: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Systolic BP (mmHg)</label>
                <input type="number" placeholder="40-300" value={vitalForm.systolicBp} onChange={e => setVitalForm({...vitalForm, systolicBp: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Diastolic BP (mmHg)</label>
                <input type="number" placeholder="20-200" value={vitalForm.diastolicBp} onChange={e => setVitalForm({...vitalForm, diastolicBp: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Body Weight (kg)</label>
                <input type="number" step="0.1" placeholder="1-500" value={vitalForm.weight} onChange={e => setVitalForm({...vitalForm, weight: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Blood Glucose (mg/dL)</label>
                <input type="number" step="0.1" placeholder="10-1000" value={vitalForm.bloodGlucose} onChange={e => setVitalForm({...vitalForm, bloodGlucose: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div className="col-span-2">
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Measurement Notes</label>
                <textarea placeholder="Optional notes regarding measurement context..." value={vitalForm.notes} onChange={e => setVitalForm({...vitalForm, notes: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 h-16" />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setIsVitalModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">
                Cancel
              </button>
              <button onClick={handleSaveManualVital} className="px-4 py-2 bg-rose-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
                Save Manual Vitals
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VitalsPage;
