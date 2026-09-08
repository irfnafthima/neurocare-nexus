import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  FileText,
  Heart
} from 'lucide-react';

/**
 * PatientsPage — Dedicated Clinician / Caregiver Patient Directory.
 * Displays only authorized patients linked via DoctorPatientLink or CaregiverPatientLink.
 */
export const PatientsPage = () => {
  const { user, authFetch } = useAuth();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [patients, setPatients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchPatients = async () => {
    try {
      setIsLoading(true);
      const res = await authFetch(getApiUrl('/patients/'));
      if (res.ok) {
        const data = await res.json();
        setPatients(Array.isArray(data) ? data : []);
      } else {
        addToast('Failed to load authorized patients list.', 'error');
      }
    } catch (err) {
      console.error('Error fetching patients:', err);
      addToast('Network error while fetching patients.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const handleReviewPatient = (patientId) => {
    if (!patientId) return;
    sessionStorage.setItem('nexus_selected_patient_id', patientId);
    navigate(`/health-records?patientId=${patientId}`);
  };

  const filteredPatients = patients.filter((p) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    const nameMatch = (p.name || '').toLowerCase().includes(q);
    const idMatch = (p.id || '').toLowerCase().includes(q);
    const condMatch = (p.condition || '').toLowerCase().includes(q);
    return nameMatch || idMatch || condMatch;
  });

  return (
    <div className="space-y-6 text-left">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 p-6 rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h1 className="text-xl font-black text-slate-950 dark:text-slate-100 tracking-tight">
              Assigned Patients Directory
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-1">
            Access authorized patient records, live telemetry streams, and clinical documentation.
          </p>
        </div>

        {/* Search Bar */}
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
      </div>

      {/* Patient Cards Grid */}
      {isLoading ? (
        <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Loading authorized patient roster...
        </div>
      ) : filteredPatients.length === 0 ? (
        <div className="py-16 text-center text-xs font-semibold text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl space-y-2">
          <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="font-bold text-slate-600 dark:text-slate-300">No matching authorized patients found.</p>
          <p className="text-[11px]">Only patients with an approved clinical connection are visible in your directory.</p>
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
    </div>
  );
};

export default PatientsPage;
