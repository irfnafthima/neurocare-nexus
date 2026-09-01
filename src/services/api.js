const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

/**
 * Returns the base URL for API requests.
 */
export const getBaseUrl = () => API_BASE_URL;

/**
 * Formats a path relative to the API base URL.
 * @param {string} path - The API path (e.g. '/auth/login').
 * @returns {string} The fully qualified API URL.
 */
export const getApiUrl = (path) => {
  if (!path) return API_BASE_URL;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;

  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (cleanPath.startsWith('/api/')) {
    return `${API_BASE_URL}${cleanPath.substring(4)}`;
  }
  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Centralized API Endpoints Helpers for Core Healthcare Modules
 */
export const apiService = {
  // Doctor Verification
  verifyDoctor: (authFetch, payload) => authFetch(getApiUrl('/auth/verify-doctor'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),

  // Health Records
  getHealthRecords: (authFetch, patientId) => authFetch(getApiUrl(`/health-records?patientId=${patientId || ''}`)),
  addHealthRecord: (authFetch, payload) => authFetch(getApiUrl('/health-records'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  deleteHealthRecordItem: (authFetch, itemType, pk) => authFetch(getApiUrl(`/health-records/${itemType}/${pk}`), { method: 'DELETE' }),
  updateHealthRecordItem: (authFetch, itemType, pk, payload) => authFetch(getApiUrl(`/health-records/${itemType}/${pk}`), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),

  // Prescriptions
  getPrescriptions: (authFetch, patientId) => authFetch(getApiUrl(`/prescriptions?patientId=${patientId || ''}`)),
  addPrescription: (authFetch, payload) => authFetch(getApiUrl('/prescriptions'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),

  // Documents
  getDocuments: (authFetch, patientId) => authFetch(getApiUrl(`/documents?patientId=${patientId || ''}`)),
  uploadDocument: (authFetch, formData) => authFetch(getApiUrl('/documents'), { method: 'POST', body: formData }),

  // Access Control Revocations
  revokeCaregiverLink: (authFetch, linkId) => authFetch(getApiUrl(`/caregivers/requests/${linkId}`), { method: 'DELETE' }),
  revokeFamilyLink: (authFetch, linkId) => authFetch(getApiUrl(`/family/requests/${linkId}`), { method: 'DELETE' })
};
