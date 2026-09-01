import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import ChartPlaceholder from '../components/dashboard/ChartPlaceholder';
import { getApiUrl } from '../services/api';
import { Activity, Heart, Sparkles, TrendingUp, Radio, AlertTriangle } from 'lucide-react';

export const VitalsPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  
  const deriveInitialPatientId = () => {
    if (userRole === 'patient' && user?.deviceId) {
      return user.deviceId.replace(/^NP-/i, 'P-');
    }
    if (userRole === 'family' && user?.patientId) {
      return user.patientId;
    }
    return 'P-101';
  };

  const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId);
  const [patientVitals, setPatientVitals] = useState({
    max30102: { heartRate: 72, spo2: 98 },
    ds18b20: { temperature: 36.8 },
    mpu6050: { state: 'NO FALL DETECTED', vectors: 'Stable Vectors' }
  });
  const [manualVitals, setManualVitals] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Manual Vital Modal States
  const [isVitalModalOpen, setIsVitalModalOpen] = useState(false);
  const [vitalForm, setVitalForm] = useState({
    heartRate: '', spo2: '', temperature: '', respiratoryRate: '',
    systolicBp: '', diastolicBp: '', weight: '', bloodGlucose: '', notes: ''
  });

  const fetchVitalsData = async () => {
    try {
      setIsLoading(true);
      // 1. Fetch live telemetry/patient record
      const res = await authFetch(getApiUrl(`/health-records?patientId=${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        if (data.manualVitals) {
          setManualVitals(data.manualVitals);
        }
        if (data.patient?.vitals) {
          setPatientVitals(data.patient.vitals);
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
        addToast('Manual vital measurement logged with source = MANUAL.', 'success');
        setIsVitalModalOpen(false);
        setVitalForm({
          heartRate: '', spo2: '', temperature: '', respiratoryRate: '',
          systolicBp: '', diastolicBp: '', weight: '', bloodGlucose: '', notes: ''
        });
        fetchVitalsData();
      } else {
        const err = await res.text();
        addToast(`Failed to log vital: ${err}`, 'error');
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
        addToast('Vital measurement entry removed.', 'info');
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
            Real-time multi-sensor telemetry stream from wearable IoT nodes with preserved device provenance.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setIsVitalModalOpen(true)}
            className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors border-none cursor-pointer flex items-center gap-1.5"
          >
            <Heart className="w-4 h-4" />
            <span>Record Manual Vitals</span>
          </button>
        </div>
      </div>

      {/* Sensor Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {/* MAX30102 Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">MAX30102 Optical</span>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Active Stream</span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">Heart Rate</span>
              <span className="text-2xl font-black text-red-500">{patientVitals.max30102?.heartRate || '--'} <span className="text-xs font-bold">BPM</span></span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">SpO2 Blood Oxygen</span>
              <span className="text-2xl font-black text-blue-600 dark:text-blue-400">{patientVitals.max30102?.spo2 || '--'}<span className="text-xs font-bold">%</span></span>
            </div>
          </div>
        </div>

        {/* DS18B20 Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">DS18B20 Thermal</span>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Calibrated</span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">Body Temperature</span>
              <span className="text-2xl font-black text-amber-500">{patientVitals.ds18b20?.temperature || '--'} <span className="text-xs font-bold">°C</span></span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">Fahrenheit</span>
              <span className="text-xs font-black text-slate-600 dark:text-slate-300">
                {patientVitals.ds18b20?.temperature ? `${((patientVitals.ds18b20.temperature * 9/5) + 32).toFixed(1)} °F` : '--'}
              </span>
            </div>
          </div>
        </div>

        {/* MPU6050 Fall Vector Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">MPU6050 Motion</span>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">Arm Angle OK</span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">Fall State</span>
              <span className="text-xs font-black text-emerald-600 uppercase">{patientVitals.mpu6050?.state || 'NO FALL DETECTED'}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-bold text-slate-500">Telemetry Vectors</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">{patientVitals.mpu6050?.vectors || 'Stable Vectors'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Live ECG Telemetry Waveform */}
      <ChartPlaceholder 
        heartRate={patientVitals.max30102?.heartRate ?? 72}
        spo2={patientVitals.max30102?.spo2 ?? 98}
      />

      {/* Manual Vital Measurements Journal */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4 text-left">
        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-rose-500" />
            <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">Recorded Vital Measurements History</span>
          </div>
          <span className="text-[10px] font-bold text-slate-400">Total Entries: {manualVitals.length}</span>
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
                      {v.source_label || (v.source === 'MANUAL' ? 'Manual entry' : 'Device / ESP32')}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-400">
                      {v.measurement_time ? new Date(v.measurement_time).toLocaleString() : 'Just Now'} • Recorded by: {v.entered_by_name || 'Patient'}
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

      {/* Record Manual Vitals Modal */}
      {isVitalModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Record Manual Vital Measurement</h3>
              <button onClick={() => setIsVitalModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>
            <p className="text-[11px] text-slate-500 italic">
              * Manual vital measurements will be stored with <strong className="font-mono">source = MANUAL</strong> and labeled "Manual entry".
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
              <button onClick={() => setIsVitalModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">Cancel</button>
              <button onClick={handleSaveManualVital} className="px-4 py-2 bg-rose-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">Save Manual Vitals</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VitalsPage;
