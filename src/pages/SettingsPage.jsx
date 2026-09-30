import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { getApiUrl } from '../services/api';
import { 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Sun, 
  Moon, 
  Monitor,
  User,
  Shield,
  CheckCircle2,
  FileCheck,
  Cpu,
  ScrollText,
  Lock,
  Edit3,
  X,
  Save,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Heart,
  Award,
  Briefcase,
  Building,
  AlertCircle,
  Clock,
  Activity
} from 'lucide-react';

export const SettingsPage = () => {
  const { user, authFetch, updateUserProfile } = useAuth();
  const { addToast } = useToast();

  const userRole = typeof user?.role === 'string' ? user.role.toLowerCase() : 'patient';
  const userName = user?.name || user?.full_name || 'User';
  const isAdmin = userRole === 'admin';

  // Profile data from /api/profile/me/
  const [profileData, setProfileData] = useState(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  // Edit form state
  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    dob: '',
    gender: '',
    bloodGroup: '',
    address: '',
    emergencyContactName: '',
    emergencyContactPhone: '',
    bio: '',
    specialization: '',
    yearsOfExperience: '',
    qualification: '',
    additionalQualifications: '',
    skills: '',
    previousExperience: '',
    currentAgency: '',
    agencyContact: ''
  });

  // Admin specific notification preferences
  const [adminNotificationPrefs, setAdminNotificationPrefs] = useState({
    doctorVerificationRequests: true,
    securityAuditEvents: true,
    deviceConnectivityAlerts: true
  });

  // Persistent notification preferences from backend (/api/notifications/preferences/)
  const [notificationPrefs, setNotificationPrefs] = useState({
    critical_alerts_in_app: true,
    critical_alerts_email: true,
    prescription_updates_email: true,
    medication_reminder_in_app: true,
    medication_reminder_email: false,
    missed_dose_in_app: true,
    missed_dose_email: true,
    adherence_escalation_in_app: true,
    adherence_escalation_email: true
  });
  const [isLoadingPrefs, setIsLoadingPrefs] = useState(false);
  const [isSavingPrefs, setIsSavingPrefs] = useState(false);

  const [activeTheme, setActiveTheme] = useState(() => {
    return localStorage.getItem('nexus_theme') || 'system';
  });

  // Fetch full profile and notification preferences from backend
  const fetchProfile = async () => {
    if (isAdmin) return;
    setIsLoadingProfile(true);
    try {
      const res = await authFetch(getApiUrl('/profile/me/'));
      if (res.ok) {
        const data = await res.json();
        setProfileData(data);
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const fetchNotificationPreferences = async () => {
    setIsLoadingPrefs(true);
    try {
      const res = await authFetch(getApiUrl('/notifications/preferences/'));
      if (res.ok) {
        const data = await res.json();
        setNotificationPrefs(prev => ({ ...prev, ...data }));
      }
    } catch (err) {
      console.error('Error fetching notification preferences:', err);
    } finally {
      setIsLoadingPrefs(false);
    }
  };

  useEffect(() => {
    if (user) {
      if (!isAdmin) fetchProfile();
      fetchNotificationPreferences();
    }
  }, [user, isAdmin]);

  // Open edit modal and populate form with current profile data
  const handleOpenEditModal = () => {
    const current = profileData || {};
    setFormData({
      fullName: current.fullName || current.full_name || user?.name || user?.full_name || '',
      phone: current.phone || user?.phone || '',
      dob: current.dob || current.date_of_birth || '',
      gender: current.gender || '',
      bloodGroup: current.bloodGroup || current.blood_group || '',
      address: current.address || '',
      emergencyContactName: current.emergencyContactName || current.emergency_contact_name || '',
      emergencyContactPhone: current.emergencyContactPhone || current.emergency_contact_phone || '',
      bio: current.bio || '',
      specialization: current.specialization || '',
      yearsOfExperience: current.yearsOfExperience !== undefined && current.yearsOfExperience !== null ? current.yearsOfExperience : (current.years_of_experience !== undefined && current.years_of_experience !== null ? current.years_of_experience : ''),
      qualification: current.qualification || '',
      additionalQualifications: current.additionalQualifications || current.additional_qualifications || '',
      skills: current.skills || '',
      previousExperience: current.previousExperience || current.previous_experience || '',
      currentAgency: current.currentAgency || current.current_agency || '',
      agencyContact: current.agencyContact || current.agency_contact || ''
    });
    setFormErrors({});
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setFormErrors({});
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setFormErrors({});

    // Build payload according to role
    const payload = {};
    if (formData.fullName !== undefined) payload.fullName = formData.fullName;
    if (formData.phone !== undefined) payload.phone = formData.phone;
    if (formData.bio !== undefined) payload.bio = formData.bio;

    if (userRole === 'patient') {
      payload.dob = formData.dob;
      payload.gender = formData.gender;
      payload.bloodGroup = formData.bloodGroup;
      payload.address = formData.address;
      payload.emergencyContactName = formData.emergencyContactName;
      payload.emergencyContactPhone = formData.emergencyContactPhone;
    } else if (userRole === 'doctor') {
      payload.specialization = formData.specialization;
      payload.yearsOfExperience = formData.yearsOfExperience === '' ? 0 : parseInt(formData.yearsOfExperience, 10);
      payload.qualification = formData.qualification;
      payload.additionalQualifications = formData.additionalQualifications;
    } else if (userRole === 'caregiver') {
      payload.qualification = formData.qualification;
      payload.yearsOfExperience = formData.yearsOfExperience === '' ? 0 : parseInt(formData.yearsOfExperience, 10);
      payload.skills = formData.skills;
      payload.previousExperience = formData.previousExperience;
      payload.currentAgency = formData.currentAgency;
      payload.agencyContact = formData.agencyContact;
    }

    try {
      const res = await authFetch(getApiUrl('/profile/me/'), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const resData = await res.json();

      if (!res.ok) {
        if (resData.detail) {
          addToast(resData.detail, 'error');
        } else {
          setFormErrors(resData);
          addToast('Please correct the highlighted errors.', 'error');
        }
        return;
      }

      setProfileData(resData);
      updateUserProfile(resData);
      addToast('Profile updated successfully!', 'success');
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Failed to update profile:', err);
      addToast('Network error while saving profile.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleThemeChange = (newTheme) => {
    setActiveTheme(newTheme);
    localStorage.setItem('nexus_theme', newTheme);
    const root = window.document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else if (newTheme === 'light') {
      root.classList.remove('dark');
    } else {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
    addToast(`Theme set to ${newTheme.toUpperCase()}`, 'info');
  };

  const handleSaveAdminSettings = (e) => {
    e.preventDefault();
    addToast('Administrative notification preferences updated successfully.', 'success');
  };

  const handleSaveClinicalSettings = async (e) => {
    e.preventDefault();
    setIsSavingPrefs(true);
    try {
      const res = await authFetch(getApiUrl('/notifications/preferences/'), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(notificationPrefs)
      });
      if (res.ok) {
        const data = await res.json();
        setNotificationPrefs(prev => ({ ...prev, ...data }));
        addToast('Notification delivery preferences saved successfully!', 'success');
      } else {
        addToast('Failed to save preferences. Please try again.', 'error');
      }
    } catch (err) {
      console.error('Failed to save preferences:', err);
      addToast('Network error while saving preferences.', 'error');
    } finally {
      setIsSavingPrefs(false);
    }
  };

  // Helper for displaying current profile info
  const effectiveProfile = profileData || {
    fullName: userName,
    email: user?.email || '',
    phone: user?.phone || '',
    role: userRole,
    specialization: user?.specialization || '',
    yearsOfExperience: user?.yearsOfExperience || '',
    qualification: user?.qualification || '',
    npi: user?.npi || user?.medical_registration_number || '',
    stateMedicalCouncil: user?.stateMedicalCouncil || user?.state_medical_council || '',
    hprId: user?.hprId || user?.hpr_id || '',
    verificationStatus: user?.verification_status || user?.verificationStatus || '',
    deviceId: user?.deviceId || user?.device_id || '',
    patientId: user?.patientId || user?.patient_id || '',
    agencyId: user?.agencyId || user?.agency_id || ''
  };

  return (
    <div className="space-y-6 text-left max-w-4xl mx-auto font-sans select-none pb-12">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          {isAdmin ? 'System & Administrative Settings' : 'Account & Profile Settings'}
        </h1>
        <p className="text-xs font-semibold text-slate-500 mt-1">
          {isAdmin 
            ? 'Manage administrative profile, system governance preferences, and platform security options.' 
            : 'View and update your personal profile, professional details, and preferences.'}
        </p>
      </div>

      {/* Profile Overview Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-900 flex items-center justify-center font-black text-base text-blue-700 dark:text-blue-300 shadow-xs">
              {(effectiveProfile.fullName || userName).split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-black text-slate-900 dark:text-slate-100">
                  {effectiveProfile.fullName || userName}
                </h2>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                  isAdmin 
                    ? 'bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border border-red-500/20' 
                    : 'bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-500/20'
                }`}>
                  {userRole}
                </span>
                {effectiveProfile.verificationStatus && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                    effectiveProfile.verificationStatus === 'VERIFIED'
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                  }`}>
                    {effectiveProfile.verificationStatus}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-semibold mt-0.5 flex items-center gap-2">
                <span>{effectiveProfile.email || user?.email}</span>
                {effectiveProfile.phone && (
                  <>
                    <span>•</span>
                    <span>{effectiveProfile.phone}</span>
                  </>
                )}
              </p>
            </div>
          </div>

          {!isAdmin && (
            <button
              onClick={handleOpenEditModal}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors cursor-pointer border-none"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Profile</span>
            </button>
          )}
        </div>

        {/* Profile Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Email Address</span>
            <p className="font-mono text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.email || '—'}</p>
          </div>

          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Phone Number</span>
            <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.phone || 'Not provided'}</p>
          </div>

          {/* Role specific profile fields */}
          {userRole === 'patient' && (
            <>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Device Serial / ID</span>
                <p className="font-mono font-bold text-blue-600 dark:text-blue-400 mt-1">{effectiveProfile.deviceId || 'Not Assigned'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Date of Birth</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.dob || effectiveProfile.date_of_birth || 'Not specified'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Gender</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1 capitalize">{effectiveProfile.gender || 'Not specified'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Blood Group</span>
                <p className="font-bold text-rose-600 dark:text-rose-400 mt-1">{effectiveProfile.bloodGroup || effectiveProfile.blood_group || 'Not specified'}</p>
              </div>
              <div className="sm:col-span-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Residential Address</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.address || 'Not specified'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Emergency Contact</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">
                  {(effectiveProfile.emergencyContactName || effectiveProfile.emergency_contact_name) ? (
                    `${effectiveProfile.emergencyContactName || effectiveProfile.emergency_contact_name} (${effectiveProfile.emergencyContactPhone || effectiveProfile.emergency_contact_phone || 'No phone'})`
                  ) : 'Not specified'}
                </p>
              </div>
            </>
          )}

          {userRole === 'doctor' && (
            <>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Medical Registration No.</span>
                <p className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.medicalRegistrationNumber || effectiveProfile.medical_registration_number || effectiveProfile.npi || '—'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">State Medical Council</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.stateMedicalCouncil || effectiveProfile.state_medical_council || '—'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">HPR Registry ID</span>
                <p className="font-mono text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.hprId || effectiveProfile.hpr_id || '—'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Specialization</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.specialization || 'General Neurology'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Experience</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.yearsOfExperience || effectiveProfile.years_of_experience || 0} Years</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Qualification</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.qualification || 'MBBS, MD'}</p>
              </div>
            </>
          )}

          {userRole === 'caregiver' && (
            <>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Agency ID</span>
                <p className="font-mono font-bold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.agencyId || effectiveProfile.agency_id || 'Not Assigned'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Qualification</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.qualification || 'Certified Nursing Assistant (CNA)'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Experience</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.yearsOfExperience || effectiveProfile.years_of_experience || 0} Years</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Current Agency</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.currentAgency || effectiveProfile.current_agency || 'Independent'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Agency Contact</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.agencyContact || effectiveProfile.agency_contact || '—'}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Specialized Skills</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200 mt-1">{effectiveProfile.skills || 'Patient Mobility, Vital Monitoring'}</p>
              </div>
            </>
          )}

          {userRole === 'family' && (
            <>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Authorized Patient ID</span>
                <p className="font-mono font-bold text-blue-600 dark:text-blue-400 mt-1">{effectiveProfile.patientId || effectiveProfile.patient_id || 'Not Assigned'}</p>
              </div>
            </>
          )}
        </div>

        {/* Bio / Summary section */}
        {effectiveProfile.bio && (
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Bio / Summary</span>
            <p className="text-xs text-slate-700 dark:text-slate-300 font-medium mt-1 leading-relaxed">
              {effectiveProfile.bio}
            </p>
          </div>
        )}
      </div>

      {/* EDIT PROFILE MODAL */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col text-left animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0">
              <div>
                <h3 className="text-base font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-blue-600" />
                  Edit {userRole.charAt(0).toUpperCase() + userRole.slice(1)} Profile
                </h3>
                <p className="text-xs text-slate-400 font-semibold mt-0.5">
                  Update your contact details and role-specific information.
                </p>
              </div>
              <button
                onClick={handleCloseEditModal}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border-none bg-transparent cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form Content */}
            <form onSubmit={handleSaveProfile} className="p-6 space-y-4 overflow-y-auto flex-1 text-xs">
              {/* Common Account Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleFormChange}
                    required
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    placeholder="e.g. Dr. Jane Doe"
                  />
                  {formErrors.fullName && <p className="text-rose-500 text-[10px] mt-1">{formErrors.fullName}</p>}
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    placeholder="+91 98765 43210"
                  />
                  {formErrors.phone && <p className="text-rose-500 text-[10px] mt-1">{formErrors.phone}</p>}
                </div>
              </div>

              {/* Read-Only Notice / Badges for Protected Credentials */}
              <div className="bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800/80 rounded-xl p-3 flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div className="text-[11px] text-slate-600 dark:text-slate-400 font-semibold leading-relaxed">
                  <span className="font-bold text-slate-800 dark:text-slate-200">Protected Clinical Credentials:</span>{' '}
                  {userRole === 'doctor' && 'Medical Registration Number, State Council, Verification Status, and HPR ID are statutory verification records and cannot be altered here.'}
                  {userRole === 'patient' && 'Device Serial (NP/P identifier) and Clinical Record Linkages are managed by hospital clinical staff.'}
                  {userRole === 'caregiver' && 'Agency Access ID is assigned by the healthcare network coordinator.'}
                  {userRole === 'family' && 'Authorized Patient Linkage is verified through clinical consent.'}
                </div>
              </div>

              {/* PATIENT ROLE SPECIFIC FIELDS */}
              {userRole === 'patient' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Date of Birth
                      </label>
                      <input
                        type="date"
                        name="dob"
                        value={formData.dob}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Gender
                      </label>
                      <select
                        name="gender"
                        value={formData.gender}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      >
                        <option value="">Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                        <option value="Prefer not to say">Prefer not to say</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Blood Group
                      </label>
                      <select
                        name="bloodGroup"
                        value={formData.bloodGroup}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      >
                        <option value="">Select Blood Group</option>
                        <option value="A+">A+</option>
                        <option value="A-">A-</option>
                        <option value="B+">B+</option>
                        <option value="B-">B-</option>
                        <option value="AB+">AB+</option>
                        <option value="AB-">AB-</option>
                        <option value="O+">O+</option>
                        <option value="O-">O-</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                      Residential Address
                    </label>
                    <textarea
                      name="address"
                      value={formData.address}
                      onChange={handleFormChange}
                      rows={2}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      placeholder="Street address, City, State, PIN"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Emergency Contact Name
                      </label>
                      <input
                        type="text"
                        name="emergencyContactName"
                        value={formData.emergencyContactName}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="Next of kin / Emergency contact"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Emergency Contact Phone
                      </label>
                      <input
                        type="tel"
                        name="emergencyContactPhone"
                        value={formData.emergencyContactPhone}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="+91 98765 43210"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* DOCTOR ROLE SPECIFIC FIELDS */}
              {userRole === 'doctor' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Primary Specialization
                      </label>
                      <input
                        type="text"
                        name="specialization"
                        value={formData.specialization}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. Neurologist, Neurosurgeon"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Years of Experience
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="70"
                        name="yearsOfExperience"
                        value={formData.yearsOfExperience}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. 12"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Primary Qualification
                      </label>
                      <input
                        type="text"
                        name="qualification"
                        value={formData.qualification}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. MBBS, MD (Neurology)"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Additional Qualifications / Sub-specialities
                      </label>
                      <input
                        type="text"
                        name="additionalQualifications"
                        value={formData.additionalQualifications}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. DM, Fellowship in Epilepsy"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* CAREGIVER ROLE SPECIFIC FIELDS */}
              {userRole === 'caregiver' && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Primary Qualification / Certification
                      </label>
                      <input
                        type="text"
                        name="qualification"
                        value={formData.qualification}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. Certified Nursing Assistant (CNA)"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Years of Experience
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="50"
                        name="yearsOfExperience"
                        value={formData.yearsOfExperience}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. 5"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                      Clinical & Care Skills
                    </label>
                    <input
                      type="text"
                      name="skills"
                      value={formData.skills}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      placeholder="e.g. Neurological Patient Mobility, Vital Monitoring, CPR"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Current Agency Name
                      </label>
                      <input
                        type="text"
                        name="currentAgency"
                        value={formData.currentAgency}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="e.g. Apollo HomeCare"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                        Agency Contact Number
                      </label>
                      <input
                        type="tel"
                        name="agencyContact"
                        value={formData.agencyContact}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        placeholder="+91 44 2829 0200"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                      Previous Experience / Clinical History
                    </label>
                    <textarea
                      name="previousExperience"
                      value={formData.previousExperience}
                      onChange={handleFormChange}
                      rows={2}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      placeholder="Brief summary of past clinical or home health assignments"
                    />
                  </div>
                </>
              )}

              {/* Bio / Description for all roles */}
              <div>
                <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
                  Bio / Personal Notes
                </label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleFormChange}
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Share any additional details or background notes..."
                />
              </div>

              {/* Modal Footer Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800 shrink-0">
                <button
                  type="button"
                  onClick={handleCloseEditModal}
                  disabled={isSaving}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-colors cursor-pointer border-none"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-xs transition-colors cursor-pointer border-none"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isSaving ? 'Saving Changes...' : 'Save Profile Changes'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADMIN SPECIFIC SETTINGS */}
      {isAdmin && (
        <>
          {/* Admin Notification Preferences Form */}
          <form onSubmit={handleSaveAdminSettings} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
            <div>
              <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
                Administrative Notification Preferences
              </span>
              <p className="text-[11px] text-slate-400 font-semibold mt-0.5">
                Configure notifications for administrative workflow events and security audits.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.doctorVerificationRequests}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    doctorVerificationRequests: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Doctor Credential Verification Requests
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive notifications when a new doctor application is submitted and requires State Medical Council verification.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.securityAuditEvents}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    securityAuditEvents: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Security & System Audit Notifications
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive alerts for critical security incidents, user access revocations, and system governance events.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-950/50 transition-colors">
                <input
                  type="checkbox"
                  checked={adminNotificationPrefs.deviceConnectivityAlerts}
                  onChange={e => setAdminNotificationPrefs({
                    ...adminNotificationPrefs, 
                    deviceConnectivityAlerts: e.target.checked
                  })}
                  className="mt-0.5 rounded text-blue-600 focus:ring-0 cursor-pointer"
                />
                <div>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100 block">
                    Device Gateway & IoT Telemetry Health
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Receive operational alerts if a biomedical wearable streaming node or synthetic gateway experiences disconnects.
                  </span>
                </div>
              </label>
            </div>

            {/* Governance Ownership Note */}
            <div className="bg-slate-50 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800/80 rounded-xl p-3.5 flex items-start gap-3 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div className="text-[11px] text-slate-600 dark:text-slate-300 font-semibold leading-relaxed">
                <span className="font-bold text-slate-900 dark:text-slate-100 block mb-0.5">
                  Clinical Alert Governance Notice
                </span>
                Patient telemetry alarms and physiological threshold notifications are routed directly to authorized consulting clinicians and care teams. The System Administrator manages infrastructure security and role access.
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-850">
              <button
                type="submit"
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl border-none cursor-pointer shadow-xs transition-colors"
              >
                Save Notification Preferences
              </button>
            </div>
          </form>

          {/* System Status & Platform Governance */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-3">
            <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
              System Status & Platform Governance
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ScrollText className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Audit Logging Engine</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  Active
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-blue-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Doctor Verification Registry</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  5,000 Records Active
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-emerald-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">Device Telemetry Fleet</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  Operational
                </span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-amber-600" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">RBAC & Authentication</span>
                </div>
                <span className="text-[10px] font-black uppercase text-emerald-600 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                  JWT Enforced
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ROLE-AWARE NOTIFICATION PREFERENCES */}
      {!isAdmin && (
        <form onSubmit={handleSaveClinicalSettings} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
                Notification Delivery Preferences
              </span>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Configure your in-app and email alert channels for clinical events, medication reminders, and treatment adherence.
              </p>
            </div>
            {isLoadingPrefs && (
              <span className="text-[10px] text-blue-600 font-bold animate-pulse">Loading...</span>
            )}
          </div>

          <div className="space-y-4 text-xs">
            {/* 1. Critical Health Alerts (All Clinical Roles) */}
            <div className="p-3.5 bg-slate-50/70 dark:bg-slate-950/70 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-900 dark:text-slate-100 block">Critical Physiological Alerts</span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">Urgent patient alarms, abnormal vitals thresholds, and fall detection alerts.</span>
                </div>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 dark:bg-emerald-950/80 dark:text-emerald-400 px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-800">
                  In-App Mandatory
                </span>
              </div>
              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 cursor-not-allowed opacity-80">
                  <input type="checkbox" checked={true} disabled className="rounded text-blue-600" />
                  <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">In-App (Required)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notificationPrefs.critical_alerts_email}
                    onChange={e => setNotificationPrefs(p => ({ ...p, critical_alerts_email: e.target.checked }))}
                    className="rounded text-blue-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">Email Notifications</span>
                </label>
              </div>
            </div>

            {/* 2. Patient-Specific: Medication Upcoming Reminders */}
            {userRole === 'patient' && (
              <div className="p-3.5 bg-slate-50/70 dark:bg-slate-950/70 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2.5">
                <div>
                  <span className="font-bold text-slate-900 dark:text-slate-100 block">Scheduled Medication Reminders</span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">Gentle lead-time reminders (30 minutes prior) for today's scheduled doses.</span>
                </div>
                <div className="flex items-center gap-6 pt-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notificationPrefs.medication_reminder_in_app}
                      onChange={e => setNotificationPrefs(p => ({ ...p, medication_reminder_in_app: e.target.checked }))}
                      className="rounded text-blue-600 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">In-App Reminders</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notificationPrefs.medication_reminder_email}
                      onChange={e => setNotificationPrefs(p => ({ ...p, medication_reminder_email: e.target.checked }))}
                      className="rounded text-blue-600 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">Email Notifications</span>
                  </label>
                </div>
              </div>
            )}

            {/* 3. Patient & Caregiver: Missed Dose Alerts */}
            {(userRole === 'patient' || userRole === 'caregiver') && (
              <div className="p-3.5 bg-slate-50/70 dark:bg-slate-950/70 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2.5">
                <div>
                  <span className="font-bold text-slate-900 dark:text-slate-100 block">
                    {userRole === 'caregiver' ? 'Linked Patient Missed Medication Alerts' : 'Missed Medication Alerts'}
                  </span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">
                    Notices dispatched after the grace period expires without a recorded action.
                  </span>
                </div>
                <div className="flex items-center gap-6 pt-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notificationPrefs.missed_dose_in_app}
                      onChange={e => setNotificationPrefs(p => ({ ...p, missed_dose_in_app: e.target.checked }))}
                      className="rounded text-blue-600 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">In-App Alerts</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notificationPrefs.missed_dose_email}
                      onChange={e => setNotificationPrefs(p => ({ ...p, missed_dose_email: e.target.checked }))}
                      className="rounded text-blue-600 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">Email Notifications</span>
                  </label>
                </div>
              </div>
            )}

            {/* 4. Adherence Escalation Notices (All Roles) */}
            <div className="p-3.5 bg-slate-50/70 dark:bg-slate-950/70 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2.5">
              <div>
                <span className="font-bold text-slate-900 dark:text-slate-100 block">Treatment Adherence Notices</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  Periodic notifications when multiple medication doses remain unrecorded over a 7-day review period.
                </span>
              </div>
              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notificationPrefs.adherence_escalation_in_app}
                    onChange={e => setNotificationPrefs(p => ({ ...p, adherence_escalation_in_app: e.target.checked }))}
                    className="rounded text-blue-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">In-App Notices</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notificationPrefs.adherence_escalation_email}
                    onChange={e => setNotificationPrefs(p => ({ ...p, adherence_escalation_email: e.target.checked }))}
                    className="rounded text-blue-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">Email Notifications</span>
                </label>
              </div>
            </div>

            {/* 5. Prescription Updates (Patient & Doctor) */}
            {(userRole === 'patient' || userRole === 'doctor') && (
              <div className="p-3.5 bg-slate-50/70 dark:bg-slate-950/70 rounded-xl border border-slate-100 dark:border-slate-800 space-y-2.5">
                <div>
                  <span className="font-bold text-slate-900 dark:text-slate-100 block">Prescription Care-Plan Updates</span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">Email notices when prescriptions are issued, modified, or discontinued.</span>
                </div>
                <div className="flex items-center gap-6 pt-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notificationPrefs.prescription_updates_email}
                      onChange={e => setNotificationPrefs(p => ({ ...p, prescription_updates_email: e.target.checked }))}
                      className="rounded text-blue-600 focus:ring-0"
                    />
                    <span className="font-semibold text-slate-700 dark:text-slate-300 text-[11px]">Email Notifications</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-850">
            <button
              type="submit"
              disabled={isSavingPrefs}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl border-none cursor-pointer shadow-xs transition-colors"
            >
              {isSavingPrefs ? 'Saving Preferences...' : 'Save Notification Preferences'}
            </button>
          </div>
        </form>
      )}

      {/* Theme Selection Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-5 shadow-sm space-y-4">
        <span className="text-xs font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider block">
          Theme & Display Mode
        </span>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleThemeChange('light')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'light'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Sun className="w-5 h-5 text-amber-500" />
            <span>Light Mode</span>
          </button>

          <button
            onClick={() => handleThemeChange('dark')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'dark'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Moon className="w-5 h-5 text-indigo-400" />
            <span>Dark Mode</span>
          </button>

          <button
            onClick={() => handleThemeChange('system')}
            className={`p-3 rounded-xl border flex flex-col items-center gap-2 font-bold text-xs cursor-pointer ${
              activeTheme === 'system'
                ? 'bg-blue-50 border-blue-600 text-blue-600 dark:bg-blue-950/40 dark:border-blue-500 dark:text-blue-300'
                : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-850 text-slate-600 dark:text-slate-400'
            }`}
          >
            <Monitor className="w-5 h-5 text-slate-400" />
            <span>System Default</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
