import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { derivePatientContextId } from '../utils/patientUtils';
import {
  Pill,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Calendar,
  User,
  ShieldCheck,
  TrendingUp,
  Activity,
  Plus,
  Info,
  Check,
  X,
  RotateCcw
} from 'lucide-react';
import { PatientContextSelector } from '../components/common/PatientContextSelector';
import { EmptyPatientState } from '../components/common/EmptyPatientState';

export const MedicinesPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const isClinician = userRole === 'doctor' || userRole === 'caregiver';
  const isDoctor = userRole === 'doctor';
  const isCaregiver = userRole === 'caregiver';
  const isFamily = userRole === 'family';
  const isPatient = userRole === 'patient';

  const queryPatientId = searchParams.get('patientId');

  const deriveInitialPatientId = () => {
    return derivePatientContextId({
      queryPatientId,
      user,
      isClinician,
      fallback: 'P-13'
    });
  };

  const [selectedPatientId, setSelectedPatientId] = useState(deriveInitialPatientId);
  const [activeTab, setActiveTab] = useState('today'); // 'today' | 'adherence' | 'prescriptions'
  const [timelineData, setTimelineData] = useState(null);
  const [adherenceData, setAdherenceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Action Modal State
  const [actionModal, setActionModal] = useState({
    isOpen: false,
    type: 'take', // 'take' | 'skip'
    dose: null,
    note: ''
  });

  // Doctor Configure Schedule Modal State
  const [scheduleModal, setScheduleModal] = useState({
    isOpen: false,
    rx: null,
    times: ['08:00', '20:00']
  });

  // Sync state if query parameter changes
  useEffect(() => {
    if (queryPatientId && queryPatientId !== selectedPatientId) {
      setSelectedPatientId(queryPatientId);
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
    }
  }, [queryPatientId]);

  const fetchData = async () => {
    if (!selectedPatientId) {
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      const [todayRes, adhRes] = await Promise.all([
        authFetch(getApiUrl(`/medications/today?patientId=${encodeURIComponent(selectedPatientId)}`)),
        authFetch(getApiUrl(`/medications/adherence?patientId=${encodeURIComponent(selectedPatientId)}&days=7`))
      ]);

      if (todayRes.ok) {
        const tData = await todayRes.json();
        setTimelineData(tData);
      } else {
        setTimelineData(null);
      }

      if (adhRes.ok) {
        const aData = await adhRes.json();
        setAdherenceData(aData);
      } else {
        setAdherenceData(null);
      }
    } catch (e) {
      console.error('Error fetching medication data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedPatientId]);

  const handleRecordAction = async () => {
    if (!actionModal.dose) return;
    const scheduleId = actionModal.dose.schedule_id;
    const actionType = actionModal.type;

    try {
      setActionLoadingId(scheduleId);
      const res = await authFetch(getApiUrl(`/medications/doses/${scheduleId}/${actionType}/`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scheduled_date: actionModal.dose.scheduled_date,
          notes: actionModal.note.trim()
        })
      });

      if (res.ok) {
        addToast(`Dose marked as ${actionType === 'take' ? 'TAKEN' : 'SKIPPED'} successfully.`, 'success');
        setActionModal({ isOpen: false, type: 'take', dose: null, note: '' });
        fetchData();
      } else {
        const err = await res.json();
        addToast(err.detail || 'Failed to record dose action.', 'error');
      }
    } catch (e) {
      addToast('Network error while recording dose action.', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleSaveSchedule = async (e) => {
    e.preventDefault();
    if (!scheduleModal.rx) return;
    try {
      const res = await authFetch(getApiUrl('/medications/schedule/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prescriptionId: scheduleModal.rx.id,
          times: scheduleModal.times.filter(t => t.trim().length > 0)
        })
      });

      if (res.ok) {
        addToast('Medication schedule configured successfully.', 'success');
        setScheduleModal({ isOpen: false, rx: null, times: ['08:00'] });
        fetchData();
      } else {
        const err = await res.json();
        addToast(err.detail || 'Failed to configure schedule.', 'error');
      }
    } catch (e) {
      addToast('Network error while saving schedule.', 'error');
    }
  };

  const getStatusBadge = (status, actionAt, markedBy) => {
    switch (status) {
      case 'TAKEN':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Taken {actionAt ? `• ${new Date(actionAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}
          </span>
        );
      case 'SKIPPED':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5" />
            Skipped
          </span>
        );
      case 'DUE':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800 flex items-center gap-1.5 animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            Due Now
          </span>
        );
      case 'MISSED':
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            Missed
          </span>
        );
      case 'UPCOMING':
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Upcoming
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Pill className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Medicine Tracker & Daily Adherence
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Daily pharmacotherapy dose checklist, real-time schedule tracking, and technical adherence analytics.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {isClinician ? (
            <PatientContextSelector
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
                <span className="text-xs font-black text-slate-900 dark:text-slate-100 font-mono">
                  {selectedPatientId || 'Not Configured'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs & Adherence Stats Overview */}
      {selectedPatientId && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4.5 shadow-xs flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">7-Day Adherence</span>
              <p className="text-lg font-black text-slate-900 dark:text-slate-100 mt-0.5">
                {adherenceData && adherenceData.adherence_rate !== null ? `${adherenceData.adherence_rate}%` : 'No adherence data yet'}
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4.5 shadow-xs flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Today's Progress</span>
              <p className="text-lg font-black text-slate-900 dark:text-slate-100 mt-0.5">
                {timelineData ? `${timelineData.summary.taken_count} / ${timelineData.summary.total_scheduled_today} Taken` : '0 Scheduled'}
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4.5 shadow-xs flex items-center gap-4">
            <div className="w-11 h-11 rounded-xl bg-rose-50 dark:bg-rose-950/60 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Missed Doses (Today)</span>
              <p className="text-lg font-black text-slate-900 dark:text-slate-100 mt-0.5">
                {timelineData ? timelineData.summary.missed_count : 0}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Role-Specific Guidance Banner */}
      {isFamily && (
        <div className="p-3.5 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 rounded-xl flex items-center gap-3 text-xs">
          <Info className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
          <span className="text-slate-600 dark:text-slate-350 font-semibold">
            Family Member Read-Only Mode: You can review scheduled doses and adherence tracking for your relative. Clinical dose logging is performed by the patient or attending caregiver.
          </span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('today')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-colors border-none cursor-pointer flex items-center gap-2 ${
            activeTab === 'today'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Today's Medicines
        </button>
        <button
          onClick={() => setActiveTab('adherence')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-colors border-none cursor-pointer flex items-center gap-2 ${
            activeTab === 'adherence'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
        >
          <Activity className="w-4 h-4" />
          Adherence Analytics
        </button>
      </div>

      {/* Main Content */}
      {!selectedPatientId && isClinician ? (
        <EmptyPatientState pageName="Medicine Tracker" isClinician={isClinician} />
      ) : isLoading ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-8 text-center text-slate-400 text-xs font-semibold animate-pulse">
          Loading medication schedule and adherence records...
        </div>
      ) : activeTab === 'today' ? (
        <div className="space-y-6">
          {/* Today's Doses */}
          <div className="space-y-3">
            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest pl-1">Today's Schedule ({timelineData?.date})</h3>

            {timelineData?.doses.length === 0 ? (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-8 text-center text-slate-400 text-xs font-semibold">
                No active medication doses scheduled for today.
              </div>
            ) : (
              timelineData?.doses.map((dose) => (
                <div
                  key={`${dose.schedule_id}-${dose.scheduled_time}`}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-xs space-y-3.5 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-850 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400 shrink-0">
                        <Clock className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-black text-slate-900 dark:text-slate-100">{dose.scheduled_time_formatted}</span>
                          {dose.time_label && (
                            <span className="text-[10px] font-bold text-slate-400 uppercase bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                              {dose.time_label}
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] font-bold text-slate-500">Prescribed by: {dose.prescribing_doctor_name || 'Attending Physician'}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-start sm:self-auto">
                      {getStatusBadge(dose.derived_status, dose.action_at, dose.marked_by_name)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase block">Medication & Dosage</span>
                      <p className="font-black text-slate-800 dark:text-slate-200 mt-0.5 text-sm flex items-center gap-1.5">
                        <Pill className="w-4 h-4 text-blue-600 shrink-0" />
                        {dose.medicine_name} ({dose.dosage || '1 dose'})
                      </p>
                    </div>
                    <div className="sm:col-span-2">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block">Clinical Administration Instructions</span>
                      <p className="text-slate-600 dark:text-slate-400 font-semibold mt-0.5">
                        {dose.instructions || 'Take with water as prescribed.'}
                      </p>
                    </div>
                  </div>

                  {/* Notes / Marked By Info */}
                  {dose.notes && (
                    <div className="p-2.5 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-850 text-xs text-slate-600 dark:text-slate-400">
                      <span className="font-bold text-[10px] uppercase text-slate-400 block">Observation Note:</span>
                      {dose.notes}
                    </div>
                  )}

                  {/* Action Buttons for Patient & Caregiver */}
                  {dose.is_actionable && !isFamily && !isDoctor && (
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-850">
                      <button
                        onClick={() => setActionModal({ isOpen: true, type: 'skip', dose, note: '' })}
                        disabled={actionLoadingId === dose.schedule_id}
                        className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-colors border-none cursor-pointer flex items-center gap-1.5"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Skip Dose</span>
                      </button>
                      <button
                        onClick={() => setActionModal({ isOpen: true, type: 'take', dose, note: '' })}
                        disabled={actionLoadingId === dose.schedule_id}
                        className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors border-none cursor-pointer flex items-center gap-1.5"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Mark as Taken</span>
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Unconfigured Prescriptions (Schedule Pending Setup) */}
          {timelineData?.unconfigured_prescriptions && timelineData.unconfigured_prescriptions.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
              <h3 className="text-xs font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest pl-1 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Active Prescriptions Pending Schedule Setup
              </h3>
              <div className="grid grid-cols-1 gap-3">
                {timelineData.unconfigured_prescriptions.map((rx) => (
                  <div key={rx.id} className="bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div>
                      <span className="font-black text-slate-900 dark:text-slate-100 text-sm block">{rx.medicines}</span>
                      <span className="text-slate-500 font-semibold">Frequency: <strong>{rx.frequency}</strong> • Dosage: {rx.dosage}</span>
                      <span className="text-[11px] text-amber-700 dark:text-amber-400 block mt-1">
                        ℹ️ Schedule Pending Setup (Suggested times: {rx.frequency.toLowerCase().includes('twice') ? '08:00 AM, 08:00 PM' : rx.frequency.toLowerCase().includes('three') ? '08:00 AM, 02:00 PM, 08:00 PM' : '08:00 AM'})
                      </span>
                    </div>

                    {isDoctor && (
                      <button
                        onClick={() => {
                          const defTimes = rx.frequency.toLowerCase().includes('twice') ? ['08:00', '20:00'] : rx.frequency.toLowerCase().includes('three') ? ['08:00', '14:00', '20:00'] : ['08:00'];
                          setScheduleModal({ isOpen: true, rx, times: defTimes });
                        }}
                        className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer shrink-0 flex items-center gap-1.5"
                      >
                        <Plus className="w-4 h-4" />
                        <span>Configure Schedule</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Adherence Analytics Tab */
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-850 pb-4">
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">7-Day Rolling Adherence Breakdown</h3>
                <p className="text-xs text-slate-500 font-semibold mt-0.5">Tracking fidelity calculated across all scheduled dose occurrences.</p>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Overall Adherence</span>
                <span className="text-xl font-black text-blue-600 dark:text-blue-400 font-mono">
                  {adherenceData && adherenceData.adherence_rate !== null ? `${adherenceData.adherence_rate}%` : 'No data'}
                </span>
              </div>
            </div>

            {/* Daily History Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-850 text-slate-400 uppercase text-[10px] font-bold">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3 text-center">Taken</th>
                    <th className="py-2.5 px-3 text-center">Skipped</th>
                    <th className="py-2.5 px-3 text-center">Missed</th>
                    <th className="py-2.5 px-3 text-center">Eligible Doses</th>
                    <th className="py-2.5 px-3 text-right">Daily Adherence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold">
                  {adherenceData?.daily_breakdown?.map((day) => (
                    <tr key={day.date} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                      <td className="py-2.5 px-3 font-bold text-slate-800 dark:text-slate-200 font-mono">{day.date}</td>
                      <td className="py-2.5 px-3 text-center text-emerald-600 dark:text-emerald-400 font-bold">{day.taken}</td>
                      <td className="py-2.5 px-3 text-center text-amber-600 dark:text-amber-400">{day.skipped}</td>
                      <td className="py-2.5 px-3 text-center text-rose-600 dark:text-rose-400 font-bold">{day.missed}</td>
                      <td className="py-2.5 px-3 text-center text-slate-500">{day.eligible}</td>
                      <td className="py-2.5 px-3 text-right font-black text-slate-900 dark:text-slate-100 font-mono">
                        {day.adherence_rate !== null ? `${day.adherence_rate}%` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-850 text-[11px] text-slate-500 font-semibold">
              ⚖️ <strong>Technical Notice</strong>: Schedule Adherence is computed automatically from recorded doses (Taken / (Taken + Skipped + Missed)). Future pending doses do not reduce adherence score. This software tracking metric does not replace direct clinical consultation.
            </div>
          </div>
        </div>
      )}

      {/* Record Action Modal (Take / Skip) */}
      {actionModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                {actionModal.type === 'take' ? 'Confirm Dose Administration' : 'Record Skipped Dose'}
              </h3>
              <button onClick={() => setActionModal({ isOpen: false, type: 'take', dose: null, note: '' })} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>

            <div className="text-xs space-y-2">
              <p className="font-semibold text-slate-700 dark:text-slate-300">
                Medication: <strong>{actionModal.dose?.medicine_name}</strong> ({actionModal.dose?.dosage})
              </p>
              <p className="text-slate-500">
                Scheduled Time: <strong>{actionModal.dose?.scheduled_time_formatted}</strong>
              </p>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mt-3 mb-1">
                  {actionModal.type === 'take' ? 'Optional Notes / Observation' : 'Reason for Skipping *'}
                </label>
                <textarea
                  placeholder={actionModal.type === 'take' ? 'e.g. Taken after breakfast with full glass of water' : 'e.g. Mild nausea, fasting for lab test'}
                  value={actionModal.note}
                  onChange={(e) => setActionModal({ ...actionModal, note: e.target.value })}
                  className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-semibold h-20 text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={() => setActionModal({ isOpen: false, type: 'take', dose: null, note: '' })}
                className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleRecordAction}
                className={`px-4 py-2 text-white font-bold text-xs rounded-xl border-none cursor-pointer ${
                  actionModal.type === 'take' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-amber-600 hover:bg-amber-700'
                }`}
              >
                {actionModal.type === 'take' ? 'Confirm Taken' : 'Confirm Skipped'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Doctor Configure Schedule Modal */}
      {scheduleModal.isOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Configure Medication Schedule</h3>
              <button onClick={() => setScheduleModal({ isOpen: false, rx: null, times: ['08:00'] })} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleSaveSchedule} className="text-xs space-y-3">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Prescription</span>
                <p className="font-black text-slate-900 dark:text-slate-100 mt-0.5 text-sm">{scheduleModal.rx?.medicines}</p>
                <span className="text-slate-500 font-semibold">Frequency: {scheduleModal.rx?.frequency}</span>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Scheduled Administration Times (24h HH:MM)</label>
                {scheduleModal.times.map((t, idx) => (
                  <div key={idx} className="flex items-center gap-2 mb-2">
                    <input
                      type="time"
                      value={t}
                      onChange={(e) => {
                        const nextTimes = [...scheduleModal.times];
                        nextTimes[idx] = e.target.value;
                        setScheduleModal({ ...scheduleModal, times: nextTimes });
                      }}
                      className="p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold text-xs flex-1"
                    />
                    {scheduleModal.times.length > 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          const nextTimes = scheduleModal.times.filter((_, i) => i !== idx);
                          setScheduleModal({ ...scheduleModal, times: nextTimes });
                        }}
                        className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg border-none bg-transparent cursor-pointer"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}

                <button
                  type="button"
                  onClick={() => setScheduleModal({ ...scheduleModal, times: [...scheduleModal.times, '12:00'] })}
                  className="text-xs font-bold text-blue-600 hover:text-blue-700 bg-transparent border-none cursor-pointer flex items-center gap-1 mt-1"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Time Slot
                </button>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-850">
                <button
                  type="button"
                  onClick={() => setScheduleModal({ isOpen: false, rx: null, times: ['08:00'] })}
                  className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer"
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MedicinesPage;
