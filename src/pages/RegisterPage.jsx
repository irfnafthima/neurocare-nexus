import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { 
  Mail, 
  Lock, 
  Stethoscope, 
  Heart, 
  Pill, 
  Key, 
  ShieldCheck, 
  ArrowRight, 
  Hospital, 
  Smartphone, 
  User, 
  Sparkles, 
  CheckCircle2, 
  Calendar,
  AlertCircle,
  Check
} from 'lucide-react';
import { syntheticNpis } from '../data/mockData';
import { getApiUrl } from '../services/api';

const validateIndianPhone = (phoneStr) => {
  if (!phoneStr || !phoneStr.trim()) return 'Mobile number is required.';
  const raw = phoneStr.trim();
  if (/[^\d\+\-\s\(\)]/.test(raw)) return 'Phone number can only contain digits and country code (+91).';
  const digits = raw.replace(/\D/g, '');
  let localNum = digits;
  if (raw.startsWith('+91') || (digits.startsWith('91') && digits.length === 12)) {
    if (digits.length === 12 && digits.startsWith('91')) {
      localNum = digits.slice(2);
    } else {
      return 'Enter a valid 10-digit Indian mobile number.';
    }
  } else if (digits.startsWith('0') && digits.length === 11) {
    localNum = digits.slice(1);
  } else if (digits.length !== 10) {
    return 'Enter a valid 10-digit Indian mobile number.';
  }
  if (!/^[6-9]\d{9}$/.test(localNum)) {
    return 'Indian mobile numbers must start with 6, 7, 8, or 9 (e.g. +91 9876543210).';
  }
  return null;
};

const validateEmail = (emailStr) => {
  if (!emailStr || !emailStr.trim()) return 'Email address is required.';
  const clean = emailStr.trim().toLowerCase();
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(clean)) return 'Enter a valid email address.';
  return null;
};

const validateName = (nameStr, fieldName = 'Name') => {
  if (!nameStr || !nameStr.trim()) return `${fieldName} is required.`;
  const clean = nameStr.trim();
  if (clean.length < 2) return `${fieldName} must be at least 2 characters.`;
  // Allow letters, spaces, hyphens, apostrophes, and dots for initials (e.g. Fathima Irfana, Anne-Marie, O'Connor, A. Kumar)
  if (!/^[a-zA-Z\s\.\'\-]+$/.test(clean) || (clean.match(/[a-zA-Z]/g) || []).length < 2) {
    return `Enter a valid ${fieldName.toLowerCase()}.`;
  }
  return null;
};

const validatePassword = (passStr) => {
  if (!passStr) return 'Password is required.';
  if (passStr.length < 8) return 'Password must be at least 8 characters long.';
  return null;
};

const AuthInput = ({ 
  label, 
  type = 'text', 
  placeholder, 
  icon: Icon, 
  value, 
  onChange, 
  onBlur, 
  name, 
  error, 
  success, 
  isTouched, 
  ...rest 
}) => {
  const showError = isTouched && !!error;
  const showSuccess = isTouched && !error && !!success;

  return (
    <div className="flex flex-col gap-1.5 text-left w-full group">
      <div className="flex justify-between items-center pl-1 pr-1">
        <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500">{label}</label>
        {showSuccess && (
          <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 animate-fade-in">
            <Check className="w-3 h-3 inline stroke-[3]" /> {typeof success === 'string' ? success : 'Valid'}
          </span>
        )}
      </div>
      <div className="relative">
        {Icon && (
          <Icon className={`absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] transition-colors duration-200 select-none pointer-events-none ${
            showError 
              ? 'text-red-500' 
              : showSuccess 
              ? 'text-emerald-500' 
              : 'text-slate-400 dark:text-slate-500 group-focus-within:text-blue-500'
          }`} />
        )}
        <input
          type={type}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          autoComplete={type === 'password' ? 'new-password' : type === 'email' ? 'email' : 'off'}
          className={`w-full py-3 pr-4 border rounded-xl bg-slate-50 dark:bg-slate-900/40 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-600 outline-none transition-all font-semibold shadow-sm read-only:bg-slate-100 dark:read-only:bg-slate-900/70 read-only:cursor-not-allowed read-only:text-slate-500 ${
            showError
              ? 'border-red-500 focus:border-red-500 ring-4 ring-red-500/10'
              : showSuccess
              ? 'border-emerald-500/80 dark:border-emerald-600/80 focus:border-emerald-500 ring-4 ring-emerald-500/10'
              : 'border-slate-200 dark:border-slate-800 focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20'
          }`}
          style={{ paddingLeft: Icon ? '2.75rem' : '1rem' }}
          {...rest}
        />
      </div>
      {showError && (
        <span className="text-[10px] font-bold text-red-500 pl-1 animate-fade-in flex items-center gap-1">
          ✕ {error}
        </span>
      )}
    </div>
  );
};

const LeftPanel = () => {
  return (
    <div className="hidden lg:flex flex-col justify-between p-12 relative overflow-hidden bg-slate-950 text-white select-none">
      {/* Background illustration */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-25 mix-blend-luminosity pointer-events-none filter brightness-95"
        style={{ backgroundImage: "url('/caring_doctor_patient.png')" }}
      />

      {/* Modern gradient wash layer */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-slate-950/20 pointer-events-none" />
      
      {/* Subtle grid pattern */}
      <div className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }} />

      {/* Top Branding Logo */}
      <div className="relative z-10 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-600 shadow-md border border-blue-500/30">
          <Heart className="w-5.5 h-5.5 text-white" />
        </div>
        <div className="text-left">
          <div className="text-white font-extrabold text-[15px] tracking-tight leading-none">NeuroCare Nexus</div>
          <div className="text-[9px] text-blue-400 font-extrabold tracking-widest uppercase mt-1 leading-none">Clinical Intelligence</div>
        </div>
      </div>

      {/* Main Content Info */}
      <div className="relative z-10 space-y-6 text-left max-w-sm mt-auto mb-8 animate-fade-in-up">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full mb-4 bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]" />
            <span className="text-emerald-400 text-[10px] font-black uppercase tracking-wider">Start 14-Day Clinic Trial</span>
          </div>

          <h2 className="text-4xl font-black text-white leading-tight tracking-tight mb-3">
            Secure Remote Workspace.
          </h2>
          <p className="text-slate-355 text-xs font-semibold leading-relaxed">
            Register your clinical profile or device serials to initiate automated health record syncs (simulated for academic demonstration).
          </p>
        </div>

        {/* B2B Diagnostics Specifications Card */}
        <div className="rounded-2xl p-4 space-y-3 bg-white/5 border border-white/10 backdrop-blur-md">
          <div className="flex justify-between items-center pb-2 border-b border-white/5">
            <span className="text-slate-400 text-[9px] font-black uppercase tracking-wider">Supported Sensor Interfaces</span>
            <span className="text-emerald-400 text-[9px] font-black uppercase tracking-widest animate-pulse">Ready</span>
          </div>

          <div className="space-y-2.5 text-xs font-semibold text-slate-300">
            <div className="flex justify-between">
              <span>MAX30102 Blood Sensor</span>
              <span className="text-white font-black">HR & SpO₂</span>
            </div>
            <div className="flex justify-between">
              <span>MPU6050 Motion Sensor</span>
              <span className="text-white font-black">Accel, Gyro & Fall</span>
            </div>
            <div className="flex justify-between">
              <span>DS18B20 Temp Probe</span>
              <span className="text-white font-black">Core Temperature</span>
            </div>
            <div className="flex justify-between">
              <span>ESP32 Main MCU Link</span>
              <span className="text-white font-black">WiFi, Battery & Signal</span>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance labels */}
      <div className="relative z-10 flex gap-2 flex-wrap animate-fade-in-up">
        {['SOC 2 Type II', 'HIPAA compliant', 'FDA Class II Stream'].map(b => (
          <span key={b} className="text-[9px] px-2.5 py-1 rounded-lg font-extrabold uppercase tracking-wider text-slate-400 bg-white/5 border border-white/10">
            {b}
          </span>
        ))}
      </div>
    </div>
  );
};

export const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { addToast } = useToast();

  const [activeRole, setActiveRole] = useState('patient'); // 'doctor' | 'patient' | 'caregiver' | 'family'
  const [view, setView] = useState('register'); // 'register' | 'otp'
  const [isLoading, setIsLoading] = useState(false);
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Debounced email availability check state
  const [emailCheckStatus, setEmailCheckStatus] = useState({ checking: false, available: null, message: '' });

  // Verification step details
  const [verificationStep, setVerificationStep] = useState('idle');
  const [verificationLabel, setVerificationLabel] = useState('');

  const [statusModal, setStatusModal] = useState({ 
    isOpen: false, 
    title: '', 
    statusLabel: '', 
    message: '', 
    status: '', 
    category: '', 
    breakdown: null 
  });

  const [facilities, setFacilities] = useState([]);

  useEffect(() => {
    fetch(getApiUrl('/facilities'))
      .then(res => res.json())
      .then(data => setFacilities(Array.isArray(data) ? data : []))
      .catch(err => console.error("Error loading facilities:", err));
  }, []);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    workEmail: '',
    phone: '',
    password: '',
    confirmPassword: '',
    dob: '',
    organization: '',
    npi: '',
    medicalRegistrationNumber: '',
    stateMedicalCouncil: '',
    registrationYear: '',
    qualification: '',
    additionalQualifications: '',
    hprId: '',
    facilityId: '',
    department: '',
    designation: '',
    deviceId: '',
    agencyId: '',
    patientId: '',
    specialization: '',
    experience: '',
    bio: '',
    caregiverType: 'PROFESSIONAL',
    skills: '',
    previousExperience: '',
    currentAgency: '',
    agencyContact: ''
  });

  // Debounce email availability live check
  useEffect(() => {
    const cleanEmail = (formData.workEmail || '').trim().toLowerCase();
    const formatErr = validateEmail(cleanEmail);
    if (!cleanEmail || formatErr) {
      setEmailCheckStatus({ checking: false, available: null, message: '' });
      return;
    }

    setEmailCheckStatus({ checking: true, available: null, message: 'Checking availability...' });
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(getApiUrl(`/auth/check-email?email=${encodeURIComponent(cleanEmail)}`));
        if (res.ok) {
          const data = await res.json();
          setEmailCheckStatus({ checking: false, available: data.available, message: data.message });
          if (!data.available) {
            setErrors(prev => ({ ...prev, workEmail: data.message || 'This email address is already registered.' }));
          } else {
            setErrors(prev => {
              const next = { ...prev };
              if (next.workEmail === 'This email address is already registered.') {
                delete next.workEmail;
              }
              return next;
            });
          }
        } else {
          setEmailCheckStatus({ checking: false, available: null, message: '' });
        }
      } catch (err) {
        setEmailCheckStatus({ checking: false, available: null, message: '' });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [formData.workEmail]);

  // Live password rules checklist
  const passwordRules = {
    hasMinLength: (formData.password || '').length >= 8,
    hasUpper: /[A-Z]/.test(formData.password || ''),
    hasLower: /[a-z]/.test(formData.password || ''),
    hasNumber: /[0-9]/.test(formData.password || ''),
    hasSpecial: /[^A-Za-z0-9]/.test(formData.password || '')
  };

  const validateSingleField = (name, value, currentFormData = formData, role = activeRole) => {
    switch (name) {
      case 'firstName':
        return validateName(value, 'First name');
      case 'lastName':
        return validateName(value, 'Last name');
      case 'workEmail':
        return validateEmail(value);
      case 'phone':
        return validateIndianPhone(value);
      case 'password':
        return validatePassword(value);
      case 'confirmPassword':
        if (!value) return 'Please confirm your password.';
        if (value !== currentFormData.password) return 'Passwords do not match.';
        return null;
      case 'dob':
        if (value) {
          const selected = new Date(value);
          const today = new Date();
          today.setHours(23, 59, 59, 999);
          if (selected > today) return 'Date of birth cannot be in the future.';
        }
        return null;
      case 'medicalRegistrationNumber':
        if (role === 'doctor') {
          const reg = (value || '').trim();
          if (!reg) return 'Medical registration number is required.';
          if (reg.length < 3) return 'Valid registration number required (min 3 chars).';
        }
        return null;
      case 'stateMedicalCouncil':
        if (role === 'doctor' && !value) return 'Select your medical council.';
        return null;
      case 'registrationYear':
        if (role === 'doctor') {
          if (!value || isNaN(value)) return 'Registration year is required.';
          const y = parseInt(value, 10);
          const currY = new Date().getFullYear();
          if (y < 1950 || y > currY) return `Registration year must be between 1950 and ${currY}.`;
        }
        return null;
      case 'qualification':
        if (role === 'doctor' && (!value || !value.trim())) return 'Primary qualification is required (e.g. MBBS).';
        return null;
      case 'specialization':
        if (role === 'doctor' && !value) return 'Clinical specialization is required.';
        return null;
      case 'experience':
        if (role === 'doctor') {
          if (value === '' || value === null || isNaN(value)) return 'Years of experience is required (>= 0).';
          if (parseInt(value, 10) < 0) return 'Experience cannot be negative.';
        }
        return null;
      case 'agencyId':
        if (role === 'caregiver' && currentFormData.caregiverType === 'PROFESSIONAL' && (!value || !value.trim())) {
          return 'Agency Certificate ID is required (e.g. CG-204).';
        }
        return null;
      case 'patientId':
        if (role === 'family' && (!value || !value.trim())) {
          return 'Patient Access Code is required (e.g. P-102).';
        }
        return null;
      default:
        return null;
    }
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    const err = validateSingleField(name, value);
    setErrors(prev => ({ ...prev, [name]: err || '' }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    let newOrg = formData.organization;

    if (name === 'medicalRegistrationNumber' || name === 'npi') {
      const regVal = value;
      if (/^\d{10}$/.test(regVal)) {
        const matched = syntheticNpis.find(n => n.npi === regVal);
        newOrg = matched ? matched.hospital : '';
      } else {
        newOrg = '';
      }
    }

    const nextFormData = {
      ...formData,
      [name]: value,
      organization: (name === 'medicalRegistrationNumber' || name === 'npi') ? newOrg : formData.organization
    };

    setFormData(nextFormData);

    // Live validate if the field was already touched or has text
    if (touched[name] || (value && value.length > 0)) {
      const err = validateSingleField(name, value, nextFormData);
      setErrors(prev => ({
        ...prev,
        [name]: err || '',
        organization: (name === 'medicalRegistrationNumber' || name === 'npi') ? '' : prev.organization
      }));
    }

    // Revalidate confirmPassword when password changes
    if (name === 'password' && (touched.confirmPassword || formData.confirmPassword)) {
      const cErr = validateSingleField('confirmPassword', formData.confirmPassword, nextFormData);
      setErrors(prev => ({ ...prev, confirmPassword: cErr || '' }));
    }
  };

  const handleRoleChange = (roleId) => {
    setActiveRole(roleId);
    setErrors({});
    setTouched({});
  };

  const validateAll = () => {
    const errs = {};
    const fnErr = validateName(formData.firstName, 'First name');
    if (fnErr) errs.firstName = fnErr;
    const lnErr = validateName(formData.lastName, 'Last name');
    if (lnErr) errs.lastName = lnErr;
    const emErr = validateEmail(formData.workEmail);
    if (emErr) errs.workEmail = emErr;
    else if (emailCheckStatus.available === false) errs.workEmail = emailCheckStatus.message || 'This email address is already registered.';
    
    const phErr = validateIndianPhone(formData.phone);
    if (phErr) errs.phone = phErr;
    const pwErr = validatePassword(formData.password);
    if (pwErr) errs.password = pwErr;
    const cpErr = validateSingleField('confirmPassword', formData.confirmPassword, formData, activeRole);
    if (cpErr) errs.confirmPassword = cpErr;

    if (activeRole === 'patient') {
      const dobErr = validateSingleField('dob', formData.dob, formData, activeRole);
      if (dobErr) errs.dob = dobErr;
    } else if (activeRole === 'doctor') {
      const regNum = (formData.medicalRegistrationNumber || formData.npi || '').trim();
      if (!regNum) {
        errs.medicalRegistrationNumber = 'Medical registration number is required.';
      } else if (regNum.length < 3) {
        errs.medicalRegistrationNumber = 'Valid registration number required (min 3 chars).';
      }
      if (!formData.stateMedicalCouncil) {
        errs.stateMedicalCouncil = 'Select your medical council.';
      }
      if (!formData.registrationYear || isNaN(formData.registrationYear)) {
        errs.registrationYear = 'Registration year is required.';
      } else {
        const y = parseInt(formData.registrationYear, 10);
        const currY = new Date().getFullYear();
        if (y < 1950 || y > currY) {
          errs.registrationYear = `Registration year must be between 1950 and ${currY}.`;
        }
      }
      if (!formData.qualification.trim()) {
        errs.qualification = 'Primary qualification is required (e.g. MBBS).';
      }
      if (!formData.specialization) {
        errs.specialization = 'Clinical specialization is required.';
      }
      if (formData.experience === '' || formData.experience === null || isNaN(formData.experience) || parseInt(formData.experience, 10) < 0) {
        errs.experience = 'Years of experience is required (>= 0).';
      }
    } else if (activeRole === 'caregiver') {
      if (formData.caregiverType === 'PROFESSIONAL') {
        const ag = (formData.agencyId || '').trim();
        if (!ag) {
          errs.agencyId = 'Agency Certificate ID is required (e.g. CG-204).';
        }
      }
    } else if (activeRole === 'family') {
      const pat = (formData.patientId || '').trim();
      if (!pat) {
        errs.patientId = 'Patient Access Code is required (e.g. P-102).';
      }
    }

    return errs;
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    // Mark all fields touched
    const allTouched = {
      firstName: true,
      lastName: true,
      workEmail: true,
      phone: true,
      password: true,
      confirmPassword: true,
      dob: true,
      medicalRegistrationNumber: true,
      stateMedicalCouncil: true,
      registrationYear: true,
      qualification: true,
      specialization: true,
      experience: true,
      agencyId: true,
      patientId: true
    };
    setTouched(allTouched);

    const errs = validateAll();
    if (Object.keys(errs).length) {
      setErrors(errs);
      const firstErrMsg = Object.values(errs)[0];
      if (firstErrMsg) {
        addToast(firstErrMsg, 'error');
      }
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        fullName: `${formData.firstName.trim()} ${formData.lastName.trim()}`,
        email: formData.workEmail.trim(),
        phone: formData.phone.trim(),
        password: formData.password,
        dob: formData.dob || undefined,
        role: activeRole,
        npi: activeRole === 'doctor' ? (formData.medicalRegistrationNumber || formData.npi) : '',
        deviceId: activeRole === 'patient' ? formData.deviceId : '',
        agencyId: activeRole === 'caregiver' ? formData.agencyId : '',
        patientId: activeRole === 'family' ? formData.patientId : '',
        medicalRegistrationNumber: activeRole === 'doctor' ? (formData.medicalRegistrationNumber || formData.npi) : '',
        stateMedicalCouncil: activeRole === 'doctor' ? formData.stateMedicalCouncil : '',
        registrationYear: activeRole === 'doctor' ? formData.registrationYear : '',
        qualification: activeRole === 'doctor' ? formData.qualification : '',
        additionalQualifications: activeRole === 'doctor' ? formData.additionalQualifications : '',
        hprId: activeRole === 'doctor' ? formData.hprId : '',
        facilityId: activeRole === 'doctor' ? formData.facilityId : '',
        organization: activeRole === 'doctor' ? formData.organization : '',
        department: activeRole === 'doctor' ? formData.department : '',
        designation: activeRole === 'doctor' ? formData.designation : '',
        specialization: activeRole === 'doctor' ? formData.specialization : '',
        experience: activeRole === 'doctor' ? formData.experience : '',
        bio: activeRole === 'doctor' ? formData.bio : '',
        caregiverType: activeRole === 'caregiver' ? formData.caregiverType : '',
        skills: activeRole === 'caregiver' ? formData.skills : '',
        previousExperience: activeRole === 'caregiver' ? formData.previousExperience : '',
        currentAgency: activeRole === 'caregiver' ? formData.currentAgency : '',
        agencyContact: activeRole === 'caregiver' ? formData.agencyContact : ''
      };
      const result = await register(payload);
      if (result && result.isPendingApproval) {
        setStatusModal({
          isOpen: true,
          title: result.title || 'Professional Verification Result',
          statusLabel: result.status_label || result.statusLabel || '',
          message: result.message || 'Your application has been submitted for administrator review.',
          status: result.status || 'PENDING',
          category: result.category || '',
          breakdown: result.breakdown || null
        });
      } else {
        addToast('Portal account created successfully!', 'success');
        navigate('/dashboard');
      }
    } catch (err) {
      const bErrors = err.errors || (err.payload && err.payload.errors) || {};
      const newErrors = {};
      if (bErrors.email) newErrors.workEmail = Array.isArray(bErrors.email) ? bErrors.email[0] : bErrors.email;
      if (bErrors.phone) newErrors.phone = Array.isArray(bErrors.phone) ? bErrors.phone[0] : bErrors.phone;
      if (bErrors.fullName) newErrors.firstName = Array.isArray(bErrors.fullName) ? bErrors.fullName[0] : bErrors.fullName;
      if (bErrors.password) newErrors.password = Array.isArray(bErrors.password) ? bErrors.password[0] : bErrors.password;
      if (bErrors.medicalRegistrationNumber) newErrors.medicalRegistrationNumber = Array.isArray(bErrors.medicalRegistrationNumber) ? bErrors.medicalRegistrationNumber[0] : bErrors.medicalRegistrationNumber;
      if (bErrors.stateMedicalCouncil) newErrors.stateMedicalCouncil = Array.isArray(bErrors.stateMedicalCouncil) ? bErrors.stateMedicalCouncil[0] : bErrors.stateMedicalCouncil;
      if (bErrors.registrationYear) newErrors.registrationYear = Array.isArray(bErrors.registrationYear) ? bErrors.registrationYear[0] : bErrors.registrationYear;
      if (bErrors.qualification) newErrors.qualification = Array.isArray(bErrors.qualification) ? bErrors.qualification[0] : bErrors.qualification;
      if (bErrors.specialization) newErrors.specialization = Array.isArray(bErrors.specialization) ? bErrors.specialization[0] : bErrors.specialization;
      if (bErrors.experience) newErrors.experience = Array.isArray(bErrors.experience) ? bErrors.experience[0] : bErrors.experience;
      if (bErrors.patientId) newErrors.patientId = Array.isArray(bErrors.patientId) ? bErrors.patientId[0] : bErrors.patientId;
      if (bErrors.agencyId) newErrors.agencyId = Array.isArray(bErrors.agencyId) ? bErrors.agencyId[0] : bErrors.agencyId;
      if (bErrors.dob) newErrors.dob = Array.isArray(bErrors.dob) ? bErrors.dob[0] : bErrors.dob;

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
      } else {
        setErrors({ form: err.message || 'Registration failed' });
      }
      addToast(err.message || 'Registration failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpChange = (value, idx) => {
    if (value.length > 1) return;
    const next = [...otpDigits];
    next[idx] = value;
    setOtpDigits(next);
    if (value && idx < 5) {
      const nextInput = document.getElementById(`otp-${idx + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleOtpKeyDown = (e, idx) => {
    if (e.key === 'Backspace' && !otpDigits[idx] && idx > 0) {
      const prevInput = document.getElementById(`otp-${idx - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleVerify = async () => {
    setIsLoading(true);
    try {
      const payload = {
        fullName: `${formData.firstName} ${formData.lastName}`,
        email: formData.workEmail,
        phone: formData.phone,
        role: activeRole,
        npi: activeRole === 'doctor' ? formData.npi : '',
        deviceId: activeRole === 'patient' ? formData.deviceId : '',
        agencyId: activeRole === 'caregiver' ? formData.agencyId : '',
        patientId: activeRole === 'family' ? formData.patientId : '',
        specialization: activeRole === 'doctor' ? formData.specialization : '',
        experience: activeRole === 'doctor' ? formData.experience : '',
        bio: activeRole === 'doctor' ? formData.bio : ''
      };
      const result = await register(payload);
      if (result && (result.isPendingApproval || result.approved === false)) {
        setStatusModal({
          isOpen: true,
          title: result.title || 'Professional Verification Result',
          statusLabel: result.status_label || result.statusLabel || '',
          message: result.message || 'Your application has been submitted for administrator review.',
          status: result.status || 'PENDING',
          category: result.category || '',
          breakdown: result.breakdown || null
        });
      } else {
        addToast('Portal account created successfully!', 'success');
        navigate('/dashboard');
      }
    } catch (err) {
      setErrors({ form: err.message || 'Registration failed' });
      addToast(err.message || 'Verification failed', 'error');
      setView('register');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-50 dark:bg-slate-900 font-sans" style={{ fontFamily: "'Inter', sans-serif" }}>
      <LeftPanel />

      {/* Right Form Panel */}
      <div className="flex flex-col items-center justify-center p-4 sm:p-10 md:p-16 min-h-screen overflow-y-auto">
        <div className="w-full max-w-lg py-8 sm:py-0">
          
          {/* Main Card container */}
          <div className="bg-white dark:bg-slate-955 border border-slate-200/80 dark:border-slate-850 p-6 sm:p-10 rounded-[28px] shadow-[0_20px_50px_rgba(0,0,0,0.03)] w-full space-y-6 animate-scale-in">
            
            {/* Mobile Logo */}
            <div className="flex lg:hidden items-center justify-center gap-2 mb-2">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-blue-50 dark:bg-blue-955/30 border border-blue-150 dark:border-blue-900/50">
                <Heart className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="font-black text-slate-900 dark:text-slate-100 text-[15px] tracking-tight">NeuroCare Nexus</span>
            </div>

            {/* REGISTER FORM VIEW OR VERIFICATION STATUS OVERLAY */}
            {isLoading && verificationStep !== 'idle' ? (
              <div className="py-10 text-center space-y-6 animate-scale-in">
                <div className="relative w-16 h-16 mx-auto">
                  <span className="absolute -inset-3.5 rounded-full bg-blue-500/10 border border-blue-500/20 animate-ping pointer-events-none" />
                  <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-955 border border-blue-150 dark:border-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400">
                    <ShieldCheck className="w-8 h-8 animate-pulse" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-black text-slate-900 dark:text-slate-100">
                    {verificationStep === 'checking_registry' && 'Querying NMC Medical Registry'}
                    {verificationStep === 'identity_proofing' && 'Verifying Clinical Affiliation'}
                    {verificationStep === 'complete' && 'Registration Verified'}
                  </h3>
                  <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
                    {verificationLabel || 'Establishing secure, encrypted connection to National Health Authority (ABDM) registry...'}
                  </p>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden max-w-xs mx-auto">
                  <div 
                    className="h-full bg-blue-600 rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: verificationStep === 'checking_registry' ? '45%' : verificationStep === 'identity_proofing' ? '80%' : '100%'
                    }}
                  />
                </div>
              </div>
            ) : view === 'register' ? (
              <div className="space-y-6">
                
                {/* Heading */}
                <div className="text-left space-y-1">
                  <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight leading-none">Register Portal Account</h1>
                  <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Configure secure credentials and clinical link keys</p>
                </div>

                {/* Segmented selector tabs */}
                <div className="grid grid-cols-4 gap-1.5 p-1.5 bg-slate-100 dark:bg-slate-900 rounded-2xl select-none border border-slate-200/30 dark:border-slate-800">
                  {[
                    { id: 'patient', label: 'Patient', icon: Heart },
                    { id: 'caregiver', label: 'Caregiver', icon: Pill },
                    { id: 'family', label: 'Family', icon: Key },
                    { id: 'doctor', label: 'Doctor', icon: Stethoscope }
                  ].map(role => {
                    const Icon = role.icon;
                    const isSelected = activeRole === role.id;
                    const isPatient = role.id === 'patient';
                    return (
                      <button
                        key={role.id}
                        type="button"
                        onClick={() => handleRoleChange(role.id)}
                        className={`py-2.5 flex flex-col items-center justify-center text-[10px] font-black uppercase tracking-wider rounded-xl cursor-pointer transition-all duration-205 border-none relative ${
                          isSelected 
                            ? (isPatient 
                                ? 'bg-blue-600 text-white shadow-md scale-[1.04] border border-blue-500' 
                                : 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-md scale-[1.02]') 
                            : (isPatient 
                                ? 'text-blue-605 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-950/15 border border-blue-200/40 dark:border-blue-900/20' 
                                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-350 bg-transparent')
                        }`}
                      >
                        <Icon className="w-4 h-4 mb-1 shrink-0" />
                        {role.label}
                      </button>
                    );
                  })}
                </div>

                <form onSubmit={handleRegister} className="space-y-4">
                  {/* Name grid */}
                  <div className="grid grid-cols-2 gap-3.5">
                    <div>
                      <AuthInput 
                        label="First Name" 
                        name="firstName" 
                        placeholder="Sarah" 
                        icon={User}
                        value={formData.firstName} 
                        onChange={handleChange}
                        onBlur={handleBlur}
                        error={errors.firstName}
                        success={formData.firstName && !errors.firstName ? 'Valid' : null}
                        isTouched={touched.firstName}
                      />
                    </div>
                    <div>
                      <AuthInput 
                        label="Last Name" 
                        name="lastName" 
                        placeholder="Johnson" 
                        icon={User}
                        value={formData.lastName} 
                        onChange={handleChange}
                        onBlur={handleBlur}
                        error={errors.lastName}
                        success={formData.lastName && !errors.lastName ? 'Valid' : null}
                        isTouched={touched.lastName}
                      />
                    </div>
                  </div>

                  <div>
                    <AuthInput 
                      label="Email Address" 
                      type="email" 
                      name="workEmail" 
                      placeholder="you@hospital.com"
                      icon={Mail} 
                      value={formData.workEmail} 
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={errors.workEmail}
                      success={
                        emailCheckStatus.checking
                          ? 'Checking...'
                          : emailCheckStatus.available === true && !errors.workEmail
                          ? 'Email available'
                          : formData.workEmail && !errors.workEmail
                          ? 'Valid format'
                          : null
                      }
                      isTouched={touched.workEmail}
                    />
                  </div>

                  {/* Role Specific Credentials */}
                  {activeRole === 'doctor' && (
                    <div className="space-y-4">
                      {/* Section 1: Verification Credentials */}
                      <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200/80 dark:border-slate-800 space-y-3.5 text-left">
                        <div className="flex items-center gap-2 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
                          <Stethoscope className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                          <h3 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200">Medical Registration Credentials</h3>
                        </div>
                        <div>
                          <AuthInput 
                            label="Medical Registration Number" 
                            name="medicalRegistrationNumber" 
                            placeholder="e.g. SYN-KER-MED-000001 or 1029384756"
                            icon={Stethoscope} 
                            value={formData.medicalRegistrationNumber} 
                            onChange={handleChange}
                            onBlur={handleBlur}
                            error={errors.medicalRegistrationNumber}
                            success={formData.medicalRegistrationNumber && !errors.medicalRegistrationNumber ? 'Format valid' : null}
                            isTouched={touched.medicalRegistrationNumber}
                          />
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1.5 text-left w-full">
                            <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">State Medical Council</label>
                            <select
                              name="stateMedicalCouncil"
                              value={formData.stateMedicalCouncil}
                              onChange={handleChange}
                              onBlur={handleBlur}
                              className={`w-full py-3 px-4 border rounded-xl bg-white dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm ${
                                touched.stateMedicalCouncil && errors.stateMedicalCouncil 
                                  ? 'border-red-500 focus:border-red-500 ring-4 ring-red-500/10' 
                                  : touched.stateMedicalCouncil && formData.stateMedicalCouncil
                                  ? 'border-emerald-500/80 dark:border-emerald-600/80'
                                  : 'border-slate-200 dark:border-slate-800'
                              }`}
                            >
                              <option value="">Select State Medical Council...</option>
                              <option value="Delhi Medical Council">Delhi Medical Council</option>
                              <option value="Karnataka Medical Council">Karnataka Medical Council</option>
                              <option value="Maharashtra Medical Council">Maharashtra Medical Council</option>
                              <option value="Tamil Nadu Medical Council">Tamil Nadu Medical Council</option>
                              <option value="Telangana State Medical Council">Telangana State Medical Council</option>
                              <option value="Kerala Medical Council">Kerala Medical Council</option>
                              <option value="Gujarat Medical Council">Gujarat Medical Council</option>
                              <option value="Uttar Pradesh Medical Council">Uttar Pradesh Medical Council</option>
                              <option value="West Bengal Medical Council">West Bengal Medical Council</option>
                            </select>
                            {touched.stateMedicalCouncil && errors.stateMedicalCouncil && (
                              <span className="text-[10px] font-bold text-red-500 pl-1 animate-fade-in flex items-center gap-1">
                                ✕ {errors.stateMedicalCouncil}
                              </span>
                            )}
                          </div>
                          <div>
                            <AuthInput 
                              label="Year of Registration" 
                              type="number" 
                              name="registrationYear" 
                              placeholder="e.g. 2015"
                              icon={Sparkles} 
                              value={formData.registrationYear} 
                              onChange={handleChange}
                              onBlur={handleBlur}
                              min="1950" 
                              max="2026" 
                              error={errors.registrationYear}
                              success={formData.registrationYear && !errors.registrationYear ? 'Valid year' : null}
                              isTouched={touched.registrationYear}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Section 2: Clinical Qualifications */}
                      <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200/80 dark:border-slate-800 space-y-3.5 text-left">
                        <div className="flex items-center gap-2 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
                          <User className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                          <h3 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200">Qualifications & Specialization</h3>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <AuthInput 
                              label="Qualification" 
                              name="qualification" 
                              placeholder="e.g. MBBS, MD"
                              icon={User} 
                              value={formData.qualification} 
                              onChange={handleChange}
                              onBlur={handleBlur}
                              error={errors.qualification}
                              success={formData.qualification && !errors.qualification ? 'Valid' : null}
                              isTouched={touched.qualification}
                            />
                          </div>
                          <div>
                            <AuthInput 
                              label="Additional Qualification (Optional)" 
                              name="additionalQualifications" 
                              placeholder="e.g. DNB, DM, Fellowship"
                              icon={User} 
                              value={formData.additionalQualifications} 
                              onChange={handleChange} 
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1.5 text-left w-full">
                            <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Clinical Specialization</label>
                            <select
                              name="specialization"
                              value={formData.specialization}
                              onChange={handleChange}
                              onBlur={handleBlur}
                              className={`w-full py-3 px-4 border rounded-xl bg-white dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm ${
                                touched.specialization && errors.specialization 
                                  ? 'border-red-500 focus:border-red-500 ring-4 ring-red-500/10' 
                                  : touched.specialization && formData.specialization
                                  ? 'border-emerald-500/80 dark:border-emerald-600/80'
                                  : 'border-slate-200 dark:border-slate-800'
                              }`}
                            >
                              <option value="">Select Specialization...</option>
                              <option value="General Medicine">General Medicine</option>
                              <option value="General Surgery">General Surgery</option>
                              <option value="Cardiology">Cardiology</option>
                              <option value="Neurology">Neurology</option>
                              <option value="Neurosurgery">Neurosurgery</option>
                              <option value="Orthopedics">Orthopedics</option>
                              <option value="Pediatrics">Pediatrics</option>
                              <option value="Pulmonology">Pulmonology</option>
                              <option value="Dermatology">Dermatology</option>
                              <option value="Other">Other</option>
                            </select>
                            {touched.specialization && errors.specialization && (
                              <span className="text-[10px] font-bold text-red-500 pl-1 animate-fade-in flex items-center gap-1">
                                ✕ {errors.specialization}
                              </span>
                            )}
                          </div>
                          <div>
                            <AuthInput 
                              label="Years of Experience" 
                              type="number" 
                              name="experience" 
                              placeholder="e.g. 8"
                              icon={Sparkles} 
                              value={formData.experience} 
                              onChange={handleChange}
                              onBlur={handleBlur}
                              min="0" 
                              error={errors.experience}
                              success={formData.experience !== '' && !errors.experience ? 'Valid' : null}
                              isTouched={touched.experience}
                            />
                          </div>
                        </div>
                        <div>
                          <AuthInput 
                            label="ABDM HPR ID (Optional)" 
                            name="hprId" 
                            placeholder="e.g. 12-3456-7890-1234"
                            icon={ShieldCheck} 
                            value={formData.hprId} 
                            onChange={handleChange} 
                          />
                        </div>
                        <div className="flex flex-col gap-1.5 text-left w-full group">
                          <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Professional Bio (Optional)</label>
                          <textarea
                            name="bio"
                            placeholder="Describe your clinical focus and practice background..."
                            value={formData.bio}
                            onChange={handleChange}
                            rows="2"
                            className="w-full p-3 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-655 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm resize-none"
                          />
                        </div>
                      </div>

                      {/* Section 3: Facility Affiliations */}
                      <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200/80 dark:border-slate-800 space-y-3.5 text-left">
                        <div className="flex items-center gap-2 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
                          <Hospital className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                          <h3 className="text-xs font-black uppercase tracking-wider text-slate-800 dark:text-slate-200">Facility & Practice Affiliations</h3>
                        </div>
                        <div className="flex flex-col gap-1.5 text-left w-full">
                          <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Primary Health Facility (Optional)</label>
                          <select
                            name="facilityId"
                            value={formData.facilityId}
                            onChange={handleChange}
                            className="w-full py-3 px-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm"
                          >
                            <option value="">Select Primary Health Facility...</option>
                            {facilities.map(f => (
                              <option key={f.id} value={f.id}>{f.name} ({f.city}, {f.state})</option>
                            ))}
                          </select>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <AuthInput 
                              label="Department (Optional)" 
                              name="department" 
                              placeholder="e.g. Cardiology"
                              icon={Hospital} 
                              value={formData.department} 
                              onChange={handleChange} 
                            />
                          </div>
                          <div>
                            <AuthInput 
                              label="Designation (Optional)" 
                              name="designation" 
                              placeholder="e.g. Senior Consultant"
                              icon={User} 
                              value={formData.designation} 
                              onChange={handleChange} 
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeRole === 'patient' && (
                    <div className="space-y-4">
                      <div>
                        <AuthInput 
                          label="Wearable Device Serial Number (Optional)" 
                          name="deviceId" 
                          placeholder="Format: NP-102"
                          icon={Heart} 
                          value={formData.deviceId} 
                          onChange={handleChange} 
                          onBlur={handleBlur}
                          error={errors.deviceId}
                          isTouched={touched.deviceId}
                        />
                      </div>
                      <div>
                        <AuthInput 
                          label="Date of Birth (Optional)" 
                          type="date" 
                          name="dob" 
                          max={new Date().toISOString().split('T')[0]}
                          icon={Calendar} 
                          value={formData.dob} 
                          onChange={handleChange} 
                          onBlur={handleBlur}
                          error={errors.dob}
                          success={formData.dob && !errors.dob ? 'Valid date' : null}
                          isTouched={touched.dob}
                        />
                      </div>
                    </div>
                  )}

                  {activeRole === 'caregiver' && (
                    <>
                      <div className="flex flex-col gap-1.5 text-left w-full">
                        <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Caregiver Category</label>
                        <select
                          name="caregiverType"
                          value={formData.caregiverType}
                          onChange={handleChange}
                          className="w-full py-3 px-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-900/40 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm"
                        >
                          <option value="PROFESSIONAL">Professional / Agency Caregiver</option>
                          <option value="FAMILY">Family / Personal Caregiver</option>
                        </select>
                      </div>
                      {formData.caregiverType === 'PROFESSIONAL' ? (
                        <div>
                          <AuthInput 
                            label="Agency Certificate ID" 
                            name="agencyId" 
                            placeholder="Format: CG-204"
                            icon={Pill} 
                            value={formData.agencyId} 
                            onChange={handleChange}
                            onBlur={handleBlur}
                            error={errors.agencyId}
                            success={formData.agencyId && !errors.agencyId ? 'Format valid' : null}
                            isTouched={touched.agencyId}
                          />
                        </div>
                      ) : (
                        <div className="text-slate-450 dark:text-slate-500 text-[10px] font-bold p-3 bg-blue-50/25 dark:bg-blue-950/5 border border-blue-150/40 dark:border-blue-900/10 rounded-xl text-left leading-relaxed">
                          ℹ Family caregivers do not require agency verification. Links can be created directly by providing the patient access code on your workspace dashboard.
                        </div>
                      )}
                      <div>
                        <AuthInput 
                          label="Caregiver Qualification (Optional)" 
                          name="qualification" 
                          placeholder="e.g. Registered Nurse, CNA, Personal Caretaker"
                          icon={User} 
                          value={formData.qualification} 
                          onChange={handleChange} 
                        />
                      </div>
                      <div>
                        <AuthInput 
                          label="Years of Experience (Optional)" 
                          type="number" 
                          name="experience" 
                          placeholder="e.g. 5"
                          icon={Sparkles} 
                          value={formData.experience} 
                          onChange={handleChange} 
                          min="0" 
                        />
                      </div>
                      <div>
                        <AuthInput 
                          label="Skills / Services Offered (Optional)" 
                          name="skills" 
                          placeholder="e.g. Elder care, Fall assist, Vitals logging"
                          icon={Sparkles} 
                          value={formData.skills} 
                          onChange={handleChange} 
                        />
                      </div>
                      <div>
                        <AuthInput 
                          label="Agency / Organization Name (Optional)" 
                          name="currentAgency" 
                          placeholder="e.g. Beacon Home Health"
                          icon={Hospital} 
                          value={formData.currentAgency} 
                          onChange={handleChange} 
                        />
                      </div>
                    </>
                  )}

                  {activeRole === 'family' && (
                    <div>
                      <AuthInput 
                        label="Authorized Patient Access Code" 
                        name="patientId" 
                        placeholder="Format: P-102"
                        icon={Key} 
                        value={formData.patientId} 
                        onChange={handleChange}
                        onBlur={handleBlur}
                        error={errors.patientId}
                        success={formData.patientId && !errors.patientId ? 'Format valid' : null}
                        isTouched={touched.patientId}
                      />
                    </div>
                  )}

                  <div>
                    <AuthInput 
                      label="Phone Number (India +91)" 
                      type="tel" 
                      name="phone" 
                      placeholder="+91 98765 43210"
                      icon={Smartphone} 
                      value={formData.phone} 
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={errors.phone}
                      success={formData.phone && !errors.phone ? 'Valid Indian mobile' : null}
                      isTouched={touched.phone}
                    />
                  </div>

                  <div>
                    <AuthInput 
                      label="Password" 
                      type="password" 
                      name="password" 
                      placeholder="Min. 8 characters"
                      icon={Lock} 
                      value={formData.password} 
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={errors.password}
                      success={formData.password && !errors.password ? 'Strong password' : null}
                      isTouched={touched.password}
                    />

                    {/* Live Password Requirements Checklist */}
                    {(touched.password || formData.password) && (
                      <div className="mt-2 p-3 bg-slate-50 dark:bg-slate-900/60 rounded-xl border border-slate-200/80 dark:border-slate-800 space-y-1.5 text-left text-xs animate-fade-in">
                        <div className="text-[10px] font-black uppercase tracking-wider text-slate-400 pb-1 border-b border-slate-200/50 dark:border-slate-800">
                          Password Requirements
                        </div>
                        <div className="grid grid-cols-2 gap-1.5 text-[11px] font-semibold">
                          <div className={`flex items-center gap-1.5 ${passwordRules.hasMinLength ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}`}>
                            <span>{passwordRules.hasMinLength ? '✓' : '○'}</span> Min 8 characters
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordRules.hasUpper ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}`}>
                            <span>{passwordRules.hasUpper ? '✓' : '○'}</span> Uppercase letter
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordRules.hasLower ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}`}>
                            <span>{passwordRules.hasLower ? '✓' : '○'}</span> Lowercase letter
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordRules.hasNumber ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}`}>
                            <span>{passwordRules.hasNumber ? '✓' : '○'}</span> Number (0-9)
                          </div>
                          <div className={`flex items-center gap-1.5 col-span-2 ${passwordRules.hasSpecial ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-400'}`}>
                            <span>{passwordRules.hasSpecial ? '✓' : '○'}</span> Special character (!@#$%^&*)
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <AuthInput 
                      label="Confirm Password" 
                      type="password" 
                      name="confirmPassword" 
                      placeholder="Re-enter your password"
                      icon={Lock} 
                      value={formData.confirmPassword} 
                      onChange={handleChange}
                      onBlur={handleBlur}
                      error={errors.confirmPassword}
                      success={formData.confirmPassword && !errors.confirmPassword && formData.confirmPassword === formData.password ? 'Passwords match' : null}
                      isTouched={touched.confirmPassword}
                    />
                  </div>

                  {errors.form && (
                    <p className="text-xs text-red-500 font-bold bg-red-55 dark:bg-red-950/20 p-3 rounded-xl border border-red-900/35 text-left">
                      {errors.form}
                    </p>
                  )}

                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer border-none mt-2 transition-all duration-205 hover:opacity-95 active:scale-[0.99]"
                    style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)', boxShadow: '0 4px 12px rgba(37,99,235,0.25)', opacity: isLoading ? 0.75 : 1 }}
                  >
                    {isLoading && (
                      <span className="w-[18px] h-[18px] border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
                    )}
                    {isLoading ? 'Verifying...' : 'Register Account →'}
                  </button>
                </form>

                <p className="text-center text-xs font-semibold text-slate-500 mt-5 leading-none">
                  Already have a clinical profile?{' '}
                  <Link to="/login" className="text-blue-600 font-black hover:text-blue-755">Sign In</Link>
                </p>
              </div>
            ) : (
              /* OTP VERIFICATION VIEW */
              <div className="text-center space-y-6">
                <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/20 mx-auto flex items-center justify-center text-emerald-600 dark:text-emerald-450 border border-emerald-100 dark:border-emerald-900/50 shadow-sm">
                  <Smartphone className="w-7 h-7" />
                </div>
                <div className="text-center">
                  <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 leading-none">Verify Your Email</h1>
                  <p className="text-xs text-slate-500 mt-2 font-semibold leading-relaxed">
                    A 6-digit confirmation token was dispatched to<br />
                    <strong className="text-slate-900 dark:text-slate-200 font-black">{formData.workEmail || 'your email'}</strong>
                  </p>
                </div>

                {/* OTP digits */}
                <div className="flex gap-2.5 justify-center select-none">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      id={`otp-${idx}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={e => handleOtpChange(e.target.value, idx)}
                      onKeyDown={e => handleOtpKeyDown(e, idx)}
                      className="w-12 h-14 text-center text-xl font-bold border-2 rounded-xl outline-none transition-all duration-200 text-slate-900 dark:text-slate-100 bg-slate-50 dark:bg-slate-900 focus:bg-white dark:focus:bg-slate-950"
                      style={{
                        borderColor: digit ? '#2563EB' : '#E2E8F0',
                        boxShadow: digit ? '0 0 0 3px rgba(37,99,235,0.1)' : 'none'
                      }}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  onClick={handleVerify}
                  disabled={isLoading || otpDigits.some(d => !d)}
                  className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer border-none shadow-md transition-all duration-200 hover:opacity-95"
                  style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)' }}
                >
                  {isLoading ? 'Confirming Token...' : 'Verify Email & Enter Dashboard →'}
                </button>

                <button
                  type="button"
                  onClick={() => addToast('Verification code resent.', 'success')}
                  className="text-xs text-blue-600 dark:text-blue-450 font-black bg-transparent border-none cursor-pointer hover:text-blue-755"
                >
                  Resend token code
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {statusModal.isOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-5 text-center">
            <div className={`w-16 h-16 rounded-2xl mx-auto flex items-center justify-center ${
              statusModal.category === 'MATCH'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 border border-emerald-200 dark:border-emerald-900/50'
                : 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 border border-amber-200 dark:border-amber-900/50'
            }`}>
              {statusModal.category === 'MATCH' ? (
                <CheckCircle2 className="w-8 h-8" />
              ) : (
                <ShieldCheck className="w-8 h-8" />
              )}
            </div>
            
            <div className="space-y-2">
              <span className={`inline-block px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                statusModal.category === 'MATCH'
                  ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                  : 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
              }`}>
                {statusModal.statusLabel || (statusModal.category === 'MATCH' ? '✓ Professional details verified' : '⚠ Administrator Review Required')}
              </span>
              <h2 className="text-xl font-black text-slate-900 dark:text-white">
                {statusModal.title || 'Professional Verification Result'}
              </h2>
              <div className="text-xs text-slate-600 dark:text-slate-300 font-semibold leading-relaxed whitespace-pre-line text-left bg-slate-50/70 dark:bg-slate-950/40 p-3.5 rounded-2xl border border-slate-100 dark:border-slate-850">
                {statusModal.message}
              </div>
            </div>

            {statusModal.breakdown && (
              <div className="bg-slate-50 dark:bg-slate-950/70 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-850 space-y-2 text-left">
                <div className="text-[10px] font-black uppercase tracking-wider text-slate-400 pb-1 border-b border-slate-100 dark:border-slate-850">
                  Verification Status Breakdown
                </div>
                <div className="space-y-1.5">
                  {Object.entries(statusModal.breakdown).map(([label, val]) => {
                    const isSuccess = ['COMPLETED', 'VERIFIED', 'FOUND', 'MATCHED'].includes(val);
                    const isReview = ['REVIEW REQUIRED', 'NOT_FOUND', 'MISMATCH'].includes(val);
                    return (
                      <div key={label} className="flex justify-between items-center text-xs font-semibold">
                        <span className="text-slate-600 dark:text-slate-350">{label}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                          isSuccess
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50'
                            : isReview
                            ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50'
                            : 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-900/50'
                        }`}>
                          {isSuccess ? `✓ ${val}` : isReview ? `⚠ ${val}` : `⏳ ${val}`}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={() => {
                setStatusModal({ isOpen: false, title: '', statusLabel: '', message: '', status: '', category: '', breakdown: null });
                navigate('/login');
              }}
              className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider bg-blue-600 hover:bg-blue-700 transition-all border-none cursor-pointer shadow-md"
            >
              OK / Continue to Login →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegisterPage;
