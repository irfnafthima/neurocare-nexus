import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { Mail, Lock, Stethoscope, Heart, Pill, Key, ShieldCheck, ArrowRight, Hospital, Smartphone, User, Sparkles } from 'lucide-react';
import { syntheticNpis, syntheticDeviceSerials, syntheticCaregivers, syntheticPatients } from '../data/mockData';
import { getApiUrl } from '../services/api';

const AuthInput = ({ label, type = 'text', placeholder, icon: Icon, value, onChange, name, ...rest }) => (
  <div className="flex flex-col gap-1.5 text-left w-full group">
    <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">{label}</label>
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-slate-400 dark:text-slate-550 group-focus-within:text-blue-500 transition-colors duration-200 select-none pointer-events-none" />
      )}
      <input
        type={type}
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoComplete={type === 'password' ? 'new-password' : type === 'email' ? 'email' : 'off'}
        className="w-full py-3 pr-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-900/40 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-655 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm read-only:bg-slate-100 dark:read-only:bg-slate-900/70 read-only:cursor-not-allowed read-only:text-slate-500"
        style={{ paddingLeft: Icon ? '2.75rem' : '1rem' }}
        {...rest}
      />
    </div>
  </div>
);

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

  // Verification step details
  const [verificationStep, setVerificationStep] = useState('idle'); // 'idle' | 'checking_registry' | 'identity_proofing' | 'complete'
  const [verificationLabel, setVerificationLabel] = useState('');

  const [facilities, setFacilities] = useState([]);

  useEffect(() => {
    fetch(getApiUrl('/facilities'))
      .then(res => res.json())
      .then(data => setFacilities(data))
      .catch(err => console.error("Error loading facilities:", err));
  }, []);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    workEmail: '',
    phone: '',
    password: '',
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    let newOrg = formData.organization;

    if (name === 'medicalRegistrationNumber' || name === 'npi') {
      const regVal = value;
      if (/^\d{10}$/.test(regVal)) {
        const matched = syntheticNpis.find(n => n.npi === regVal);
        if (matched) {
          newOrg = matched.hospital;
        } else {
          newOrg = '';
        }
      } else {
        newOrg = '';
      }
    }

    setFormData(prev => ({ 
      ...prev, 
      [name]: value,
      organization: (name === 'medicalRegistrationNumber' || name === 'npi') ? newOrg : prev.organization
    }));
    
    setErrors(prev => ({ 
      ...prev, 
      [name]: '',
      organization: (name === 'medicalRegistrationNumber' || name === 'npi') ? '' : prev.organization
    }));
  };

  const validate = () => {
    const errs = {};
    if (!formData.firstName.trim()) errs.firstName = 'Required';
    if (!formData.lastName.trim()) errs.lastName = 'Required';
    if (!formData.workEmail.includes('@')) errs.workEmail = 'Valid email required';
    if (formData.password.length < 8) errs.password = 'Min. 8 characters';

    if (activeRole === 'doctor') {
      const regNum = formData.medicalRegistrationNumber.trim() || formData.npi.trim();
      if (!regNum) {
        errs.medicalRegistrationNumber = 'Required';
      } else if (regNum.length < 4) {
        errs.medicalRegistrationNumber = 'Valid registration number required';
      }
      
      if (!formData.stateMedicalCouncil) {
        errs.stateMedicalCouncil = 'Required';
      }
      if (!formData.registrationYear || isNaN(formData.registrationYear)) {
        errs.registrationYear = 'Required';
      }
      if (!formData.qualification.trim()) {
        errs.qualification = 'Required';
      }
      if (!formData.specialization) {
        errs.specialization = 'Required';
      }
      if (formData.experience === '' || isNaN(formData.experience) || parseInt(formData.experience, 10) < 0) {
        errs.experience = 'Required (>= 0)';
      }
      if (!formData.facilityId && !formData.organization) {
        errs.facilityId = 'Hospital selection required';
      }
    } else if (activeRole === 'patient') {
      // Device ID optional — auto-assigned by backend if empty
    } else if (activeRole === 'caregiver') {
      if (formData.caregiverType === 'PROFESSIONAL') {
        const ag = formData.agencyId.trim();
        if (!ag) {
          errs.agencyId = 'Agency Certificate ID required (e.g. CG-204)';
        }
      }
    } else if (activeRole === 'family') {
      const pat = formData.patientId.trim();
      if (!pat) {
        errs.patientId = 'Patient access code required (e.g. P-102)';
      }
    }

    return errs;
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setIsLoading(true);
    try {
      const payload = {
        fullName: `${formData.firstName} ${formData.lastName}`,
        email: formData.workEmail,
        phone: formData.phone,
        password: formData.password,
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
        addToast(result.message || 'Verification pending Administrator approval.', 'info');
        navigate('/login');
      } else {
        addToast('Portal account created successfully!', 'success');
        navigate('/dashboard');
      }
    } catch (err) {
      setErrors({ form: err.message || 'Registration failed' });
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
      if (result && result.isPendingApproval) {
        addToast(result.message || 'Verification pending Administrator approval.', 'info');
        navigate('/login');
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
                  <h2 className="text-base font-black text-slate-900 dark:text-slate-100 uppercase tracking-wider leading-none">Security Registry Check</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">{verificationLabel}</p>
                </div>

                <div className="flex flex-col gap-2.5 max-w-xs mx-auto text-left text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${verificationStep === 'checking_registry' ? 'bg-blue-500 animate-pulse' : (verificationStep === 'identity_proofing' || verificationStep === 'complete') ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-800'}`} />
                    <span>NPI Registry / Device MAC validation</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${verificationStep === 'identity_proofing' ? 'bg-blue-500 animate-pulse' : verificationStep === 'complete' ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-800'}`} />
                    <span>ID.me Identity Proofing validation</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${verificationStep === 'complete' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-200 dark:bg-slate-800'}`} />
                    <span>Workspace Access Token issue</span>
                  </div>
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
                        onClick={() => { setActiveRole(role.id); setErrors({}); }}
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
                      <AuthInput label="First Name" name="firstName" placeholder="Sarah" icon={User}
                        value={formData.firstName} onChange={handleChange} />
                      {errors.firstName && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.firstName}</p>}
                    </div>
                    <div>
                      <AuthInput label="Last Name" name="lastName" placeholder="Johnson" icon={User}
                        value={formData.lastName} onChange={handleChange} />
                      {errors.lastName && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.lastName}</p>}
                    </div>
                  </div>

                  <div>
                    <AuthInput label="Email Address" type="email" name="workEmail" placeholder="you@hospital.com"
                      icon={Mail} value={formData.workEmail} onChange={handleChange} />
                    {errors.workEmail && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.workEmail}</p>}
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
                          <AuthInput label="Medical Registration Number" name="medicalRegistrationNumber" placeholder="e.g. SYN-KER-MED-000001 or 1029384756"
                            icon={Stethoscope} value={formData.medicalRegistrationNumber} onChange={handleChange} />
                          {errors.medicalRegistrationNumber && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.medicalRegistrationNumber}</p>}
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1.5 text-left w-full">
                            <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">State Medical Council</label>
                            <select
                              name="stateMedicalCouncil"
                              value={formData.stateMedicalCouncil}
                              onChange={handleChange}
                              className="w-full py-3 px-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm"
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
                            {errors.stateMedicalCouncil && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.stateMedicalCouncil}</p>}
                          </div>
                          <div>
                            <AuthInput label="Year of Registration" type="number" name="registrationYear" placeholder="e.g. 2015"
                              icon={Sparkles} value={formData.registrationYear} onChange={handleChange} min="1950" max="2026" />
                            {errors.registrationYear && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.registrationYear}</p>}
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
                            <AuthInput label="Qualification" name="qualification" placeholder="e.g. MBBS, MD"
                              icon={User} value={formData.qualification} onChange={handleChange} />
                            {errors.qualification && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.qualification}</p>}
                          </div>
                          <div>
                            <AuthInput label="Additional Qualification (Optional)" name="additionalQualifications" placeholder="e.g. DNB, DM, Fellowship"
                              icon={User} value={formData.additionalQualifications} onChange={handleChange} />
                          </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div className="flex flex-col gap-1.5 text-left w-full">
                            <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Clinical Specialization</label>
                            <select
                              name="specialization"
                              value={formData.specialization}
                              onChange={handleChange}
                              className="w-full py-3 px-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm"
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
                            {errors.specialization && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.specialization}</p>}
                          </div>
                          <div>
                            <AuthInput label="Years of Experience" type="number" name="experience" placeholder="e.g. 8"
                              icon={Sparkles} value={formData.experience} onChange={handleChange} min="0" />
                            {errors.experience && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.experience}</p>}
                          </div>
                        </div>
                        <div>
                          <AuthInput label="ABDM HPR ID (Optional)" name="hprId" placeholder="e.g. 12-3456-7890-1234"
                            icon={ShieldCheck} value={formData.hprId} onChange={handleChange} />
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
                          <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-555 pl-1">Primary Health Facility</label>
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
                          {errors.facilityId && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.facilityId}</p>}
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <AuthInput label="Department" name="department" placeholder="e.g. Cardiology"
                              icon={Hospital} value={formData.department} onChange={handleChange} />
                          </div>
                          <div>
                            <AuthInput label="Designation" name="designation" placeholder="e.g. Senior Consultant"
                              icon={User} value={formData.designation} onChange={handleChange} />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeRole === 'patient' && (
                    <div>
                      <AuthInput label="Wearable Device Serial Number" name="deviceId" placeholder="Format: NP-102"
                        icon={Heart} value={formData.deviceId} onChange={handleChange} />
                      {errors.deviceId && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.deviceId}</p>}
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
                          <AuthInput label="Agency Certificate ID" name="agencyId" placeholder="Format: CG-204"
                            icon={Pill} value={formData.agencyId} onChange={handleChange} />
                          {errors.agencyId && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.agencyId}</p>}
                        </div>
                      ) : (
                        <div className="text-slate-450 dark:text-slate-500 text-[10px] font-bold p-3 bg-blue-50/25 dark:bg-blue-950/5 border border-blue-150/40 dark:border-blue-900/10 rounded-xl text-left leading-relaxed">
                          ℹ Family caregivers do not require agency verification. Links can be created directly by providing the patient access code on your workspace dashboard.
                        </div>
                      )}
                      <div>
                        <AuthInput label="Caregiver Qualification" name="qualification" placeholder="e.g. Registered Nurse, CNA, Personal Caretaker"
                          icon={User} value={formData.qualification} onChange={handleChange} />
                      </div>
                      <div>
                        <AuthInput label="Years of Experience" type="number" name="experience" placeholder="e.g. 5"
                          icon={Sparkles} value={formData.experience} onChange={handleChange} min="0" />
                      </div>
                      <div>
                        <AuthInput label="Skills / Services Offered" name="skills" placeholder="e.g. Elder care, Fall assist, Vitals logging"
                          icon={Sparkles} value={formData.skills} onChange={handleChange} />
                      </div>
                      <div>
                        <AuthInput label="Agency / Organization Name (Optional)" name="currentAgency" placeholder="e.g. Beacon Home Health"
                          icon={Hospital} value={formData.currentAgency} onChange={handleChange} />
                      </div>
                    </>
                  )}

                  {activeRole === 'family' && (
                    <div>
                      <AuthInput label="Authorized Patient Access Code" name="patientId" placeholder="Format: P-102"
                        icon={Key} value={formData.patientId} onChange={handleChange} />
                      {errors.patientId && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.patientId}</p>}
                    </div>
                  )}

                  <AuthInput label="Phone Number (India +91)" type="tel" name="phone" placeholder="+91 98765 43210"
                    icon={Smartphone} value={formData.phone} onChange={handleChange} />

                  <div>
                    <AuthInput label="Password" type="password" name="password" placeholder="Min. 8 characters"
                      icon={Lock} value={formData.password} onChange={handleChange} />
                    {errors.password && <p className="text-[10px] text-red-500 text-left mt-1 font-black uppercase pl-1">{errors.password}</p>}
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
                  onClick={handleVerify} 
                  disabled={isLoading}
                  className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer border-none mb-4 transition-all duration-200 hover:opacity-95"
                  style={{ background: 'linear-gradient(135deg, #10B981, #059669)', boxShadow: '0 4px 16px rgba(16,185,129,0.25)', opacity: isLoading ? 0.75 : 1 }}
                >
                  {isLoading && (
                    <span className="w-[18px] h-[18px] border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
                  )}
                  {isLoading ? 'Verifying Link...' : '✓ Verify & Complete Register'}
                </button>

                <button 
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
    </div>
  );
};

export default RegisterPage;
