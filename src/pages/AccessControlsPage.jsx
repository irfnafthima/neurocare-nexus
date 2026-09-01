import React, { useState, useEffect } from 'react';
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
  AlertTriangle 
} from 'lucide-react';

export const AccessControlsPage = () => {
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

  const fetchAccessControls = async () => {
    try {
      setIsLoading(true);
      // Fetch access controls
      const res = await authFetch(getApiUrl(`/access-controls?patientId=${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        setAccessControls(data);
      }

      // Fetch doctors directory for searching
      const docRes = await authFetch(getApiUrl('/doctors/directory'));
      if (docRes.ok) {
        const docData = await docRes.json();
        setDoctorsList(docData.doctors || []);
      }

      // Fetch connection requests
      const reqRes = await authFetch(getApiUrl('/doctor-requests/'));
      if (reqRes.ok) {
        const reqData = await reqRes.json();
        setConnectionRequests(reqData.requests || []);
      }
    } catch (e) {
      console.error('Error fetching access controls:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccessControls();
  }, [selectedPatientId]);

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
