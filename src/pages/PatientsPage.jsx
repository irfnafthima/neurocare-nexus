import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import {
  Users,
  Search,
  Activity,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Clock,
  Check,
  X,
  UserCheck,
  RefreshCw,
  Heart
} from 'lucide-react';

export const PatientsPage = () => {
  const { user, authFetch } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const isDoctor = userRole === 'doctor';
  const isCaregiver = userRole === 'caregiver';

  const initialTab = searchParams.get('tab') === 'pending' ? 'pending' : 'assigned';
  const [activeTab, setActiveTab] = useState(initialTab);

  const [patients, setPatients] = useState([]);
  const [connectionRequests, setConnectionRequests] = useState([]);
  const [caregiverRequests, setCaregiverRequests] = useState([]);
  const [accessCodeInput, setAccessCodeInput] = useState('');
  const [isLinking, setIsLinking] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'pending') {
      setActiveTab('pending');
    } else if (tabParam === 'assigned') {
      setActiveTab('assigned');
    }
  }, [searchParams]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [patientsRes, requestsRes, cgRequestsRes] = await Promise.all([
        authFetch(getApiUrl('/patients/')),
        isDoctor ? authFetch(getApiUrl('/connections/requests')) : Promise.resolve({ ok: false }),
        isCaregiver ? authFetch(getApiUrl('/caregiver-requests')) : Promise.resolve({ ok: false })
      ]);

      if (patientsRes.ok) {
        const data = await patientsRes.json();
        setPatients(Array.isArray(data) ? data : []);
      }

      if (requestsRes && requestsRes.ok) {
        const rData = await requestsRes.json();
        const rList = Array.isArray(rData) ? rData : (rData.requests || []);
        setConnectionRequests(rList);
      }

      if (cgRequestsRes && cgRequestsRes.ok) {
        const cgData = await cgRequestsRes.json();
        const cgList = Array.isArray(cgData) ? cgData : [];
        setCaregiverRequests(cgList);
      }
    } catch (err) {
      console.error('Error fetching patients data:', err);
      addToast('Network error while fetching patients.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [userRole]);

  const handleReviewPatient = (patientId) => {
    if (!patientId) return;
    sessionStorage.setItem('nexus_selected_patient_id', patientId);
    navigate(`/health-records?patientId=${patientId}`);
  };

  const handleCaregiverRequest = async (e) => {
    e.preventDefault();
    if (!accessCodeInput.trim()) return;
    try {
      setIsLinking(true);
      const res = await authFetch(getApiUrl('/caregiver-requests'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patientId: accessCodeInput.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        addToast(`Connection request sent to ${data.patientName || 'patient'} (${accessCodeInput.trim()})! Access activates once approved.`, 'success');
        setAccessCodeInput('');
        fetchData();
        setActiveTab('pending');
      } else {
        const err = await res.text();
        addToast(`Failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error sending connection request to patient.', 'error');
    } finally {
      setIsLinking(false);
    }
  };

  const handleApproveRequest = async (requestId, patientName) => {
    try {
      setActionLoadingId(requestId);
      const res = await authFetch(getApiUrl(`/connections/requests/${requestId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Approved' })
      });

      if (res.ok) {
        addToast(`Patient ${patientName || ''} approved and linked to your clinical roster!`, 'success');
        fetchData();
      } else {
        const err = await res.text();
        addToast(`Failed to approve request: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error approving patient link request.', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeclineRequest = async (requestId, patientName) => {
    try {
      setActionLoadingId(requestId);
      const res = await authFetch(getApiUrl(`/connections/requests/${requestId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'Declined' })
      });

      if (res.ok) {
        addToast(`Connection request from ${patientName || 'patient'} declined.`, 'info');
        fetchData();
      } else {
        const err = await res.text();
        addToast(`Failed to decline request: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error declining patient link request.', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const pendingDoctorRequests = connectionRequests.filter(r => (r.status || '').toLowerCase() === 'pending');
  const pendingCaregiverRequests = caregiverRequests.filter(r => !r.isApproved);
  const pendingCount = isDoctor ? pendingDoctorRequests.length : (isCaregiver ? pendingCaregiverRequests.length : 0);

  const filteredPatients = patients.filter((p) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    const nameMatch = (p.name || '').toLowerCase().includes(q);
    const idMatch = (p.id || '').toLowerCase().includes(q);
    const condMatch = (p.condition || '').toLowerCase().includes(q);
    return nameMatch || idMatch || condMatch;
  });

  const filteredPending = pendingDoctorRequests.filter((r) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    const nameMatch = (r.patientName || '').toLowerCase().includes(q);
    const idMatch = (r.patientId || '').toLowerCase().includes(q);
    return nameMatch || idMatch;
  });

  const formatTimestamp = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return `${d.toLocaleDateString()} • ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } catch {
      return ts;
    }
  };

  return (
    <div className="space-y-6 text-left max-w-6xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 p-6 rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200/60 dark:border-blue-900/60 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-950 dark:text-slate-100 tracking-tight">
                {isCaregiver ? 'Caregiver Patient Roster & Linking' : 'Patients & Clinical Access Directory'}
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
                {isCaregiver 
                  ? 'Connect to patients via their Access Code and monitor authorized vital streams.' 
                  : 'Manage assigned patient rosters, review incoming link requests, and access telemetry records.'}
              </p>
            </div>
          </div>
        </div>

        {/* Search Bar & Refresh */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search patient name, ID, or condition..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium"
            />
          </div>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-600 dark:text-slate-300 transition-colors border-none cursor-pointer shrink-0"
            title="Refresh Directory"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Caregiver Link Patient via Access Code Card */}
      {isCaregiver && (
        <div className="bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-purple-500/10 border border-blue-200/80 dark:border-blue-900/50 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[10px] font-black uppercase tracking-wider text-blue-600 dark:text-blue-400 block">
                Connect To Patient
              </span>
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 mt-0.5">
                Link Patient Using Access Code
              </h3>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                Ask the patient for their Patient Access Code (e.g. <span className="font-mono font-bold text-blue-600">P-13</span>, <span className="font-mono font-bold text-blue-600">P-105</span>, <span className="font-mono font-bold text-blue-600">P-139</span>) to send an access request.
              </p>
            </div>
          </div>

          <form onSubmit={handleCaregiverRequest} className="flex flex-col sm:flex-row gap-2.5 pt-1">
            <input
              type="text"
              placeholder="Enter Patient Access Code (e.g. P-13, P-105, NP-139)..."
              value={accessCodeInput}
              onChange={(e) => setAccessCodeInput(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 shadow-xs"
            />
            <button
              type="submit"
              disabled={isLinking || !accessCodeInput.trim()}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-black uppercase tracking-wider border-none cursor-pointer transition-colors shadow-xs flex items-center justify-center gap-2 shrink-0"
            >
              {isLinking ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              <span>Send Connection Request</span>
            </button>
          </form>
        </div>
      )}

      {/* Tabs Toolbar (for Doctors and Caregivers) */}
      {(isDoctor || isCaregiver) && (
        <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
          <button
            onClick={() => {
              setActiveTab('assigned');
              setSearchParams({});
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border-none cursor-pointer ${
              activeTab === 'assigned'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Assigned Patients ({patients.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('pending');
              setSearchParams({ tab: 'pending' });
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border-none cursor-pointer relative ${
              activeTab === 'pending'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>{isCaregiver ? 'Sent Access Requests' : 'Pending Requests'}</span>
            {pendingCount > 0 && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                activeTab === 'pending' ? 'bg-white text-amber-700' : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
              }`}>
                {pendingCount}
              </span>
            )}
          </button>
        </div>
      )}

      {/* TAB 1: ASSIGNED PATIENTS */}
      {activeTab === 'assigned' && (
        <>
          {isLoading && patients.length === 0 ? (
            <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl">
              <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-2 text-blue-600" />
              Loading authorized patient roster...
            </div>
          ) : filteredPatients.length === 0 ? (
            <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl space-y-2">
              <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="font-bold text-slate-600 dark:text-slate-300">No matching authorized patients found.</p>
              <p className="text-[11px]">
                {isCaregiver 
                  ? 'Enter a Patient Access Code above to request access to their telemetry dashboard.' 
                  : 'Only patients with an approved clinical connection are visible in your directory.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredPatients.map((patient) => {
                const isCritical = (patient.risk || 0) >= 70 || patient.status === 'Critical';
                const isMod = (patient.risk || 0) >= 40 && (patient.risk || 0) < 70;

                return (
                  <div
                    key={patient.id}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4"
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-base font-black text-slate-950 dark:text-slate-100">
                            {patient.name}
                          </h3>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                              {patient.id}
                            </span>
                            <span className="text-slate-300 dark:text-slate-700">•</span>
                            <span className="text-[11px] text-slate-500 font-semibold">
                              Age: {patient.age || 'N/A'} • {patient.gender || 'Other'}
                            </span>
                          </div>
                        </div>

                        <span
                          className={`text-[9px] font-black uppercase px-2.5 py-1 rounded-full border ${
                            isCritical
                              ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900/50'
                              : isMod
                              ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900/50'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50'
                          }`}
                        >
                          {patient.status || 'Active'}
                        </span>
                      </div>

                      <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl space-y-1.5 border border-slate-100 dark:border-slate-800">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400 font-bold uppercase text-[10px]">Condition:</span>
                          <span className="font-bold text-slate-800 dark:text-slate-200 text-right truncate max-w-[180px]">
                            {patient.condition || 'General Care'}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400 font-bold uppercase text-[10px]">Room / Unit:</span>
                          <span className="font-bold text-slate-700 dark:text-slate-300 font-mono">
                            {patient.room || 'Room 101'}
                          </span>
                        </div>
                        {patient.blood_group && (
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-400 font-bold uppercase text-[10px]">Blood Group:</span>
                            <span className="font-bold text-rose-600 dark:text-rose-400">
                              {patient.blood_group}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Authorized</span>
                      </div>

                      <button
                        onClick={() => handleReviewPatient(patient.id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm shadow-blue-500/10 cursor-pointer"
                      >
                        <span>Review Patient</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* TAB 2: PENDING PATIENT REQUESTS */}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          {/* Caregiver view of their sent requests */}
          {isCaregiver ? (
            <div>
              {pendingCaregiverRequests.length === 0 ? (
                <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl space-y-2">
                  <UserCheck className="w-9 h-9 text-slate-400 mx-auto" />
                  <p className="font-bold text-slate-700 dark:text-slate-300">No pending access requests.</p>
                  <p className="text-[11px] text-slate-400">Use the Access Code input above to send an authorization request to a patient.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pendingCaregiverRequests.map((req) => (
                    <div
                      key={req.id}
                      className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-900/50 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-base font-black text-slate-950 dark:text-slate-100">
                              {req.patientName || 'Patient'}
                            </h3>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">
                                Patient Access Code: {req.patientId}
                              </span>
                            </div>
                          </div>

                          <span className="text-[9px] font-black uppercase px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Awaiting Patient Approval
                          </span>
                        </div>

                        <div className="p-3 bg-slate-50 dark:bg-slate-850/60 rounded-xl space-y-1 border border-slate-100 dark:border-slate-800 text-xs">
                          <p className="text-slate-700 dark:text-slate-300 font-medium">
                            Connection request sent. The patient can accept this request on their Access Controls dashboard to authorize your monitoring access.
                          </p>
                          {req.createdAt && (
                            <span className="text-[10px] text-slate-400 font-semibold block pt-1">
                              Sent: {formatTimestamp(req.createdAt)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Doctor view of incoming requests */
            <div>
              {isLoading && pendingDoctorRequests.length === 0 ? (
                <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl">
                  <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-2 text-amber-600" />
                  Loading pending connection requests...
                </div>
              ) : filteredPending.length === 0 ? (
                <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl space-y-2">
                  <UserCheck className="w-9 h-9 text-slate-400 mx-auto" />
                  <p className="font-bold text-slate-700 dark:text-slate-300">No pending patient connection requests.</p>
                  <p className="text-[11px] text-slate-400">All incoming patient link requests have been reviewed.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredPending.map((req) => (
                    <div
                      key={req.id}
                      className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-900/50 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-base font-black text-slate-950 dark:text-slate-100">
                              {req.patientName || 'Unknown Patient'}
                            </h3>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-xs font-bold text-amber-600 dark:text-amber-400">
                                {req.patientId}
                              </span>
                              <span className="text-slate-300 dark:text-slate-700">•</span>
                              <span className="text-[11px] text-slate-500 font-semibold">
                                Age: {req.age || 'N/A'} • {req.gender || 'Unspecified'}
                              </span>
                            </div>
                          </div>

                          <span className="text-[9px] font-black uppercase px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Pending Approval
                          </span>
                        </div>

                        <div className="p-3 bg-slate-50 dark:bg-slate-850/60 rounded-xl space-y-1 border border-slate-100 dark:border-slate-800 text-xs">
                          <span className="text-[10px] font-black uppercase text-slate-400 block">Request Note:</span>
                          <p className="text-slate-700 dark:text-slate-300 font-medium italic">
                            "{req.requestMessage || req.generalReason || 'Requesting clinical supervision and telemetry oversight.'}"
                          </p>
                          {req.createdAt && (
                            <span className="text-[10px] text-slate-400 font-semibold block pt-1">
                              Received: {formatTimestamp(req.createdAt)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-2.5">
                        <button
                          onClick={() => handleDeclineRequest(req.id, req.patientName)}
                          disabled={actionLoadingId === req.id}
                          className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold transition-all border-none cursor-pointer flex items-center gap-1.5"
                        >
                          <X className="w-3.5 h-3.5 text-rose-500" />
                          <span>Decline</span>
                        </button>

                        <button
                          onClick={() => handleApproveRequest(req.id, req.patientName)}
                          disabled={actionLoadingId === req.id}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all border-none cursor-pointer shadow-sm flex items-center gap-1.5"
                        >
                          {actionLoadingId === req.id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          <span>Approve & Link Patient</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PatientsPage;
