import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  FileText, 
  User, 
  AlertTriangle, 
  ShieldAlert, 
  Plus, 
  Download, 
  Upload, 
  CheckCircle2, 
  Calendar,
  Clock,
  Trash2,
  Edit
} from 'lucide-react';

export const HealthRecordsPage = () => {
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
  const [patientData, setPatientData] = useState(null);
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [nextConsultations, setNextConsultations] = useState([]);
  const [aiPatientNote, setAiPatientNote] = useState(null);
  const [isLoadingAiNote, setIsLoadingAiNote] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Document Upload States
  const [docTitle, setDocTitle] = useState('');
  const [docCategory, setDocCategory] = useState('Lab Report');
  const [docDescription, setDocDescription] = useState('');
  const [docFile, setDocFile] = useState(null);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);

  // Profile Modal State
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [profileForm, setProfileForm] = useState({
    name: '', dob: '', age: '', gender: 'Other', phone: '', address: '',
    emergencyContactName: '', emergencyContactPhone: '', bloodGroup: ''
  });

  // Condition Modal State
  const [isConditionModalOpen, setIsConditionModalOpen] = useState(false);
  const [editingConditionId, setEditingConditionId] = useState(null);
  const [conditionForm, setConditionForm] = useState({
    conditionName: '', description: '', diagnosisDate: '', status: 'Active', notes: ''
  });

  // Allergy Modal State
  const [isAllergyModalOpen, setIsAllergyModalOpen] = useState(false);
  const [editingAllergyId, setEditingAllergyId] = useState(null);
  const [allergyForm, setAllergyForm] = useState({
    allergen: '', reaction: '', severity: 'Moderate', notes: ''
  });

  const fetchAiNote = async () => {
    try {
      setIsLoadingAiNote(true);
      const res = await authFetch(getApiUrl(`/ai/patient-summary/${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        setAiPatientNote(data);
      }
    } catch (err) {
      console.error('Error fetching AI patient note:', err);
    } finally {
      setIsLoadingAiNote(false);
    }
  };

  const fetchRecords = async () => {
    try {
      setIsLoading(true);
      const res = await authFetch(getApiUrl(`/health-records?patientId=${selectedPatientId || ''}`));
      if (res.ok) {
        const data = await res.json();
        setPatientData(data.patient || null);
        setConditions(data.conditions || []);
        setAllergies(data.allergies || []);
        setDocuments(data.documents || []);
        setConsultations(data.consultations || []);
        setNextConsultations(data.nextConsultations || []);
        if (data.patient) {
          setProfileForm({
            name: data.patient.name || '',
            dob: data.patient.dob || '',
            age: data.patient.age || '',
            gender: data.patient.gender || 'Other',
            phone: data.patient.phone || '',
            address: data.patient.address || '',
            emergencyContactName: data.patient.emergency_contact_name || '',
            emergencyContactPhone: data.patient.emergency_contact_phone || '',
            bloodGroup: data.patient.blood_group || ''
          });
        }
      }
      fetchAiNote();
    } catch (e) {
      console.error('Error fetching health records:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [selectedPatientId]);

  const handleSaveProfile = async () => {
    try {
      const res = await authFetch(getApiUrl(`/patients/${selectedPatientId}/`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileForm)
      });
      if (res.ok) {
        addToast('Patient Health Profile updated successfully.', 'success');
        setIsProfileModalOpen(false);
        fetchRecords();
      } else {
        addToast('Failed to update patient profile.', 'error');
      }
    } catch (e) {
      addToast('Error saving profile changes.', 'error');
    }
  };

  const handleSaveCondition = async () => {
    if (!conditionForm.conditionName.trim()) {
      addToast('Condition name is required.', 'error');
      return;
    }
    try {
      const payload = {
        patientId: selectedPatientId,
        conditionName: conditionForm.conditionName,
        description: conditionForm.description,
        diagnosisDate: conditionForm.diagnosisDate,
        status: conditionForm.status,
        notes: conditionForm.notes
      };
      const url = editingConditionId
        ? getApiUrl(`/health-records/condition/${editingConditionId}`)
        : getApiUrl('/health-records');
      const method = editingConditionId ? 'PUT' : 'POST';

      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingConditionId ? payload : { type: 'condition', ...payload })
      });

      if (res.ok) {
        addToast(editingConditionId ? 'Condition updated.' : 'Condition recorded.', 'success');
        setIsConditionModalOpen(false);
        setEditingConditionId(null);
        setConditionForm({ conditionName: '', description: '', diagnosisDate: '', status: 'Active', notes: '' });
        fetchRecords();
      } else {
        addToast('Failed to save condition.', 'error');
      }
    } catch (e) {
      addToast('Error saving condition record.', 'error');
    }
  };

  const handleDeleteCondition = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/health-records/condition/${id}`), { method: 'DELETE' });
      if (res.ok) {
        addToast('Condition record deleted.', 'info');
        setConditions(prev => prev.filter(c => c.id !== id));
      }
    } catch (e) {
      addToast('Error deleting condition.', 'error');
    }
  };

  const handleSaveAllergy = async () => {
    if (!allergyForm.allergen.trim()) {
      addToast('Allergen name is required.', 'error');
      return;
    }
    try {
      const payload = {
        patientId: selectedPatientId,
        allergen: allergyForm.allergen,
        reaction: allergyForm.reaction,
        severity: allergyForm.severity,
        notes: allergyForm.notes
      };
      const url = editingAllergyId
        ? getApiUrl(`/health-records/allergy/${editingAllergyId}`)
        : getApiUrl('/health-records');
      const method = editingAllergyId ? 'PUT' : 'POST';

      const res = await authFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingAllergyId ? payload : { type: 'allergy', ...payload })
      });

      if (res.ok) {
        addToast(editingAllergyId ? 'Allergy updated.' : 'Allergy recorded.', 'success');
        setIsAllergyModalOpen(false);
        setEditingAllergyId(null);
        setAllergyForm({ allergen: '', reaction: '', severity: 'Moderate', notes: '' });
        fetchRecords();
      } else {
        addToast('Failed to save allergy.', 'error');
      }
    } catch (e) {
      addToast('Error saving allergy record.', 'error');
    }
  };

  const handleDeleteAllergy = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/health-records/allergy/${id}`), { method: 'DELETE' });
      if (res.ok) {
        addToast('Allergy record deleted.', 'info');
        setAllergies(prev => prev.filter(a => a.id !== id));
      }
    } catch (e) {
      addToast('Error deleting allergy.', 'error');
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!docTitle.trim() || !docFile) {
      addToast('Please provide a document title and select a file.', 'error');
      return;
    }
    try {
      setIsUploadingDoc(true);
      const formData = new FormData();
      formData.append('patientId', selectedPatientId);
      formData.append('title', docTitle.trim());
      formData.append('document_type', docCategory);
      formData.append('description', docDescription.trim());
      formData.append('file', docFile);

      const res = await authFetch(getApiUrl('/medical-documents/'), {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        addToast('Medical document uploaded to vault.', 'success');
        setDocTitle('');
        setDocDescription('');
        setDocFile(null);
        fetchRecords();
      } else {
        const err = await res.text();
        addToast(`Upload failed: ${err}`, 'error');
      }
    } catch (err) {
      addToast('Error uploading document.', 'error');
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const handleDeleteDocument = async (id) => {
    try {
      const res = await authFetch(getApiUrl(`/medical-documents/${id}/`), { method: 'DELETE' });
      if (res.ok) {
        addToast('Document removed from vault.', 'info');
        setDocuments(prev => prev.filter(d => d.id !== id));
      }
    } catch (e) {
      addToast('Error deleting document.', 'error');
    }
  };

  return (
    <div className="space-y-6 text-left max-w-5xl mx-auto font-sans select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Health Records & Medical Documents
          </h1>
          <p className="text-xs font-semibold text-slate-500 mt-1">
            Clinical history, diagnosed health conditions, recorded allergies, and secured medical reports.
          </p>
        </div>
      </div>

      {/* 1. Patient Health Profile Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4 text-left">
        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">Patient Clinical Profile</span>
          </div>
          <button
            onClick={() => setIsProfileModalOpen(true)}
            className="px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white font-black text-[10px] uppercase rounded-xl transition-colors border-none cursor-pointer"
          >
            Edit Profile
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-semibold">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Full Name</span>
            <p className="text-sm font-black text-slate-900 dark:text-slate-100 mt-0.5">{patientData?.name || user?.full_name || 'Patient User'}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Patient ID</span>
            <p className="font-mono font-bold text-blue-600 dark:text-blue-400 mt-0.5">{selectedPatientId}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Age / Gender</span>
            <p className="font-bold text-slate-800 dark:text-slate-200 mt-0.5">{patientData?.age ? `${patientData.age} Yrs` : '--'} • {patientData?.gender || 'Other'}</p>
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Blood Group</span>
            <p className="font-bold text-rose-600 dark:text-rose-400 mt-0.5">{patientData?.blood_group || 'Not Specified'}</p>
          </div>
        </div>
      </div>

      {/* AI Patient Note / Clinical Summary */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3 text-left">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 dark:border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-purple-50 dark:bg-purple-950/40 flex items-center justify-center text-purple-600 dark:text-purple-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">
                  AI Patient Note & Clinical Summary
                </span>
                <span className="text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50">
                  Clinician Verification Required
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-semibold">
                Synthesized from PostgreSQL clinical records, vital telemetry, active alerts, and uploaded document vault.
              </p>
            </div>
          </div>
          <button
            onClick={fetchAiNote}
            disabled={isLoadingAiNote}
            className="px-3 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-[10px] font-bold rounded-lg transition-colors border-none cursor-pointer self-start sm:self-auto"
          >
            {isLoadingAiNote ? 'Generating Note...' : '⟳ Refresh AI Note'}
          </button>
        </div>

        {isLoadingAiNote ? (
          <div className="py-6 text-center text-xs font-semibold text-slate-400">
            Synthesizing clinical evidence and vital trends...
          </div>
        ) : aiPatientNote && aiPatientNote.note ? (
          <div className="space-y-3">
            <div className="bg-slate-50/70 dark:bg-slate-950/40 border border-slate-200/70 dark:border-slate-800 rounded-xl p-4 text-xs font-medium leading-relaxed text-slate-800 dark:text-slate-200 whitespace-pre-line font-mono">
              {aiPatientNote.note}
            </div>

            {aiPatientNote.sources && aiPatientNote.sources.length > 0 && (
              <div className="pt-2 flex flex-wrap items-center gap-1.5 text-[10px]">
                <span className="font-bold text-slate-400 uppercase tracking-wider mr-1">Evidence Sources:</span>
                {aiPatientNote.sources.map((src, sIdx) => (
                  <span
                    key={sIdx}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900/50 font-semibold text-[10px]"
                  >
                    🗄️ {src.source_name || src.title}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="py-4 text-xs font-semibold text-slate-500">
            AI Patient Note unavailable or patient has no active records on file.
          </div>
        )}
      </div>

      {/* 2. Health Conditions & Allergies 2-Column Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Conditions Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">Health Conditions</span>
            </div>
            <button
              onClick={() => {
                setEditingConditionId(null);
                setConditionForm({ conditionName: '', description: '', diagnosisDate: '', status: 'Active', notes: '' });
                setIsConditionModalOpen(true);
              }}
              className="px-2.5 py-1 bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 hover:bg-amber-600 hover:text-white font-black text-[10px] uppercase rounded-xl transition-colors border-none cursor-pointer"
            >
              + Add Condition
            </button>
          </div>

          {conditions.length === 0 ? (
            <div className="p-5 text-center text-xs font-semibold text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl">
              No active medical conditions recorded.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-850 max-h-64 overflow-y-auto">
              {conditions.map(c => (
                <div key={c.id} className="py-2.5 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-black text-slate-900 dark:text-slate-100">{c.condition_name}</span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-black uppercase bg-amber-50 text-amber-700 border border-amber-200">
                        {c.status}
                      </span>
                    </div>
                    {c.description && <p className="text-[11px] text-slate-500 mt-0.5">{c.description}</p>}
                    {c.diagnosis_date && <span className="text-[9px] text-slate-400 block mt-0.5">Diagnosed: {c.diagnosis_date}</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setEditingConditionId(c.id);
                        setConditionForm({
                          conditionName: c.condition_name,
                          description: c.description || '',
                          diagnosisDate: c.diagnosis_date || '',
                          status: c.status || 'Active',
                          notes: c.notes || ''
                        });
                        setIsConditionModalOpen(true);
                      }}
                      className="p-1 text-slate-400 hover:text-blue-600 bg-transparent border-none cursor-pointer"
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteCondition(c.id)}
                      className="p-1 text-slate-400 hover:text-red-600 bg-transparent border-none cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Allergies Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-500" />
              <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">Allergies & Sensitivities</span>
            </div>
            <button
              onClick={() => {
                setEditingAllergyId(null);
                setAllergyForm({ allergen: '', reaction: '', severity: 'Moderate', notes: '' });
                setIsAllergyModalOpen(true);
              }}
              className="px-2.5 py-1 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 hover:bg-red-600 hover:text-white font-black text-[10px] uppercase rounded-xl transition-colors border-none cursor-pointer"
            >
              + Add Allergy
            </button>
          </div>

          {allergies.length === 0 ? (
            <div className="p-5 text-center text-xs font-semibold text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl">
              No known drug or clinical allergies recorded.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-850 max-h-64 overflow-y-auto">
              {allergies.map(a => (
                <div key={a.id} className="py-2.5 flex items-start justify-between gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-black text-slate-900 dark:text-slate-100">{a.allergen}</span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-black uppercase bg-red-50 text-red-700 border border-red-200">
                        {a.severity}
                      </span>
                    </div>
                    {a.reaction && <p className="text-[11px] text-slate-500 mt-0.5">Reaction: {a.reaction}</p>}
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setEditingAllergyId(a.id);
                        setAllergyForm({
                          allergen: a.allergen,
                          reaction: a.reaction || '',
                          severity: a.severity || 'Moderate',
                          notes: a.notes || ''
                        });
                        setIsAllergyModalOpen(true);
                      }}
                      className="p-1 text-slate-400 hover:text-blue-600 bg-transparent border-none cursor-pointer"
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteAllergy(a.id)}
                      className="p-1 text-slate-400 hover:text-red-600 bg-transparent border-none cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3. Medical Document Vault */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-850 pb-2.5">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-black text-slate-950 dark:text-slate-100 uppercase tracking-wider">Medical Document Vault (RAG Ready)</span>
          </div>
          <span className="text-[10px] font-bold text-slate-400">{documents.length} Files Protected</span>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUploadDocument} className="p-4 bg-slate-50 dark:bg-slate-950 border border-slate-200/60 dark:border-slate-800 rounded-xl space-y-3">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">Upload Clinical Lab Report / Medical Document</span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <input
                type="text"
                placeholder="Document Title (e.g., Blood Panel Report)..."
                value={docTitle}
                onChange={e => setDocTitle(e.target.value)}
                className="w-full p-2.5 border rounded-xl bg-white dark:bg-slate-900 font-semibold text-xs text-slate-800 dark:text-slate-200 outline-none"
              />
            </div>
            <div>
              <select
                value={docCategory}
                onChange={e => setDocCategory(e.target.value)}
                className="w-full p-2.5 border rounded-xl bg-white dark:bg-slate-900 font-semibold text-xs text-slate-800 dark:text-slate-200 outline-none"
              >
                <option value="Lab Report">Lab Report</option>
                <option value="Scan / Imaging">Scan / Imaging</option>
                <option value="Prescription PDF">Prescription PDF</option>
                <option value="Discharge Summary">Discharge Summary</option>
                <option value="General Report">General Report</option>
              </select>
            </div>
            <div>
              <input
                type="file"
                onChange={e => setDocFile(e.target.files[0])}
                className="w-full p-1.5 border rounded-xl bg-white dark:bg-slate-900 text-xs font-semibold text-slate-600 dark:text-slate-300"
              />
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <input
              type="text"
              placeholder="Clinical summary or extracted text findings..."
              value={docDescription}
              onChange={e => setDocDescription(e.target.value)}
              className="flex-1 p-2.5 border rounded-xl bg-white dark:bg-slate-900 font-semibold text-xs text-slate-800 dark:text-slate-200 outline-none"
            />
            <button
              type="submit"
              disabled={isUploadingDoc}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs cursor-pointer border-none shadow-xs disabled:opacity-50"
            >
              {isUploadingDoc ? 'Uploading...' : 'Upload File'}
            </button>
          </div>
        </form>

        {/* Documents List */}
        {documents.length === 0 ? (
          <div className="p-6 text-center text-xs font-semibold text-slate-400 bg-slate-50 dark:bg-slate-950 rounded-xl">
            No medical documents in vault. Upload lab reports above to allow AI Chatbot document extraction.
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-850">
            {documents.map(doc => (
              <div key={doc.id} className="py-3 flex items-center justify-between gap-4 text-xs">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-black text-slate-900 dark:text-slate-100">{doc.title}</span>
                    <span className="px-2 py-0.2 rounded text-[9px] font-black uppercase bg-blue-50 text-blue-700 border border-blue-200">
                      {doc.document_type}
                    </span>
                  </div>
                  {doc.description && <p className="text-[11px] text-slate-500 leading-snug">{doc.description}</p>}
                  <span className="text-[9px] text-slate-400 block">Uploaded: {doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Recent'}</span>
                </div>
                <div className="flex items-center gap-2">
                  {doc.file && (
                    <a
                      href={doc.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-[10px] rounded-lg inline-flex items-center gap-1 text-decoration-none"
                    >
                      <Download className="w-3 h-3" />
                      <span>View</span>
                    </a>
                  )}
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="p-1 text-slate-400 hover:text-red-600 bg-transparent border-none cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Profile Modal */}
      {isProfileModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">Edit Patient Health Profile</h3>
              <button onClick={() => setIsProfileModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Full Name</label>
                <input type="text" value={profileForm.name} onChange={e => setProfileForm({...profileForm, name: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Date of Birth</label>
                  <input type="date" value={profileForm.dob} onChange={e => setProfileForm({...profileForm, dob: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Age (Years)</label>
                  <input type="number" value={profileForm.age} onChange={e => setProfileForm({...profileForm, age: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Gender</label>
                  <select value={profileForm.gender} onChange={e => setProfileForm({...profileForm, gender: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold">
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Blood Group</label>
                  <input type="text" placeholder="e.g. A+, O-, B+" value={profileForm.bloodGroup} onChange={e => setProfileForm({...profileForm, bloodGroup: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Phone Number</label>
                <input type="text" value={profileForm.phone} onChange={e => setProfileForm({...profileForm, phone: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Address</label>
                <textarea value={profileForm.address} onChange={e => setProfileForm({...profileForm, address: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 h-16" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Emergency Contact Name</label>
                  <input type="text" value={profileForm.emergencyContactName} onChange={e => setProfileForm({...profileForm, emergencyContactName: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Emergency Contact Phone</label>
                  <input type="text" value={profileForm.emergencyContactPhone} onChange={e => setProfileForm({...profileForm, emergencyContactPhone: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setIsProfileModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">Cancel</button>
              <button onClick={handleSaveProfile} className="px-4 py-2 bg-blue-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">Save Profile</button>
            </div>
          </div>
        </div>
      )}

      {/* Condition Modal */}
      {isConditionModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">{editingConditionId ? 'Edit Health Condition' : 'Record Health Condition'}</h3>
              <button onClick={() => setIsConditionModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Condition Name *</label>
                <input type="text" placeholder="e.g. Hypertension, Diabetes Type 2" value={conditionForm.conditionName} onChange={e => setConditionForm({...conditionForm, conditionName: e.target.value})} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Clinical Description</label>
                <input type="text" placeholder="Brief diagnosis details..." value={conditionForm.description} onChange={e => setConditionForm({...conditionForm, description: e.target.value})} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Diagnosis Date</label>
                  <input type="date" value={conditionForm.diagnosisDate} onChange={e => setConditionForm({...conditionForm, diagnosisDate: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950" />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase">Status</label>
                  <select value={conditionForm.status} onChange={e => setConditionForm({...conditionForm, status: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold">
                    <option value="Active">Active</option>
                    <option value="Managed">Managed</option>
                    <option value="Resolved">Resolved</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setIsConditionModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">Cancel</button>
              <button onClick={handleSaveCondition} className="px-4 py-2 bg-amber-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">Save Condition</button>
            </div>
          </div>
        </div>
      )}

      {/* Allergy Modal */}
      {isAllergyModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in text-left">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider">{editingAllergyId ? 'Edit Allergy Record' : 'Record Allergy'}</h3>
              <button onClick={() => setIsAllergyModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-base font-bold bg-transparent border-none cursor-pointer">✕</button>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Allergen *</label>
                <input type="text" placeholder="e.g. Penicillin, Latex, Peanuts" value={allergyForm.allergen} onChange={e => setAllergyForm({...allergyForm, allergen: e.target.value})} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Reaction</label>
                <input type="text" placeholder="e.g. Anaphylaxis, Rash, Dyspnea" value={allergyForm.reaction} onChange={e => setAllergyForm({...allergyForm, reaction: e.target.value})} className="w-full p-2.5 border rounded-xl bg-slate-50 dark:bg-slate-950" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase">Severity</label>
                <select value={allergyForm.severity} onChange={e => setAllergyForm({...allergyForm, severity: e.target.value})} className="w-full p-2 border rounded-xl bg-slate-50 dark:bg-slate-950 font-bold">
                  <option value="Mild">Mild</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Severe">Severe</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setIsAllergyModalOpen(false)} className="px-4 py-2 bg-slate-100 text-slate-700 font-bold text-xs rounded-xl border-none cursor-pointer">Cancel</button>
              <button onClick={handleSaveAllergy} className="px-4 py-2 bg-red-600 text-white font-bold text-xs rounded-xl border-none cursor-pointer">Save Allergy</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthRecordsPage;
