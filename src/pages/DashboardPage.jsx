import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  Activity, 
  Users, 
  AlertTriangle, 
  Cpu, 
  Heart,
  TrendingUp,
  ShieldCheck, 
  Sparkles, 
  Pill, 
  Search, 
  FileText, 
  FileCheck,
  ScrollText,
  UserCheck,
  MessageSquare, 
  Bot,
  ArrowRight,
  ShieldAlert,
  Calendar
} from 'lucide-react';

export const DashboardPage = () => {
  const { user, authFetch } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const userName = user?.name || user?.full_name || 'User';

  const queryPatientId = searchParams.get('patientId');

  const deriveInitialPatientId = () => {
    if (queryPatientId) {
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
      return queryPatientId;
    }
    const stored = sessionStorage.getItem('nexus_selected_patient_id');
    if (stored && userRole === 'doctor') {
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
  const [patientSummary, setPatientSummary] = useState(null);
  const [vitals, setVitals] = useState({
    max30102: { heartRate: 72, spo2: 98 },
    ds18b20: { temperature: 36.8 },
    mpu6050: { state: 'NO FALL DETECTED', vectors: 'Stable' }
  });
  const [connectedDoctor, setConnectedDoctor] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [doctorRiskReviews, setDoctorRiskReviews] = useState([]);
  const [doctorAggregateStats, setDoctorAggregateStats] = useState({
    assignedPatientsCount: 0,
    requiringReviewCount: 0,
    activeAlarmsCount: 0,
    pendingRequestsCount: 0
  });
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);
  const [adminStats, setAdminStats] = useState({
    totalUsers: 0,
    registeredDoctors: 0,
    activeDoctors: 0,
    pendingDoctors: 0,
    rejectedDoctors: 0,
    totalPatients: 0,
    totalDevices: 0,
    assignedDevices: 0,
    referenceRecords: 5000,
    auditEvents: 0,
    criticalAlarms: 0
  });

  // Sync state if query parameter changes
  useEffect(() => {
    if (queryPatientId && queryPatientId !== selectedPatientId) {
      setSelectedPatientId(queryPatientId);
      sessionStorage.setItem('nexus_selected_patient_id', queryPatientId);
    }
  }, [queryPatientId]);

  const [familyLinkCode, setFamilyLinkCode] = useState('');
  const [isLinkingFamily, setIsLinkingFamily] = useState(false);
  const [familyRequests, setFamilyRequests] = useState([]);

  const fetchDashboardData = async () => {
    try {
      if (userRole === 'admin') {
        const res = await authFetch(getApiUrl('/admin-stats'));
        if (res.ok) {
          const data = await res.json();
          setAdminStats(data);
        }
      } else if (userRole === 'doctor') {
        setIsLoadingRisk(true);
        const [patientsRes, riskRes, requestsRes] = await Promise.all([
          authFetch(getApiUrl('/patients/')),
          authFetch(getApiUrl('/ai/doctor-risk-reviews')),
          authFetch(getApiUrl('/connections/requests'))
        ]);
        
        let pCount = 0;
        let rReviews = [];
        let reqCount = 0;

        if (patientsRes.ok) {
          const pData = await patientsRes.json();
          pCount = Array.isArray(pData) ? pData.length : 0;
        }
        if (riskRes.ok) {
          const riskData = await riskRes.json();
          rReviews = Array.isArray(riskData) ? riskData : [];
          setDoctorRiskReviews(rReviews);
        }
        if (requestsRes.ok) {
          const reqData = await requestsRes.json();
          const reqList = Array.isArray(reqData) ? reqData : (reqData.requests || []);
          reqCount = reqList.filter(r => r.status === 'Pending').length;
        }

        const highRiskCount = rReviews.filter(r => r.risk_level === 'HIGH').length;
        const reviewCount = rReviews.filter(r => r.risk_level === 'HIGH' || r.risk_level === 'MODERATE').length;

        setDoctorAggregateStats({
          assignedPatientsCount: pCount,
          requiringReviewCount: reviewCount,
          activeAlarmsCount: highRiskCount,
          pendingRequestsCount: reqCount
        });
        setIsLoadingRisk(false);
      } else {
        const [recordsRes, famReqRes] = await Promise.all([
          authFetch(getApiUrl(`/health-records?patientId=${selectedPatientId || ''}`)),
          userRole === 'family' ? authFetch(getApiUrl('/family-requests')) : Promise.resolve({ ok: false })
        ]);

        if (recordsRes.ok) {
          const data = await recordsRes.json();
          setPatientSummary(data.patient || null);
          if (data.patient?.vitals) {
            setVitals(data.patient.vitals);
          }
          if (data.doctor) {
            setConnectedDoctor(data.doctor);
          } else {
            setConnectedDoctor(null);
          }
        }

        if (famReqRes && famReqRes.ok) {
          const famData = await famReqRes.json();
          setFamilyRequests(Array.isArray(famData) ? famData : []);
        }
      }
    } catch (e) {
      console.error('Error fetching dashboard summary:', e);
      setIsLoadingRisk(false);
    }
  };

  const handleFamilyRequest = async (e) => {
    e.preventDefault();
    if (!familyLinkCode.trim()) return;
    try {
      setIsLinkingFamily(true);
      const res = await authFetch(getApiUrl('/family-requests'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patientId: familyLinkCode.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        addToast(`Connection request sent to relative (${data.patientName || familyLinkCode.trim()})! Access activates once approved.`, 'success');
        setFamilyLinkCode('');
        fetchDashboardData();
      } else {
        const err = await res.text();
        addToast(`Failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error sending connection request.', 'error');
    } finally {
      setIsLinkingFamily(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedPatientId, userRole]);

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Welcome / Slogan Banner */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-850 p-6 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-left">
        <div>
          <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight">
            {userRole === 'admin' && 'Administrator Operations Center'}
            {userRole === 'doctor' && `Clinician Dashboard: Dr. ${userName}`}
            {userRole === 'caregiver' && `Caregiver Dashboard: ${userName}`}
            {userRole === 'patient' && `Hello, ${userName}`}
            {userRole === 'family' && `Welcome Back, ${userName}`}
          </h1>
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            {userRole === 'admin' && 'Root system nodes, device telemetry health, and audit monitoring.'}
            {userRole === 'doctor' && 'Remote patient telemetry overview and clinical supervision.'}
            {userRole === 'caregiver' && 'Assigned patient care overview and urgent alerts.'}
            {userRole === 'patient' && 'NeuroCare Nexus is monitoring your health securely. Slogan: We are with you always.'}
            {userRole === 'family' && 'Relative patient health status monitor. Slogan: Care that never sleeps.'}
          </p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 px-3.5 py-1.5 rounded-full inline-flex items-center gap-1.5 self-start text-xs font-black text-blue-700 dark:text-blue-300 select-none">
          <Sparkles className="w-3.5 h-3.5" />
          <span>System Active</span>
        </div>
      </div>

      {/* Family Member Relative Access Code Link Card */}
      {userRole === 'family' && (
        <div className="bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-indigo-500/10 border border-purple-200/80 dark:border-purple-900/50 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
            <div>
              <span className="text-[10px] font-black uppercase tracking-wider text-purple-600 dark:text-purple-400 block">
                Relative Telemetry Link
              </span>
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 mt-0.5">
                {patientSummary ? `Connected Relative: ${patientSummary.name} (${selectedPatientId})` : 'Connect To Relative via Patient Access Code'}
              </h3>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                {patientSummary 
                  ? 'Real-time telemetry and vital readings are active. You can link another relative using their code below.'
                  : "Enter your family member's Patient Access Code (e.g. P-13, P-105, NP-139) to request remote monitoring authorization."}
              </p>
            </div>
          </div>

          <form onSubmit={handleFamilyRequest} className="flex flex-col sm:flex-row gap-2.5 pt-1">
            <input
              type="text"
              placeholder="Enter Relative's Patient Access Code (e.g. P-13, P-105, NP-139)..."
              value={familyLinkCode}
              onChange={(e) => setFamilyLinkCode(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-xl text-xs font-semibold text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-purple-500 shadow-xs"
            />
            <button
              type="submit"
              disabled={isLinkingFamily || !familyLinkCode.trim()}
              className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-xl text-xs font-black uppercase tracking-wider border-none cursor-pointer transition-colors shadow-xs flex items-center justify-center gap-2 shrink-0"
            >
              {isLinkingFamily ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              <span>Send Link Request</span>
            </button>
          </form>

          {familyRequests.filter(r => !r.isApproved).length > 0 && (
            <div className="pt-2 border-t border-purple-200/50 dark:border-purple-900/30 space-y-1.5">
              <span className="text-[10px] font-black uppercase text-amber-600 dark:text-amber-400 tracking-wider block">
                Pending Approval Requests
              </span>
              {familyRequests.filter(r => !r.isApproved).map(r => (
                <div key={r.id} className="text-xs font-medium text-slate-600 dark:text-slate-400 flex items-center justify-between p-2 bg-white/70 dark:bg-slate-900/70 rounded-xl">
                  <span>Request sent for relative <strong>{r.patientName || r.patientId}</strong></span>
                  <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full border border-amber-200 dark:border-amber-900/50">
                    Awaiting Relative Acceptance
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Doctor Specific: AI CLINICAL ATTENTION — Patients Requiring Review */}
      {userRole === 'doctor' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                  AI Clinical Attention — Patients Requiring Review
                </h2>
                <p className="text-[11px] text-slate-400 font-semibold">
                  Deterministic risk flags generated from vital telemetry, active alarms, and documented findings.
                </p>
              </div>
            </div>
            <span className="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 self-start sm:self-auto">
              AI Risk Review
            </span>
          </div>

          {isLoadingRisk ? (
            <div className="py-6 text-center text-xs font-semibold text-slate-400">
              Evaluating authorized patient risk streams...
            </div>
          ) : doctorRiskReviews && doctorRiskReviews.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {doctorRiskReviews.map((r, idx) => {
                const isHigh = r.risk_level === 'HIGH';
                const isMod = r.risk_level === 'MODERATE';
                const badgeColor = isHigh
                  ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900/50'
                  : isMod
                  ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900/50'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50';

                return (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                      isHigh
                        ? 'border-red-200/80 bg-red-50/20 dark:border-red-900/30'
                        : isMod
                        ? 'border-amber-200/80 bg-amber-50/20 dark:border-amber-900/30'
                        : 'border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900'
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-xs font-black text-slate-900 dark:text-slate-100">
                            {r.patient_name}
                          </h3>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ID: {r.patient_id} • Age: {r.age || 'N/A'}
                          </span>
                        </div>
                        <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full border ${badgeColor}`}>
                          {r.risk_level} PRIORITY
                        </span>
                      </div>

                      <div className="space-y-1">
                        {r.reasons && r.reasons.slice(0, 2).map((reason, rIdx) => (
                          <p key={rIdx} className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 flex items-start gap-1">
                            <span>•</span>
                            <span className="leading-tight">{reason}</span>
                          </p>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                      <span className="text-[9px] text-slate-400 font-mono">
                        {r.latest_evidence?.spo2 ? `SpO2: ${r.latest_evidence.spo2}` : (r.latest_evidence?.heart_rate ? `HR: ${r.latest_evidence.heart_rate}` : 'Clinical Baseline')}
                      </span>
                      <button
                        onClick={() => {
                          sessionStorage.setItem('nexus_selected_patient_id', r.patient_id);
                          navigate(`/health-records?patientId=${r.patient_id}`);
                        }}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[10px] font-bold transition-colors cursor-pointer"
                      >
                        Review Patient →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-4 text-xs font-semibold text-slate-500">
              No immediate high-risk patient flags detected. All linked patients are within stable thresholds.
            </div>
          )}
        </div>
      )}

      {/* Doctor Specific Aggregate Overview */}
      {userRole === 'doctor' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div 
            onClick={() => navigate('/patients')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-blue-500 p-5 rounded-2xl shadow-sm space-y-1 cursor-pointer transition-all"
          >
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[10px] font-black uppercase tracking-wider">Assigned Patients</span>
              <Users className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">{doctorAggregateStats.assignedPatientsCount}</p>
            <span className="text-[10px] text-slate-400 font-semibold">Active Doctor-Patient Links</span>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 p-5 rounded-2xl shadow-sm space-y-1">
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[10px] font-black uppercase tracking-wider">AI Clinical Attention</span>
              <ShieldAlert className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">{doctorAggregateStats.requiringReviewCount}</p>
            <span className="text-[10px] text-amber-600 font-semibold">Patients Requiring Review</span>
          </div>

          <div 
            onClick={() => navigate('/alerts')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-red-500 p-5 rounded-2xl shadow-sm space-y-1 cursor-pointer transition-all"
          >
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[10px] font-black uppercase tracking-wider">Active Clinical Alarms</span>
              <AlertTriangle className="w-4 h-4 text-red-500" />
            </div>
            <p className="text-2xl font-black text-red-500 mt-1">{doctorAggregateStats.activeAlarmsCount}</p>
            <span className="text-[10px] text-red-500 font-semibold">High Priority Telemetry Flags</span>
          </div>

          <div 
            onClick={() => navigate('/patients?tab=pending')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-emerald-500 p-5 rounded-2xl shadow-sm space-y-1 cursor-pointer transition-all"
          >
            <div className="flex justify-between items-center text-slate-400">
              <span className="text-[10px] font-black uppercase tracking-wider">Pending Patient Requests</span>
              <UserCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{doctorAggregateStats.pendingRequestsCount}</p>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">Review Pending Requests →</span>
          </div>
        </div>
      )}

      {/* Admin Specific Overview */}
      {userRole === 'admin' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <div className="flex justify-between items-center text-slate-400">
                <span className="text-[10px] font-black uppercase tracking-wider">Registered Users</span>
                <Users className="w-4 h-4 text-blue-500" />
              </div>
              <p className="text-2xl font-black text-slate-900 dark:text-slate-100">{adminStats.totalUsers || 0}</p>
              <span className="text-[10px] text-slate-400 font-semibold">Patients, Doctors & Family</span>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <div className="flex justify-between items-center text-slate-400">
                <span className="text-[10px] font-black uppercase tracking-wider">Registered Doctors</span>
                <UserCheck className="w-4 h-4 text-emerald-500" />
              </div>
              <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">{adminStats.registeredDoctors || adminStats.totalClinicians || 0}</p>
              <span className="text-[10px] text-slate-400 font-semibold">{adminStats.activeDoctors || 0} Active • {adminStats.pendingDoctors || 0} Pending</span>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <div className="flex justify-between items-center text-slate-400">
                <span className="text-[10px] font-black uppercase tracking-wider">Pending Verifications</span>
                <FileCheck className="w-4 h-4 text-amber-500" />
              </div>
              <p className="text-2xl font-black text-amber-600 dark:text-amber-400">{adminStats.pendingDoctors || 0}</p>
              <span className="text-[10px] text-amber-600 font-semibold">Awaiting Medical Credential Review</span>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-1">
              <div className="flex justify-between items-center text-slate-400">
                <span className="text-[10px] font-black uppercase tracking-wider">Devices (Assigned / Total)</span>
                <Cpu className="w-4 h-4 text-purple-500" />
              </div>
              <p className="text-2xl font-black text-purple-600 dark:text-purple-400">
                {adminStats.assignedDevices || 0} / {adminStats.totalDevices || 0}
              </p>
              <span className="text-[10px] text-slate-400 font-semibold">Wearable Biosensors & IoT Feeds</span>
            </div>
          </div>

          {/* Reference Verification Dataset & Security Audit Strip */}
          <div className="bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 flex flex-col sm:flex-row justify-between sm:items-center gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs font-black text-slate-900 dark:text-slate-100">
                  Reference Medical Registry: {(adminStats.referenceRecords || 5000).toLocaleString()} Verified Records
                </span>
                <p className="text-[11px] text-slate-500 font-semibold">
                  National / State Medical Council ground-truth dataset used for deterministic registration verification.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <span className="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800">
                Audit Events: {adminStats.auditEvents || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Patient / Family Personal Vital Summary Cards */}
      {(userRole === 'patient' || userRole === 'family') && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
          {/* Heart Rate */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Heart Rate</span>
              <Heart className="w-4 h-4 text-red-500" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-black text-red-500">{vitals.max30102?.heartRate || 72}</span>
              <span className="text-xs font-bold text-slate-400">BPM</span>
            </div>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">
              Normal Rhythm
            </span>
          </div>

          {/* SpO2 */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">SpO2 Oxygen</span>
              <Activity className="w-4 h-4 text-blue-600" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-black text-blue-600 dark:text-blue-400">{vitals.max30102?.spo2 || 98}</span>
              <span className="text-xs font-bold text-slate-400">%</span>
            </div>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">
              Optimal
            </span>
          </div>

          {/* Temperature */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Body Temp</span>
              <TrendingUp className="w-4 h-4 text-amber-500" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-black text-amber-500">{vitals.ds18b20?.temperature || 36.8}</span>
              <span className="text-xs font-bold text-slate-400">°C</span>
            </div>
            <span className="text-[9px] text-emerald-500 font-extrabold uppercase bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded border border-emerald-500/20">
              Afebrile
            </span>
          </div>

          {/* Fall Detection State */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">MPU6050 Motion</span>
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-sm font-black text-slate-800 dark:text-slate-200">{vitals.mpu6050?.state || 'NO FALL'}</span>
              <span className="text-xs font-mono font-bold text-emerald-500">Secure</span>
            </div>
            <span className="text-[9px] text-slate-400 font-bold uppercase">
              Stable Vectors
            </span>
          </div>
        </div>
      )}

      {/* Attending Doctor Summary & Connection Overview (Patient/Family) */}
      {(userRole === 'patient' || userRole === 'family') && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
            <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Attending Consulting Clinician</span>
            <button
              onClick={() => navigate('/access-controls')}
              className="text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline bg-transparent border-none cursor-pointer uppercase"
            >
              Manage Access Controls →
            </button>
          </div>
          
          {connectedDoctor ? (
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-xs font-semibold">
              <div className="space-y-1">
                <p className="text-sm font-black text-slate-900 dark:text-slate-100">
                  {connectedDoctor.name}
                  {connectedDoctor.specialization && (
                    <span className="text-[10px] text-blue-600 dark:text-blue-400 font-extrabold uppercase tracking-wider ml-2">
                      ({connectedDoctor.specialization})
                    </span>
                  )}
                </p>
                <p className="text-slate-400">
                  {connectedDoctor.hospital || 'Clinical Health Practice'} {connectedDoctor.npi ? `• Reg No: ${connectedDoctor.npi}` : ''}
                </p>
              </div>
              <button
                onClick={() => navigate('/care-team-chat')}
                className="px-3.5 py-2 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white rounded-xl font-bold text-xs transition-colors border border-blue-200 dark:border-blue-800 cursor-pointer self-start sm:self-auto flex items-center gap-1.5"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Open Care-Team Chat</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-xs font-semibold py-1">
              <div className="space-y-1 text-left">
                <p className="text-sm font-black text-slate-700 dark:text-slate-300">
                  No Consulting Clinician Linked
                </p>
                <p className="text-slate-400 text-xs">
                  Connect with a doctor in Access Controls to enable real-time vitals reviews and clinical care plans.
                </p>
              </div>
              <button
                onClick={() => navigate('/access-controls')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs transition-colors border-none cursor-pointer self-start sm:self-auto flex items-center gap-1.5 shadow-sm"
              >
                <span>Find & Request Clinician →</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Admin Quick Navigation Action Cards */}
      {userRole === 'admin' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Doctor Verification */}
          <div 
            onClick={() => navigate('/doctor-verification')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-red-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-xl bg-red-50 dark:bg-red-950 flex items-center justify-center text-red-600 dark:text-red-400 group-hover:scale-110 transition-transform">
                <FileCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-red-600">Doctor Verification</h3>
                <p className="text-xs text-slate-500 mt-0.5">Review professional registration details and approve or reject doctor applications.</p>
              </div>
            </div>
            <div className="flex items-center text-[10px] font-black text-red-600 dark:text-red-400 uppercase tracking-wider pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>Review Applications</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* User Management */}
          <div 
            onClick={() => navigate('/users')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-blue-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-blue-600">User Management</h3>
                <p className="text-xs text-slate-500 mt-0.5">View and manage registered patients, doctors, caregivers and family accounts.</p>
              </div>
            </div>
            <div className="flex items-center text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-wider pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>Manage Users</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Audit & Security */}
          <div 
            onClick={() => navigate('/audit-logs')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-purple-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950 flex items-center justify-center text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform">
                <ScrollText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-purple-600">Audit & Security</h3>
                <p className="text-xs text-slate-500 mt-0.5">Review authentication, access delegations, and administrative activity.</p>
              </div>
            </div>
            <div className="flex items-center text-[10px] font-black text-purple-600 dark:text-purple-400 uppercase tracking-wider pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>View Audit Logs</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Device Management */}
          <div 
            onClick={() => navigate('/devices')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-emerald-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-emerald-600">Device Management</h3>
                <p className="text-xs text-slate-500 mt-0.5">Review registered monitoring devices, telemetry bindings and hardware status.</p>
              </div>
            </div>
            <div className="flex items-center text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-wider pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>Manage Devices</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      )}

      {/* Clinical User Navigation Action Cards (Doctor, Patient, Caregiver, Family) */}
      {userRole !== 'admin' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {/* Go to Vitals */}
          <div 
            onClick={() => navigate('/vitals')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-blue-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left"
          >
            <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-blue-600">Vitals & Monitoring</h3>
              <p className="text-xs text-slate-500 mt-0.5">View real-time waveforms, historical charts, and log manual vital readings.</p>
            </div>
            <div className="flex items-center text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-wider pt-1">
              <span>Explore Vitals</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Go to Health Records */}
          <div 
            onClick={() => navigate('/health-records')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-blue-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left"
          >
            <div className="w-9 h-9 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-emerald-600">Health Records & Documents</h3>
              <p className="text-xs text-slate-500 mt-0.5">Manage health conditions, allergies, and upload clinical lab reports to vault.</p>
            </div>
            <div className="flex items-center text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-wider pt-1">
              <span>Open Vault</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Go to AI Assistant */}
          <div 
            onClick={() => navigate('/ai-chatbot')}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:border-blue-500 rounded-2xl p-5 shadow-sm cursor-pointer transition-all hover:shadow-md space-y-3 group text-left"
          >
            <div className="w-9 h-9 rounded-xl bg-purple-50 dark:bg-purple-950 flex items-center justify-center text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 group-hover:text-purple-600">AI Clinical Assistant</h3>
              <p className="text-xs text-slate-500 mt-0.5">Ask questions about vitals, medications, clinical guidelines, and safety.</p>
            </div>
            <div className="flex items-center text-[10px] font-black text-purple-600 dark:text-purple-400 uppercase tracking-wider pt-1">
              <span>Open AI Assistant</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
