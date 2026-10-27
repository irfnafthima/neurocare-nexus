/**
 * Safe Patient Context Identification Utilities
 * Ensures physical WearableDevice serial numbers (e.g. NCN-ESP32-001)
 * are NEVER erroneously substituted for patient clinical record IDs (e.g. P-13).
 */

export const resolveUserPatientId = (user, fallback = 'P-13') => {
  if (!user) return fallback;
  if (user.patientId) return user.patientId;
  if (user.patient_id) return user.patient_id;
  const role = typeof user.role === 'string' ? user.role.toLowerCase() : '';
  if (role === 'patient') {
    if (user.deviceId && /^NP-/i.test(user.deviceId)) {
      return user.deviceId.replace(/^NP-/i, 'P-');
    }
    if (user.deviceId && /^P-/i.test(user.deviceId)) {
      return user.deviceId;
    }
  }
  return fallback;
};

export const derivePatientContextId = ({
  queryPatientId = null,
  user = null,
  isClinician = false,
  fallback = 'P-13'
} = {}) => {
  if (queryPatientId) {
    try { sessionStorage.setItem('nexus_selected_patient_id', queryPatientId); } catch (e) {}
    return queryPatientId;
  }
  let stored = null;
  try { stored = sessionStorage.getItem('nexus_selected_patient_id'); } catch (e) {}

  const role = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';

  if (role === 'patient') {
    return resolveUserPatientId(user, fallback);
  }

  if (role === 'family') {
    return resolveUserPatientId(user, stored || fallback);
  }

  if (stored && (isClinician || role === 'doctor' || role === 'caregiver')) {
    return stored;
  }

  return stored || fallback;
};
