import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  ScrollText, 
  Pill, 
  Plus, 
  Calendar, 
  Clock, 
  UserCheck, 
  ShieldCheck, 
  AlertCircle,
  FileText
} from 'lucide-react';

export const PrescriptionsPage = () => {
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
  const [prescriptions, setPrescriptions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Clinician Prescribe Modal States
  const [isPrescriptionModalOpen, setIsPrescriptionModalOpen] = useState(false);
  const [rxMedicines, setRxMedicines] = useState('');
  const [rxDosage, setRxDosage] = useState('');
  const [rxFrequency, setRxFrequency] = useState('Once daily');
  const [rxDuration, setRxDuration] = useState('7 days');
  const [rxInstructions, setRxInstructions] = useState('');
  const [rxDate, setRxDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchPrescriptions = async () => {
    try {
      setIsLoading(true);
      const res = await authFetch(getApiUrl(`/prescriptions/?patientId=${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        setPrescriptions(data.prescriptions || []);
      }
    } catch (e) {
      console.error('Error fetching prescriptions:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, [selectedPatientId]);

  const handleCreatePrescription = async (e) => {
    e.preventDefault();
    if (!rxMedicines.trim() || !rxDosage.trim()) {
      addToast('Medication name and dosage are required.', 'error');
      return;
    }
    try {
      const res = await authFetch(getApiUrl('/prescriptions/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientId: selectedPatientId,
          medicines: rxMedicines.trim(),
          dosage: rxDosage.trim(),
          frequency: rxFrequency,
          duration: rxDuration,
          instructions: rxInstructions.trim(),
          prescription_date: rxDate
        })
      });

      if (res.ok) {
        addToast('Official prescription issued by attending clinician.', 'success');
        setIsPrescriptionModalOpen(false);
        setRxMedicines('');
        setRxDosage('');
        setRxInstructions('');
        fetchPrescriptions();
      } else {
        const err = await res.text();
        addToast(`Prescription issuance failed: ${err}`, 'error');
      }
    } catch (e) {
      addToast('Error issuing prescription.', 'error');
    }
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <ScrollText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Official Medical Prescriptions
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Clinician-authorized prescriptions, dosage schedules, duration guidelines, and patient instructions.
          </p>
        </div>
        {userRole === 'doctor' && (
          <button
            onClick={() => setIsPrescriptionModalOpen(true)}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors border-none cursor-pointer flex items-center gap-1.5 self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Issue New Prescription</span>
          </button>
        )}
      </div>

      {/* Security notice */}
      <div className="p-3.5 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30 rounded-xl flex items-center gap-3 text-xs">
        <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
        <span className="text-slate-600 dark:text-slate-350 font-semibold leading-relaxed">
          Official prescriptions are issued and modified exclusively by registered attending clinicians. AI Assistant provides medication safety context only.
        </span>
      </div>

      {/* Prescriptions List */}
      <div className="space-y-4">
        {prescriptions.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-8 text-center text-slate-400 text-xs font-semibold">
            No active prescriptions on file for this patient record.
          </div>
        ) : (
          prescriptions.map(rx => (
            <div key={rx.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-850 pb-3">
                <div className="flex items-center gap-2">
                  <Pill className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-black text-slate-900 dark:text-slate-100">{rx.medicines}</span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {rx.status || 'Active'}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-semibold text-slate-400">
                  <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {rx.prescription_date ? new Date(rx.prescription_date).toLocaleDateString() : 'Active'}</span>
                  <span>• Prescribed by: <strong className="text-slate-700 dark:text-slate-300 font-bold">{rx.doctor_name || 'Attending Physician'}</strong></span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Dosage</span>
                  <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{rx.dosage}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Frequency</span>
                  <p className="font-bold text-blue-600 dark:text-blue-400 mt-0.5">{rx.frequency}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Duration</span>
                  <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{rx.duration || 'Ongoing'}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Refills</span>
                  <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{rx.refills_remaining ?? '0'} Remaining</p>
                </div>
              </div>

              {rx.instructions && (
                <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-850 text-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Doctor's Clinical Instructions</span>
                  <p className="text-slate-650 dark:text-slate-350 font-semibold mt-0.5">{rx.instructions}</p>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Clinician Issue Prescription Modal */}
      {isPrescriptionModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Issue Official Prescription</h3>
              <button onClick={() => setIsPrescriptionModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>
            <form onSubmit={handleCreatePrescription} className="space-y-3 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Medication Name *</label>
                <input type="text" placeholder="e.g. Metformin, Lisinopril, Atorvastatin" value={rxMedicines} onChange={e => setRxMedicines(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Dosage *</label>
                  <input type="text" placeholder="e.g. 500mg, 10mg" value={rxDosage} onChange={e => setRxDosage(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Frequency</label>
                  <select value={rxFrequency} onChange={e => setRxFrequency(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold">
                    <option value="Once daily">Once daily</option>
                    <option value="Twice daily">Twice daily</option>
                    <option value="Three times daily">Three times daily</option>
                    <option value="Every 8 hours">Every 8 hours</option>
                    <option value="As needed (PRN)">As needed (PRN)</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Duration</label>
                  <input type="text" placeholder="e.g. 7 days, 30 days, Ongoing" value={rxDuration} onChange={e => setRxDuration(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Prescription Date</label>
                  <input type="date" value={rxDate} onChange={e => setRxDate(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Clinical Administration Instructions</label>
                <textarea placeholder="Take with food after morning meal..." value={rxInstructions} onChange={e => setRxInstructions(e.target.value)} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 h-16" />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t">
                <button type="button" onClick={() => setIsPrescriptionModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">Authorize & Issue</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrescriptionsPage;
