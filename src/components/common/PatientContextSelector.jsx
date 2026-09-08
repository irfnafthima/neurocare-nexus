import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getApiUrl } from '../../services/api';
import { 
  Users, 
  ChevronDown, 
  Check, 
  User, 
  Activity, 
  ShieldCheck, 
  Search 
} from 'lucide-react';

export const PatientContextSelector = ({
  activePatientId,
  onSelectPatient,
  className = ''
}) => {
  const { user, authFetch } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const isClinician = userRole === 'doctor' || userRole === 'caregiver';

  const [isOpen, setIsOpen] = useState(false);
  const [patients, setPatients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch authorized patients for clinician
  useEffect(() => {
    if (!isClinician) return;

    let isMounted = true;
    const fetchAuthorizedPatients = async () => {
      try {
        setIsLoading(true);
        const res = await authFetch(getApiUrl('/patients/'));
        if (res.ok) {
          const data = await res.json();
          if (isMounted) {
            setPatients(Array.isArray(data) ? data : []);
          }
        }
      } catch (err) {
        console.error('Error fetching authorized patient roster for selector:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchAuthorizedPatients();
    return () => { isMounted = false; };
  }, [userRole]);

  // Find active patient object
  const activePatient = patients.find(p => p.id === activePatientId) || null;

  const handleSelect = (patientId) => {
    sessionStorage.setItem('nexus_selected_patient_id', patientId);
    setIsOpen(false);
    setSearchTerm('');

    if (onSelectPatient) {
      onSelectPatient(patientId);
    } else {
      // Update URL with new patientId on current route
      navigate(`${location.pathname}?patientId=${patientId}`, { replace: false });
    }
  };

  // Only render selector for Clinicians (Doctor / Caregiver) who manage multiple patients
  if (!isClinician) {
    return null;
  }

  const filteredPatients = patients.filter(p => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (p.name || '').toLowerCase().includes(q) || (p.id || '').toLowerCase().includes(q);
  });

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-bold transition-all shadow-xs cursor-pointer select-none"
        title="Switch active patient context"
      >
        <Users className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
        <span className="text-[11px] font-mono text-slate-400 font-semibold uppercase tracking-wider">
          Active Patient:
        </span>
        <span className="font-black text-slate-900 dark:text-slate-50 truncate max-w-[160px]">
          {activePatient ? `${activePatient.name} (${activePatient.id})` : (activePatientId ? `Patient ${activePatientId}` : 'Select Patient')}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-1.5 w-72 max-h-80 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl z-50 overflow-hidden flex flex-col animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="p-2.5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
            <div className="flex items-center justify-between pb-1.5 px-1">
              <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider">
                Authorized Assigned Patients ({patients.length})
              </span>
            </div>
            {patients.length > 4 && (
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter by name or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-750 rounded-lg text-xs font-semibold text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>
            )}
          </div>

          <div className="overflow-y-auto max-h-60 p-1.5 divide-y divide-slate-100/50 dark:divide-slate-800/50">
            {isLoading ? (
              <div className="py-6 text-center text-xs text-slate-400 font-semibold">
                Loading linked patients...
              </div>
            ) : filteredPatients.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400 font-semibold">
                No matching assigned patients found.
              </div>
            ) : (
              filteredPatients.map((p) => {
                const isSelected = p.id === activePatientId;
                return (
                  <button
                    key={p.id}
                    onClick={() => handleSelect(p.id)}
                    className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition-colors border-none cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-200 bg-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                        isSelected
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                      }`}>
                        {p.name ? p.name.charAt(0).toUpperCase() : 'P'}
                      </div>
                      <div className="truncate">
                        <span className="font-black text-xs block truncate leading-tight">
                          {p.name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 font-bold block">
                          ID: {p.id} {p.age ? `• ${p.age}y` : ''} {p.gender ? `• ${p.gender}` : ''}
                        </span>
                      </div>
                    </div>

                    {isSelected && (
                      <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 ml-2" />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientContextSelector;
