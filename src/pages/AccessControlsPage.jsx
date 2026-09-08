import React, { useState, useEffect } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  Users, 
  Search, 
  UserCheck, 
  ShieldCheck, 
  Check, 
  X, 
  Clock, 
  AlertTriangle,
  FileCheck,
  ShieldAlert,
  Building2,
  Stethoscope,
  Trash2,
  RefreshCw,
  Eye
} from 'lucide-react';

export const AccessControlsPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();
  const location = useLocation();
  const [searchParams] = useSearchParams();

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
  const [accessControls, setAccessControls] = useState({
    doctors: [],
    pendingDoctors: [],
    caregivers: [],
    familyMembers: []
  });
  const [doctorsList, setDoctorsList] = useState([]);
  const [connectionRequests, setConnectionRequests] = useState([]);
  const [doctorSearchQuery, setDoctorSearchQuery] = useState('');
  const [caregiverLinkInput, setCaregiverLinkInput] = useState('');
  const [familyLinkInput, setFamilyLinkInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Admin specific state
  const deriveInitialAdminTab = () => {
    const tabParam = searchParams.get('tab');
    if (tabParam === 'users' || location.pathname === '/users') return 'users';
    return 'verification';
  };
  const [adminTab, setAdminTab] = useState(deriveInitialAdminTab);

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (location.pathname === '/users' || tabParam === 'users') {
      setAdminTab('users');
    } else if (location.pathname === '/doctor-verification' || tabParam === 'verification') {
      setAdminTab('verification');
    }
  }, [location.pathname, searchParams]);

  const [pendingDoctors, setPendingDoctors] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminSearchQuery, setAdminSearchQuery] = useState('');
  const [selectedDoctorDetails, setSelectedDoctorDetails] = useState(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const fetchAccessControls = async () => {
    try {
      setIsLoading(true);
      if (userRole === 'admin') {
        const [pendingRes, usersRes] = await Promise.all([
          authFetch(getApiUrl('/admin/pending-doctors')),
          authFetch(getApiUrl('/admin/users'))
        ]);
        if (pendingRes.ok) {
          const pData = await pendingRes.json();
          setPendingDoctors(pData || []);
        }
        if (usersRes.ok) {
          const uData = await usersRes.json();
          setAdminUsers(uData || []);
        }
      } else {
        // Fetch access controls for patient/family/doctor
        const res = await authFetch(getApiUrl(`/access-controls?patientId=${selectedPatientId || ''}`));
        if (res.ok) {
          const data = await res.json();
          setAccessControls(data);
        }

        // Fetch doctors directory for searching
        const docRes = await authFetch(getApiUrl('/doctors/directory'));
        if (docRes.ok) {
          const docData = await docRes.json();
          const list = Array.isArray(docData) ? docData : (docData.doctors || docData.results || []);
          setDoctorsList(list);
        }

        // Fetch connection requests
        const reqRes = await authFetch(getApiUrl('/connections/requests'));
        if (reqRes.ok) {
          const reqData = await reqRes.json();
          const reqList = Array.isArray(reqData) ? reqData : (reqData.requests || []);
          setConnectionRequests(reqList);
        }
      }
    } catch (e) {
      console.error('Error fetching access controls:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccessControls();
  }, [selectedPatientId, userRole]);

  // Admin Actions
  const handleApproveDoctor = async (doctorId) => {
    setActionLoading(doctorId);
    try {
      const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/approve`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        addToast('Doctor credentials approved successfully! Portal access enabled.', 'success');
        fetchAccessControls();
        setIsDetailsModalOpen(false);
      } else {
        const err = await res.text();
        addToast(`Approval failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error approving doctor account.', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectDoctor = async (doctorId) => {
    setActionLoading(doctorId);
    try {
      const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/reject`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Credentials verification failed or disciplinary block.' })
      });
      if (res.ok) {
        addToast('Doctor application rejected.', 'info');
        fetchAccessControls();
        setIsDetailsModalOpen(false);
      } else {
        const err = await res.text();
        addToast(`Rejection failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error rejecting doctor account.', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewDoctorDetails = async (doctorId) => {
    setActionLoading(doctorId);
    try {
      const res = await authFetch(getApiUrl(`/admin/doctors/${doctorId}/details`));
      if (res.ok) {
        const data = await res.json();
        setSelectedDoctorDetails(data);
        setIsDetailsModalOpen(true);
      } else {
        addToast('Could not load detailed verification report.', 'error');
      }
    } catch (e) {
      addToast('Error fetching doctor details.', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (userId, userEmail) => {
    if (!window.confirm(`Revoke and delete user ${userEmail}? This will terminate their portal access.`)) return;
    try {
      const res = await authFetch(getApiUrl(`/admin/users/${userId}`), { method: 'DELETE' });
      if (res.ok) {
        addToast('User access revoked successfully.', 'success');
        fetchAccessControls();
      } else {
        addToast('Failed to revoke user.', 'error');
      }
    } catch (e) {
      addToast('Error revoking user access.', 'error');
    }
  };

  // Patient / Caregiver / Family Actions
  const handleSendConnectionRequest = async (doctorNpi) => {
    try {
      const res = await authFetch(getApiUrl('/doctor-requests/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doctorNpi: doctorNpi,
          patientId: selectedPatientId,
          notes: 'Patient requesting clinical link'
        })
      });

      if (res.ok) {
        addToast('Connection request sent to doctor successfully.', 'success');
        fetchAccessControls();
      } else {
        const err = await res.text();
        addToast(`Failed to send request: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error sending connection request.', 'error');
    }
  };

  const handleCancelConnectionRequest = async (requestId) => {
    try {
      const res = await authFetch(getApiUrl(`/doctor-requests/${requestId}/`), {
        method: 'DELETE'
      });
      if (res.ok) {
        addToast('Connection request cancelled.', 'info');
        fetchAccessControls();
      } else {
        addToast('Failed to cancel request.', 'error');
      }
    } catch (e) {
      addToast('Error cancelling connection request.', 'error');
    }
  };

  const handleConnectCaregiver = async (e) => {
    e.preventDefault();
    if (!caregiverLinkInput.trim()) return;
    try {
      const res = await authFetch(getApiUrl('/access-controls/caregiver/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientId: selectedPatientId,
          caregiverIdentifier: caregiverLinkInput.trim()
        })
      });
      if (res.ok) {
        addToast('Caregiver link invitation registered.', 'success');
        setCaregiverLinkInput('');
        fetchAccessControls();
      } else {
        const err = await res.text();
        addToast(`Failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error linking caregiver.', 'error');
    }
  };

  const handleRevokeCaregiver = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/access-controls/caregiver/${id}/`), { method: 'DELETE' });
      if (res.ok) {
        addToast('Caregiver access revoked.', 'info');
        fetchAccessControls();
      }
    } catch (e) {
      addToast('Error revoking caregiver access.', 'error');
    }
  };

  const handleConnectFamily = async (e) => {
    e.preventDefault();
    if (!familyLinkInput.trim()) return;
    try {
      const res = await authFetch(getApiUrl('/access-controls/family/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientId: selectedPatientId,
          familyIdentifier: familyLinkInput.trim()
        })
      });
      if (res.ok) {
        addToast('Family member access granted.', 'success');
        setFamilyLinkInput('');
        fetchAccessControls();
      } else {
        const err = await res.text();
        addToast(`Failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error linking family member.', 'error');
    }
  };

  const handleRevokeFamily = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/access-controls/family/${id}/`), { method: 'DELETE' });
      if (res.ok) {
        addToast('Family access revoked.', 'info');
        fetchAccessControls();
      }
    } catch (e) {
      addToast('Error revoking family access.', 'error');
    }
  };

  // RENDER ADMIN VIEW
  if (userRole === 'admin') {
    return (
      <div className="space-y-6 text-left max-w-6xl mx-auto font-sans select-none">
        {/* Admin Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <ShieldCheck className="w-6 h-6 text-red-600 dark:text-red-400" />
              Administrative Verification & User Access Control
            </h1>
            <p className="text-xs font-semibold text-slate-500 mt-1">
              Verify medical credentials against State Medical Council registries and manage enterprise access permissions.
            </p>
          </div>
          <button
            onClick={fetchAccessControls}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold hover:bg-slate-200 transition-colors border-none cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 p-1.5 bg-slate-100 dark:bg-slate-900 rounded-2xl w-fit border border-slate-200/50 dark:border-slate-800">
          <button
            onClick={() => setAdminTab('verification')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all border-none cursor-pointer ${
              adminTab === 'verification'
                ? 'bg-red-600 text-white shadow-md'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 bg-transparent'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            Doctor Verification Queue ({pendingDoctors.length})
          </button>
          <button
            onClick={() => setAdminTab('users')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all border-none cursor-pointer ${
              adminTab === 'users'
                ? 'bg-red-600 text-white shadow-md'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 bg-transparent'
            }`}
          >
            <Users className="w-4 h-4" />
            System User Directory ({adminUsers.length})
          </button>
        </div>

        {/* TAB 1: DOCTOR VERIFICATION QUEUE */}
        {adminTab === 'verification' && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm space-y-4">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 bg-red-50/10 dark:bg-red-950/10 flex justify-between items-center">
              <div>
                <h3 className="text-sm font-black text-slate-950 dark:text-slate-100">
                  Doctor Credential Verification & Approval Queue
                </h3>
                <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
                  Doctors registered through the portal must be verified before clinical data access is enabled.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-50 dark:bg-amber-950/30 text-amber-600 border border-amber-500/20">
                {pendingDoctors.length} Awaiting Decision
              </span>
            </div>

            {pendingDoctors.length === 0 ? (
              <div className="p-10 text-center space-y-2">
                <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto opacity-70" />
                <h4 className="text-sm font-black text-slate-800 dark:text-slate-200">No Pending Doctor Registrations</h4>
                <p className="text-xs text-slate-400 font-semibold">
                  All registered doctors have been evaluated and approved/rejected.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-850">
                {pendingDoctors.map((doc) => (
                  <div key={doc.id} className="p-5 space-y-3 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <Stethoscope className="w-4 h-4 text-blue-600" />
                          <h4 className="text-sm font-black text-slate-900 dark:text-slate-100">{doc.fullName}</h4>
                          <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase ${
                            doc.verificationStatus === 'UNDER_REVIEW'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                          }`}>
                            {doc.verificationStatus}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 font-semibold mt-1">
                          {doc.email} • {doc.phone} • Specialization: <span className="font-bold text-slate-800 dark:text-slate-200">{doc.specialization}</span> ({doc.qualification})
                        </p>
                        <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
                          Registration No: <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{doc.medicalRegistrationNumber}</span> • Council: {doc.stateMedicalCouncil}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewDoctorDetails(doc.id)}
                          disabled={actionLoading === doc.id}
                          className="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold cursor-pointer border-none flex items-center gap-1.5 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Inspect Details
                        </button>
                        <button
                          onClick={() => handleApproveDoctor(doc.id)}
                          disabled={actionLoading === doc.id}
                          className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold cursor-pointer border-none flex items-center gap-1.5 shadow-sm transition-colors"
                        >
                          <Check className="w-3.5 h-3.5" />
                          Approve
                        </button>
                        <button
                          onClick={() => handleRejectDoctor(doc.id)}
                          disabled={actionLoading === doc.id}
                          className="px-3 py-2 bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-950/40 dark:text-red-300 rounded-xl text-xs font-bold cursor-pointer border-none flex items-center gap-1.5 transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                          Reject
                        </button>
                      </div>
                    </div>

                    {/* Verification checks summary badge row */}
                    {doc.checks && (
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-slate-100 dark:border-slate-850">
                        {Object.entries(doc.checks).map(([key, val]) => (
                          <div key={key} className="bg-slate-50 dark:bg-slate-950 p-2 rounded-lg text-center">
                            <span className="text-[9px] text-slate-400 uppercase font-black block tracking-wider truncate">
                              {key.replace(/([A-Z])/g, ' $1')}
                            </span>
                            <span className={`text-[10px] font-bold ${
                              val === 'VERIFIED' ? 'text-emerald-600' : 'text-amber-600'
                            }`}>
                              {val === 'VERIFIED' ? '✓ VERIFIED' : '⏳ PENDING'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: SYSTEM USER DIRECTORY */}
        {adminTab === 'users' && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm space-y-4">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-black text-slate-950 dark:text-slate-100">
                  Registered Portal Users ({adminUsers.length})
                </h3>
                <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
                  Complete registry of all Doctors, Patients, Caregivers, Family Members, and Administrators.
                </p>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter users..."
                  value={adminSearchQuery}
                  onChange={(e) => setAdminSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 border border-slate-200 dark:border-slate-800 rounded-xl text-xs bg-slate-50 dark:bg-slate-950 outline-none"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                    <th className="py-3 px-6 text-left">User Profile</th>
                    <th className="py-3 px-6 text-left">Role</th>
                    <th className="py-3 px-6 text-left">Phone & Email</th>
                    <th className="py-3 px-6 text-left">Identifier / Reg</th>
                    <th className="py-3 px-6 text-left">Status</th>
                    <th className="py-3 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-300">
                  {adminUsers
                    .filter(u => 
                      !adminSearchQuery || 
                      u.fullName.toLowerCase().includes(adminSearchQuery.toLowerCase()) ||
                      u.email.toLowerCase().includes(adminSearchQuery.toLowerCase()) ||
                      u.role.toLowerCase().includes(adminSearchQuery.toLowerCase())
                    )
                    .map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                        <td className="py-3.5 px-6 font-black text-slate-900 dark:text-slate-100">
                          {u.fullName}
                          {u.email === user?.email && <span className="ml-1.5 text-[9px] text-blue-600 font-bold">(You)</span>}
                        </td>
                        <td className="py-3.5 px-6">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                            u.role === 'doctor' ? 'bg-blue-50 text-blue-600 dark:bg-blue-950/40' :
                            u.role === 'patient' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40' :
                            u.role === 'caregiver' ? 'bg-purple-50 text-purple-600 dark:bg-purple-950/40' :
                            u.role === 'family' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/40' :
                            'bg-red-50 text-red-600 dark:bg-red-950/40'
                          }`}>
                            {u.role}
                          </span>
                        </td>
                        <td className="py-3.5 px-6">
                          <p className="text-slate-900 dark:text-slate-100">{u.email}</p>
                          <p className="text-[10px] text-slate-400">{u.phone || 'No phone'}</p>
                        </td>
                        <td className="py-3.5 px-6 font-mono text-[11px]">
                          {u.medicalRegistrationNumber || u.patientId || u.agencyId || u.linkedPatientId || '—'}
                        </td>
                        <td className="py-3.5 px-6">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            u.status === 'ACTIVE' || u.approved ? 'text-emerald-600' : 'text-amber-600'
                          }`}>
                            {u.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-6 text-right">
                          {u.email !== user?.email && (
                            <button
                              onClick={() => handleDeleteUser(u.id, u.email)}
                              className="px-2.5 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg text-xs font-bold border-none cursor-pointer transition-colors"
                              title="Revoke User Access"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* DOCTOR DETAILS INSPECTION MODAL */}
        {isDetailsModalOpen && selectedDoctorDetails && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-sm animate-fade-in">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-3xl p-6 max-w-2xl w-full shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto text-left">
              <div className="flex justify-between items-start border-b border-slate-100 dark:border-slate-800 pb-4">
                <div>
                  <h3 className="text-lg font-black text-slate-900 dark:text-white flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-blue-600" />
                    Doctor Credential Verification Audit
                  </h3>
                  <p className="text-xs text-slate-500 font-semibold mt-0.5">
                    {selectedDoctorDetails.fullName || selectedDoctorDetails.accountDetails?.fullName} • Reg No: <span className="font-mono font-bold text-slate-800 dark:text-slate-200">{selectedDoctorDetails.medicalRegistrationNumber || selectedDoctorDetails.professionalDetails?.medicalRegistrationNumber}</span>
                  </p>
                </div>
                <button
                  onClick={() => setIsDetailsModalOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded-lg border-none bg-transparent cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* 1. DOCTOR APPLICATION (Submitted Information) */}
              <div className="space-y-2">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                  Doctor Application (Submitted Information)
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-100 dark:border-slate-850 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Applicant Name</span>
                    <span className="font-black text-slate-900 dark:text-white">{selectedDoctorDetails.accountDetails?.fullName || selectedDoctorDetails.fullName}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Registration Number</span>
                    <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{selectedDoctorDetails.professionalDetails?.medicalRegistrationNumber || selectedDoctorDetails.medicalRegistrationNumber}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Medical Council</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{selectedDoctorDetails.professionalDetails?.stateMedicalCouncil || selectedDoctorDetails.stateMedicalCouncil}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Qualification</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{selectedDoctorDetails.professionalDetails?.qualification || selectedDoctorDetails.qualification || 'MBBS'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Specialization</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{selectedDoctorDetails.professionalDetails?.specialization || selectedDoctorDetails.specialization || 'General Medicine'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Experience</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{selectedDoctorDetails.professionalDetails?.yearsOfExperience ?? selectedDoctorDetails.experience ?? '0'} Years</span>
                  </div>
                </div>
              </div>

              {/* 2. AUTOMATIC VERIFICATION BREAKDOWN */}
              <div className="space-y-2">
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">
                  Automatic Reference Verification Breakdown
                </span>
                <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-100 dark:border-slate-850 space-y-2.5">
                  {(() => {
                    const checks = selectedDoctorDetails.datasetVerificationDetails?.checks || selectedDoctorDetails.checks || {};
                    const hasRef = !!selectedDoctorDetails.referenceDoctorRecord || !!selectedDoctorDetails.referenceRegistryMatch || checks.registration_check === 'VERIFIED';
                    const councilMatched = checks.council_check === 'VERIFIED' || checks.councilCheck === 'VERIFIED';
                    const nameMatched = checks.name_check === 'VERIFIED' || checks.name_check === 'LIKELY' || checks.nameCheck === 'VERIFIED';
                    const discClear = !selectedDoctorDetails.disciplinaryRecords?.length && checks.disciplinary_check !== 'BLOCKED' && checks.disciplinaryCheck !== 'BLOCKED';
                    const isFullyVerified = hasRef && councilMatched && nameMatched && discClear;

                    const breakdownItems = [
                      {
                        label: 'Registration Record',
                        value: hasRef ? (isFullyVerified ? 'MATCHED' : 'FOUND') : 'NOT FOUND',
                        isGood: hasRef
                      },
                      {
                        label: 'Registration Number',
                        value: hasRef ? 'MATCHED' : 'NOT FOUND',
                        isGood: hasRef
                      },
                      {
                        label: 'Medical Council',
                        value: councilMatched ? 'MATCHED' : 'REVIEW REQUIRED',
                        isGood: councilMatched
                      },
                      {
                        label: 'Professional Details',
                        value: nameMatched ? 'MATCHED' : 'REVIEW REQUIRED',
                        isGood: nameMatched
                      },
                      {
                        label: 'Disciplinary Check',
                        value: discClear ? 'CLEAR' : 'BLOCKED',
                        isGood: discClear
                      },
                      {
                        label: 'Automatic Verification',
                        value: isFullyVerified ? 'VERIFIED' : 'ADMIN REVIEW REQUIRED',
                        isGood: isFullyVerified
                      },
                      {
                        label: 'Final Administrator Approval',
                        value: selectedDoctorDetails.accountDetails?.approved ? 'APPROVED' : 'PENDING',
                        isGood: selectedDoctorDetails.accountDetails?.approved
                      }
                    ];

                    return (
                      <div className="space-y-2">
                        <div className="divide-y divide-slate-200/60 dark:divide-slate-800">
                          {breakdownItems.map((item, idx) => (
                            <div key={idx} className="py-1.5 flex justify-between items-center text-xs font-semibold">
                              <span className="text-slate-600 dark:text-slate-400">{item.label}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                                item.isGood
                                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50'
                                  : 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50'
                              }`}>
                                {item.isGood ? `✓ ${item.value}` : `⚠ ${item.value}`}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>

              {/* Reference Disciplinary Alert if any */}
              {selectedDoctorDetails.disciplinaryRecords && selectedDoctorDetails.disciplinaryRecords.length > 0 && (
                <div className="p-3.5 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 rounded-2xl text-xs font-semibold border border-red-200 dark:border-red-900/50 space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-red-600" />
                    <span>Active Disciplinary Record Warning</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    A reference restriction exists for this registration ID. Administrator discretion required.
                  </p>
                </div>
              )}

              {/* Modal Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  onClick={() => setIsDetailsModalOpen(false)}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold border-none cursor-pointer"
                >
                  Close
                </button>
                <button
                  onClick={() => handleRejectDoctor(selectedDoctorDetails.id || selectedDoctorDetails.accountDetails?.id)}
                  className="px-4 py-2.5 bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-950/40 dark:text-red-300 rounded-xl text-xs font-bold border-none cursor-pointer transition-colors"
                >
                  Reject Application
                </button>
                <button
                  onClick={() => handleApproveDoctor(selectedDoctorDetails.id || selectedDoctorDetails.accountDetails?.id)}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold border-none cursor-pointer shadow-md transition-colors flex items-center gap-1.5"
                >
                  <Check className="w-4 h-4" />
                  <span>Approve & Enable Clinical Access</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // STANDARD PATIENT / CAREGIVER / FAMILY VIEW
  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Healthcare Access Controls & Permissions
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Authorize consulting clinicians, certified caregivers, and family members to access your remote monitoring stream.
          </p>
        </div>
      </div>

      {/* Patient Access Code Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
        <span className="text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest block">Your Patient Access Code</span>
        <div className="flex items-center gap-3">
          <span className="font-mono font-black text-xl text-slate-900 dark:text-white tracking-widest">{selectedPatientId}</span>
          <button 
            onClick={() => {
              navigator.clipboard.writeText(selectedPatientId);
              addToast("Access code copied to clipboard!", "success");
            }}
            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-bold border-none cursor-pointer"
          >
            Copy Code
          </button>
        </div>
        <p className="text-xs text-slate-450 dark:text-slate-500">
          Share this access identifier with your clinician or care team so they can send a link request.
        </p>
      </div>

      {/* Linked Doctors & Pending Requests */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl overflow-hidden shadow-sm space-y-4">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 bg-blue-50/10 dark:bg-blue-950/5 flex justify-between items-center">
          <h3 className="text-sm font-black text-slate-950 dark:text-slate-100">Attending Clinicians & Doctors</h3>
          {(accessControls.pendingDoctors || []).length > 0 && (
            <span className="px-2.5 py-0.5 rounded-full text-[9px] bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-black uppercase tracking-wider">
              {(accessControls.pendingDoctors || []).length} Request Pending Approval
            </span>
          )}
        </div>

        {/* Pending Requests */}
        {(accessControls.pendingDoctors || []).length > 0 && (
          <div className="p-4 bg-amber-50/10 dark:bg-amber-950/5 border-b border-slate-100 dark:border-slate-850 space-y-2">
            <span className="text-[10px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest block">Pending Requests Sent To Clinicians</span>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {(accessControls.pendingDoctors || []).map(pDoc => (
                <div key={pDoc.id} className="py-2.5 flex justify-between items-center text-xs">
                  <div>
                    <p className="font-black text-slate-900 dark:text-slate-100">{pDoc.doctorName}</p>
                    <p className="text-[10px] text-slate-400">{pDoc.doctorHospital || 'Facility'} • Status: <span className="font-extrabold text-amber-600 uppercase">{pDoc.status}</span></p>
                  </div>
                  <button
                    onClick={() => handleCancelConnectionRequest(pDoc.id)}
                    className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-red-50 hover:text-red-500 text-slate-600 dark:text-slate-300 rounded-lg text-[10px] font-bold uppercase cursor-pointer border-none"
                  >
                    Cancel Request
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Linked Doctors Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 text-slate-400 text-[10px] font-black uppercase border-b border-slate-100 dark:border-slate-850">
                <th className="py-3 px-6 text-left">Clinician Name</th>
                <th className="py-3 px-6 text-left">Specialization</th>
                <th className="py-3 px-6 text-left">Email</th>
                <th className="py-3 px-6 text-left">Link Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-semibold text-slate-700 dark:text-slate-300">
              {accessControls.doctors.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-6 text-center text-slate-400 font-semibold">No consulting doctors linked yet. Search below to request connection.</td>
                </tr>
              ) : (
                accessControls.doctors.map(d => (
                  <tr key={d.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-950/50">
                    <td className="py-3.5 px-6 font-black text-slate-900 dark:text-slate-100">{d.doctorName}</td>
                    <td className="py-3.5 px-6 font-bold text-blue-600">{d.specialization}</td>
                    <td className="py-3.5 px-6 font-mono text-slate-500">{d.doctorEmail}</td>
                    <td className="py-3.5 px-6 text-slate-400">{d.createdAt ? new Date(d.createdAt).toLocaleDateString() : 'Active'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Search Doctor Directory */}
        <div className="p-5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-950/40 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Search & Request Consulting Clinician</span>
            <span className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase">{doctorsList.length} Clinicians Registered</span>
          </div>
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search clinician by name, medical registration number, specialization, or hospital..."
              value={doctorSearchQuery}
              onChange={(e) => setDoctorSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 text-xs font-semibold text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 shadow-sm"
            />
          </div>

          {doctorSearchQuery.trim() !== '' && (
            <div className="border border-slate-200/60 dark:border-slate-800 rounded-xl divide-y divide-slate-100 dark:divide-slate-850 overflow-hidden bg-white dark:bg-slate-900 max-h-56 overflow-y-auto shadow-sm">
              {doctorsList.filter(doc =>
                doc.name.toLowerCase().includes(doctorSearchQuery.toLowerCase()) ||
                (doc.specialization && doc.specialization.toLowerCase().includes(doctorSearchQuery.toLowerCase())) ||
                (doc.hospital && doc.hospital.toLowerCase().includes(doctorSearchQuery.toLowerCase())) ||
                (doc.npi && doc.npi.toLowerCase().includes(doctorSearchQuery.toLowerCase()))
              ).map(doc => {
                const docReq = connectionRequests.find(r => r.doctorNpi === doc.npi);
                const isAlreadyConnected = accessControls.doctors.some(d => d.doctorNpi === doc.npi);
                const isAlreadyPending = (docReq?.status === 'Pending');

                return (
                  <div key={doc.npi || doc.id} className="p-3.5 flex justify-between items-center text-xs hover:bg-slate-50 dark:hover:bg-slate-950">
                    <div className="flex-1 pr-4">
                      <p className="font-black text-slate-900 dark:text-slate-100 text-sm">{doc.name}</p>
                      <p className="text-[10px] text-blue-600 dark:text-blue-400 font-extrabold uppercase tracking-wider mt-0.5">
                        {doc.specialization || 'Consulting Physician'} • {doc.experience || '0'} Yrs Exp.
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{doc.hospital} • Reg No: <span className="font-mono">{doc.npi}</span></p>
                    </div>
                    {isAlreadyConnected ? (
                      <span className="px-3 py-1.5 bg-emerald-50 text-emerald-600 border border-emerald-500/20 rounded-xl font-bold text-[10px] uppercase">
                        ✓ Connected
                      </span>
                    ) : isAlreadyPending ? (
                      <span className="px-3 py-1.5 bg-amber-50 text-amber-600 border border-amber-500/20 rounded-xl font-bold text-[10px] uppercase">
                        ⏳ Request Sent
                      </span>
                    ) : (
                      <button
                        onClick={() => {
                          handleSendConnectionRequest(doc.npi);
                          setDoctorSearchQuery('');
                        }}
                        className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-[10px] uppercase tracking-wider cursor-pointer border-none shadow-xs transition-colors"
                      >
                        Request Connection
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Caregiver & Family Access Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Caregivers */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Caregiver Authorizations</span>
          <form onSubmit={handleConnectCaregiver} className="flex gap-2">
            <input
              type="text"
              placeholder="Caregiver email or Agency ID..."
              value={caregiverLinkInput}
              onChange={e => setCaregiverLinkInput(e.target.value)}
              className="flex-1 p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 text-xs font-semibold"
            />
            <button type="submit" className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
              Link Caregiver
            </button>
          </form>
          <div className="divide-y divide-slate-100 dark:divide-slate-850">
            {accessControls.caregivers.length === 0 ? (
              <p className="text-xs text-slate-400 p-3 text-center">No caregivers currently authorized.</p>
            ) : (
              accessControls.caregivers.map(cg => (
                <div key={cg.id} className="py-2.5 flex justify-between items-center text-xs">
                  <div>
                    <p className="font-bold text-slate-900 dark:text-slate-100">{cg.name || cg.email}</p>
                    <span className="text-[10px] text-slate-400">Agency: {cg.agencyId || 'Independent'}</span>
                  </div>
                  <button onClick={() => handleRevokeCaregiver(cg.id)} className="px-2 py-1 bg-red-50 text-red-600 font-bold text-[10px] rounded border-none cursor-pointer">
                    Revoke
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Family Members */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">Family Member Authorizations</span>
          <form onSubmit={handleConnectFamily} className="flex gap-2">
            <input
              type="text"
              placeholder="Family member email..."
              value={familyLinkInput}
              onChange={e => setFamilyLinkInput(e.target.value)}
              className="flex-1 p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 text-xs font-semibold"
            />
            <button type="submit" className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer">
              Grant Access
            </button>
          </form>
          <div className="divide-y divide-slate-100 dark:divide-slate-850">
            {accessControls.familyMembers.length === 0 ? (
              <p className="text-xs text-slate-400 p-3 text-center">No family members linked.</p>
            ) : (
              accessControls.familyMembers.map(fm => (
                <div key={fm.id} className="py-2.5 flex justify-between items-center text-xs">
                  <div>
                    <p className="font-bold text-slate-900 dark:text-slate-100">{fm.name || fm.email}</p>
                    <span className="text-[10px] text-slate-400">Relationship: {fm.relationship || 'Relative'}</span>
                  </div>
                  <button onClick={() => handleRevokeFamily(fm.id)} className="px-2 py-1 bg-red-50 text-red-600 font-bold text-[10px] rounded border-none cursor-pointer">
                    Revoke
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessControlsPage;

