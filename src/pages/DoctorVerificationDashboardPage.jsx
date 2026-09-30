import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import {
  ShieldCheck,
  ShieldAlert,
  Clock,
  FileText,
  Upload,
  Download,
  AlertCircle,
  RefreshCw,
  LogOut,
  CheckCircle2,
  FileSpreadsheet,
  Building,
  Stethoscope,
  Info
} from 'lucide-react';

export const DoctorVerificationDashboardPage = () => {
  const { user, logout, authFetch } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [statusData, setStatusData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  // Upload form state
  const [documentType, setDocumentType] = useState('MEDICAL_LICENSE');
  const [doctorNotes, setDoctorNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState('');

  const fetchVerificationStatus = async () => {
    try {
      setIsLoading(true);
      const res = await authFetch(getApiUrl('/doctor/verification-status'));
      if (res.ok) {
        const data = await res.json();
        setStatusData(data);
      } else {
        addToast('Failed to fetch doctor verification status.', 'error');
      }
    } catch (e) {
      console.error('Error fetching verification status:', e);
      addToast('Error connecting to verification server.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVerificationStatus();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    setFileError('');
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    const maxSizeBytes = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|png|jpg|jpeg)$/i)) {
      setFileError('Invalid file type. Only PDF, PNG, JPG, and JPEG documents are permitted.');
      setSelectedFile(null);
      return;
    }

    if (file.size > maxSizeBytes) {
      setFileError('File size exceeds the 10MB limit.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setFileError('Please select a valid document file to upload.');
      return;
    }

    try {
      setIsUploading(true);
      const formData = new FormData();
      formData.append('document_file', selectedFile);
      formData.append('file', selectedFile);
      formData.append('document_type', documentType);
      formData.append('documentType', documentType);
      if (doctorNotes.trim()) {
        formData.append('notes', doctorNotes.trim());
      }

      // If there is an existing pending/requested document record for this type, link it
      const existingRequestedDoc = (statusData?.documents || []).find(
        (d) => (d.document_type === documentType || d.documentType === documentType) && d.status === 'REQUESTED'
      );
      if (existingRequestedDoc) {
        formData.append('document_id', existingRequestedDoc.id);
        formData.append('documentId', existingRequestedDoc.id);
      }

      const res = await authFetch(getApiUrl('/doctor/documents/upload'), {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const result = await res.json();
        addToast(result.message || 'Document uploaded successfully.', 'success');
        setSelectedFile(null);
        setDoctorNotes('');
        // Reset file input
        const fileInput = document.getElementById('verification-file-input');
        if (fileInput) fileInput.value = '';
        fetchVerificationStatus();
      } else {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
        addToast(err.detail || err.error || 'Failed to upload document.', 'error');
      }
    } catch (e) {
      console.error('Document upload error:', e);
      addToast('Network error while uploading document.', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadDocument = async (docId, fileName) => {
    try {
      const res = await authFetch(getApiUrl(`/doctor/documents/download/${docId}`));
      if (!res.ok) {
        addToast('Unable to download file. It may be missing or inaccessible.', 'error');
        return;
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName || `doctor_document_${docId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      console.error('Download error:', e);
      addToast('Failed to download document.', 'error');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span className="px-3 py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Verified & Approved
          </span>
        );
      case 'DOCUMENTS_REQUESTED':
        return (
          <span className="px-3 py-1 bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5 animate-pulse">
            <AlertCircle className="w-3.5 h-3.5" /> Documents Requested
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="px-3 py-1 bg-blue-500/15 text-blue-700 dark:text-blue-400 border border-blue-500/30 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Under Administrative Review
          </span>
        );
      case 'REJECTED':
        return (
          <span className="px-3 py-1 bg-red-500/15 text-red-700 dark:text-red-400 border border-red-500/30 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" /> Application Not Approved
          </span>
        );
      case 'PENDING':
      default:
        return (
          <span className="px-3 py-1 bg-slate-500/15 text-slate-700 dark:text-slate-300 border border-slate-500/30 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> Verification Pending
          </span>
        );
    }
  };

  const getDocumentStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED':
        return (
          <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded-lg text-[10px] font-black uppercase">
            ✓ Accepted
          </span>
        );
      case 'RESUBMISSION_REQUIRED':
        return (
          <span className="px-2.5 py-0.5 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800 rounded-lg text-[10px] font-black uppercase">
            ⚠ Resubmission Required
          </span>
        );
      case 'PENDING':
      default:
        return (
          <span className="px-2.5 py-0.5 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-lg text-[10px] font-black uppercase">
            ⏳ Pending Review
          </span>
        );
    }
  };

  const docTypeLabels = {
    MEDICAL_LICENSE: 'Medical Council License',
    BOARD_CERTIFICATION: 'Board / Degree Certificate',
    IDENTITY_PROOF: 'Government Photo ID / Aadhaar / Passport',
    CLINICAL_EXPERIENCE: 'Clinical Experience Certificate',
    OTHER: 'Supplementary Supporting Document'
  };

  const currentStatus = statusData?.verification_status || user?.verification_status || 'PENDING';
  const isRestricted = statusData?.is_restricted ?? true;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans select-none text-left p-4 sm:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Top Navigation Bar */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4 sm:p-6 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-md">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-lg sm:text-xl font-black text-slate-900 dark:text-slate-100">
                  Doctor Verification Portal
                </h1>
                {getStatusBadge(currentStatus)}
              </div>
              <p className="text-xs font-semibold text-slate-500 mt-0.5">
                {user?.name || user?.full_name || 'Doctor'} • Medical Reg: <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{statusData?.medical_registration_number || user?.medicalRegistrationNumber || 'N/A'}</span> • {statusData?.state_medical_council || 'State Medical Council'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={fetchVerificationStatus}
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold transition-colors border-none cursor-pointer"
              title="Refresh status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="flex items-center gap-1.5 px-3 py-2 bg-red-50 hover:bg-red-100 dark:bg-red-950/40 text-red-600 dark:text-red-400 rounded-xl text-xs font-bold transition-colors border-none cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        {/* Status Notice Banner */}
        <div className={`p-5 rounded-2xl border text-xs sm:text-sm font-semibold space-y-2 ${
          currentStatus === 'DOCUMENTS_REQUESTED'
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200'
            : currentStatus === 'REJECTED'
            ? 'bg-red-500/10 border-red-500/30 text-red-900 dark:text-red-200'
            : currentStatus === 'UNDER_REVIEW'
            ? 'bg-blue-500/10 border-blue-500/30 text-blue-900 dark:text-blue-200'
            : 'bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300'
        }`}>
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 flex-shrink-0 mt-0.5 text-current" />
            <div className="space-y-1">
              <h3 className="font-black text-sm">
                {currentStatus === 'DOCUMENTS_REQUESTED' && 'Action Required: Additional Verification Documents Requested'}
                {currentStatus === 'UNDER_REVIEW' && 'Account Under Administrative Review'}
                {currentStatus === 'REJECTED' && 'Registration Application Rejected'}
                {currentStatus === 'PENDING' && 'Registration Verification In Progress'}
                {currentStatus === 'VERIFIED' && 'Account Fully Verified & Active'}
              </h3>
              <p className="text-xs leading-relaxed opacity-90">
                {currentStatus === 'DOCUMENTS_REQUESTED' &&
                  (statusData?.requested_document_notes ||
                    'The administrator has reviewed your application and requested additional supporting documents (such as your Medical Council Registration Certificate, Board Degree, or Government Photo ID). Please upload the requested files below.')}
                {currentStatus === 'UNDER_REVIEW' &&
                  'Your submitted medical credentials are undergoing cross-verification against National/State Medical Council registries. You will receive an automated email notification once review is complete.'}
                {currentStatus === 'REJECTED' &&
                  (statusData?.rejection_reason ||
                    'Your application could not be verified against the medical council database or failed credential verification. Please reach out to the platform administration for assistance.')}
                {currentStatus === 'PENDING' &&
                  'Your registration has been received. While your account is pending approval, clinical and patient records remain protected to ensure patient safety and HIPAA compliance.'}
                {currentStatus === 'VERIFIED' &&
                  'Your medical credentials have been verified and approved by the system administrator. You have full clinical access.'}
              </p>
            </div>
          </div>
        </div>

        {/* Main Grid: Upload Widget & Documents Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Upload Documents Card */}
          <div className="lg:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
              <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Upload className="w-4 h-4 text-blue-600" />
                Upload Verification Document
              </h2>
              <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
                Upload verified PDFs or clear scans (PNG/JPG, max 10MB).
              </p>
            </div>

            <form onSubmit={handleUploadDocument} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-slate-500 dark:text-slate-400">
                  Document Type *
                </label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500"
                >
                  <option value="MEDICAL_LICENSE">Medical Council License / Reg Certificate</option>
                  <option value="BOARD_CERTIFICATION">Board / Degree Certificate (MBBS / MD / DM)</option>
                  <option value="IDENTITY_PROOF">Government Photo ID / Aadhaar / Passport</option>
                  <option value="CLINICAL_EXPERIENCE">Clinical Experience Certificate</option>
                  <option value="OTHER">Other Supporting Document</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-slate-500 dark:text-slate-400">
                  Doctor Notes / Context (Optional)
                </label>
                <textarea
                  rows="2"
                  placeholder="e.g. Karnataka Medical Council renewal copy 2026..."
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] font-black uppercase text-slate-500 dark:text-slate-400">
                  Select File * (PDF, PNG, JPG, max 10MB)
                </label>
                <input
                  id="verification-file-input"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                  onChange={handleFileChange}
                  className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-600 hover:file:bg-blue-100 cursor-pointer"
                />
                {fileError && (
                  <p className="text-[11px] text-red-600 font-bold mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                    {fileError}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isUploading || !selectedFile}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-sm transition-colors border-none cursor-pointer flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Uploading Encrypted File...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-3.5 h-3.5" />
                    <span>Submit for Admin Review</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Right Column: Submitted Documents List */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  Submitted Verification Documents
                </h2>
                <p className="text-[11px] text-slate-500 font-semibold mt-0.5">
                  Secure encrypted files stored in private medical vault.
                </p>
              </div>
              <span className="text-[10px] font-black uppercase text-slate-400">
                {(statusData?.documents || []).length} Uploaded
              </span>
            </div>

            {(!statusData?.documents || statusData.documents.length === 0) ? (
              <div className="py-12 text-center space-y-2">
                <FileSpreadsheet className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
                <p className="text-xs font-bold text-slate-600 dark:text-slate-400">
                  No verification documents uploaded yet.
                </p>
                <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
                  Upload your state medical registration certificate or degree above to expedite administrative verification.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-850">
                {statusData.documents.map((doc) => (
                  <div key={doc.id} className="py-3.5 space-y-2">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-black text-xs text-slate-900 dark:text-slate-100">
                            {docTypeLabels[doc.document_type] || doc.document_type}
                          </span>
                          {getDocumentStatusBadge(doc.status)}
                        </div>
                        <p className="text-[11px] text-slate-500 font-mono">
                          {doc.original_filename || doc.fileName || doc.title || 'Document'} • {((doc.file_size_bytes || doc.fileSize || 0) > 0 ? (((doc.file_size_bytes || doc.fileSize) / 1024).toFixed(1) + ' KB') : (doc.status === 'REQUESTED' ? 'Pending Upload' : '—'))} • {doc.created_at || doc.submittedAt ? `Uploaded ${new Date(doc.created_at || doc.submittedAt).toLocaleDateString()}` : 'Requested by Administrator'}
                        </p>
                      </div>

                      {(doc.status !== 'REQUESTED' || doc.file_name) && (
                        <button
                          onClick={() => handleDownloadDocument(doc.id, doc.original_filename || doc.fileName)}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold border-none cursor-pointer flex items-center gap-1.5 transition-colors self-start sm:self-auto"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </button>
                      )}
                    </div>

                    {/* Doctor notes or Admin review notes */}
                    {doc.doctor_notes && (
                      <p className="text-[11px] text-slate-500 bg-slate-50 dark:bg-slate-950 p-2 rounded-lg italic">
                        Doctor Note: "{doc.doctor_notes}"
                      </p>
                    )}
                    {doc.admin_review_notes && (
                      <p className={`text-[11px] font-semibold p-2 rounded-lg ${
                        doc.status === 'RESUBMISSION_REQUIRED'
                          ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300'
                          : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                      }`}>
                        Admin Review: {doc.admin_review_notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Help & Support Footer Card */}
        <div className="bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 font-semibold">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <span>Need verification assistance or urgent credential activation? Contact support at <strong className="text-slate-800 dark:text-slate-200">neurocarenexus@gmail.com</strong></span>
          </div>
          <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
            NeuroCare Nexus Compliance Engine v2.4
          </span>
        </div>

      </div>
    </div>
  );
};

export default DoctorVerificationDashboardPage;
