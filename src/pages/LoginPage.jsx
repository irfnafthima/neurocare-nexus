import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { Mail, Lock, Stethoscope, Heart, Pill, Key, ShieldCheck, ArrowLeft, HeartPulse, Sparkles } from 'lucide-react';

const AuthInput = ({ label, type = 'text', placeholder, icon: Icon, value, onChange, name }) => (
  <div className="flex flex-col gap-1.5 text-left w-full group">
    <label className="text-[11px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 pl-1">{label}</label>
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-slate-400 dark:text-slate-550 group-focus-within:text-blue-500 transition-colors duration-250 select-none pointer-events-none" />
      )}
      <input
        type={type}
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoComplete={type === 'password' ? 'current-password' : type === 'email' ? 'email' : 'off'}
        className="w-full py-3 pr-4 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50 dark:bg-slate-900/40 focus:bg-white dark:focus:bg-slate-950 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-650 outline-none focus:border-blue-500 dark:focus:border-blue-700 focus:ring-4 focus:ring-blue-500/10 dark:focus:ring-blue-950/20 transition-all font-semibold shadow-sm"
        style={{ paddingLeft: Icon ? '2.75rem' : '1rem' }}
      />
    </div>
  </div>
);

const LeftPanel = () => {
  return (
    <div className="hidden lg:flex flex-col justify-between p-12 relative overflow-hidden bg-slate-950 text-white select-none">
      {/* Background illustration with professional contrast */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-30 mix-blend-luminosity pointer-events-none filter brightness-95"
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
          <HeartPulse className="w-5.5 h-5.5 text-white" />
        </div>
        <div className="text-left">
          <div className="text-white font-extrabold text-[15px] tracking-tight leading-none">NeuroCare Nexus</div>
          <div className="text-[9px] text-blue-400 font-extrabold tracking-widest uppercase mt-1 leading-none">Clinical Intelligence</div>
        </div>
      </div>

      {/* Empathetic slogan banner */}
      <div className="relative z-10 space-y-6 text-left max-w-sm mt-auto mb-8 animate-fade-in-up">
        <div>
          <span className="px-3 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-400 text-[10px] font-black uppercase tracking-wider block w-fit mb-4">
            Authorized Platform
          </span>
          <h2 className="text-4xl font-black text-white leading-tight tracking-tight mb-3">
            We are with you always.
          </h2>
          <p className="text-slate-350 text-xs font-semibold leading-relaxed">
            Unifying clinical precision with human care. Real-time diagnostics streams from MAX30102, DS18B20, and MPU6050 nodes.
          </p>
        </div>

        {/* Feature stats card */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <div className="bg-white/5 border border-white/10 rounded-xl p-3 backdrop-blur-md">
            <span className="text-lg font-black text-emerald-400">99.9%</span>
            <div className="text-[9px] text-slate-400 font-black mt-0.5 uppercase tracking-wider">Device Uptime</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-3 backdrop-blur-md">
            <span className="text-lg font-black text-blue-400">&lt; 1s</span>
            <div className="text-[9px] text-slate-400 font-black mt-0.5 uppercase tracking-wider">Alert Latency</div>
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

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { addToast } = useToast();

  const [activeRole, setActiveRole] = useState('patient'); // 'doctor' | 'patient' | 'caregiver' | 'family' | 'admin'
  const [view, setView] = useState('login'); // 'login' | 'forgot'
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false,
    npi: '',
    deviceId: '',
    agencyId: '',
    patientId: '',
    accessKey: ''
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      setError('Please fill in email and password.');
      return;
    }

    let credentials = {};
    if (activeRole === 'doctor') {
      if (!/^\d{10}$/.test(formData.npi)) {
        setError('Doctor login requires a valid 10-digit NPI License.');
        return;
      }
      credentials = { npi: formData.npi };
    } else if (activeRole === 'patient') {
      const dev = formData.deviceId.trim().toUpperCase();
      if (!/^NP-\d{3,5}$/.test(dev)) {
        setError('Patient login requires a Device Serial Number formatted as: NP-XXX.');
        return;
      }
      credentials = { deviceId: dev };
    } else if (activeRole === 'caregiver') {
      const ag = formData.agencyId.trim().toUpperCase();
      if (!/^CG-\d{3,5}$/.test(ag)) {
        setError('Caregiver login requires an Agency Certificate formatted as: CG-XXX.');
        return;
      }
      credentials = { agencyId: ag };
    } else if (activeRole === 'family') {
      const pat = formData.patientId.trim().toUpperCase();
      if (!/^P-\d{3,5}$/.test(pat)) {
        setError('Family login requires a Patient Access Code formatted as: P-XXX.');
        return;
      }
      credentials = { patientId: pat };
    } else if (activeRole === 'admin') {
      const key = formData.accessKey.trim().toUpperCase();
      if (!/^ADM-\d{4,6}$/.test(key)) {
        setError('Administrator login requires a System Access Key formatted as: ADM-XXXX.');
        return;
      }
      credentials = { accessKey: key };
    }

    setIsLoading(true);
    try {
      await login(formData.email, formData.password, activeRole, credentials);
      addToast('Welcome to the dashboard!', 'success');
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your credentials.');
      addToast(err.message || 'Login failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-50 dark:bg-slate-900 font-sans" style={{ fontFamily: "'Inter', sans-serif" }}>
      <LeftPanel />

      {/* Right form container wrapper */}
      <div className="flex flex-col items-center justify-center p-4 sm:p-10 md:p-16 min-h-screen overflow-y-auto">
        <div className="w-full max-w-lg py-8 sm:py-0">
          
          {/* Main Card Wrapper */}
          <div className="bg-white dark:bg-slate-950 border border-slate-200/80 dark:border-slate-850 p-6 sm:p-10 rounded-[28px] shadow-[0_20px_50px_rgba(0,0,0,0.03)] w-full space-y-6 animate-scale-in">
            
            {/* Mobile Branding Logo */}
            <div className="flex lg:hidden items-center justify-center gap-2.5 mb-2">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-blue-50 dark:bg-blue-950/30 border border-blue-150 dark:border-blue-900/50">
                <HeartPulse className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="font-black text-slate-900 dark:text-slate-100 text-[15px] tracking-tight">NeuroCare Nexus</span>
            </div>

            {view === 'login' && (
              <div className="space-y-6">
                
                {/* Heading details */}
                <div className="text-left space-y-1">
                  {activeRole === 'admin' ? (
                    <>
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 dark:bg-red-950/30 border border-red-100 dark:border-red-900/30 text-red-650 dark:text-red-400 text-[10px] font-black uppercase tracking-wider mb-2 select-none animate-pulse">
                        <Sparkles className="w-3 h-3" /> restricted administrative gate
                      </div>
                      <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight leading-none">System Admin Access</h1>
                    </>
                  ) : (
                    <>
                      <h1 className="text-2xl font-black text-slate-950 dark:text-slate-50 tracking-tight leading-none">Clinical Portal Access</h1>
                      <p className="text-xs font-semibold text-slate-400 dark:text-slate-500">Sign in to monitor active patient biometrics</p>
                    </>
                  )}
                </div>

                {/* Segmented Selector widget (standard roles only) */}
                {activeRole !== 'admin' && (
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
                          onClick={() => { setActiveRole(role.id); setError(''); }}
                          className={`py-2.5 flex flex-col items-center justify-center text-[10px] font-black uppercase tracking-wider rounded-xl cursor-pointer transition-all duration-200 border-none relative ${
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
                )}

                <form onSubmit={handleLogin} className="space-y-4">
                  <AuthInput 
                    label="Secure Email Address" 
                    type="email" 
                    name="email" 
                    placeholder={activeRole === 'admin' ? 'admin@nexus.com' : 'you@hospital.com'}
                    icon={Mail} 
                    value={formData.email} 
                    onChange={handleChange} 
                  />

                  <AuthInput 
                    label="Password" 
                    type="password" 
                    name="password" 
                    placeholder="••••••••"
                    icon={Lock} 
                    value={formData.password} 
                    onChange={handleChange} 
                  />

                  {/* Role Specific Credentials */}
                  {activeRole === 'doctor' && (
                    <AuthInput 
                      label="National Provider Identifier (NPI)" 
                      name="npi" 
                      placeholder="10-digit NPI license number"
                      icon={Stethoscope} 
                      value={formData.npi} 
                      onChange={handleChange} 
                    />
                  )}

                  {activeRole === 'patient' && (
                    <AuthInput 
                      label="ESP32 Device Serial Number" 
                      name="deviceId" 
                      placeholder="Format: NP-102"
                      icon={Heart} 
                      value={formData.deviceId} 
                      onChange={handleChange} 
                    />
                  )}

                  {activeRole === 'caregiver' && (
                    <AuthInput 
                      label="Agency Certificate ID" 
                      name="agencyId" 
                      placeholder="Format: CG-204"
                      icon={Pill} 
                      value={formData.agencyId} 
                      onChange={handleChange} 
                    />
                  )}

                  {activeRole === 'family' && (
                    <AuthInput 
                      label="Patient Access Code" 
                      name="patientId" 
                      placeholder="Format: P-102"
                      icon={Key} 
                      value={formData.patientId} 
                      onChange={handleChange} 
                    />
                  )}

                  {activeRole === 'admin' && (
                    <AuthInput 
                      label="System Access Key" 
                      name="accessKey" 
                      placeholder="Format: ADM-90210"
                      icon={ShieldCheck} 
                      value={formData.accessKey} 
                      onChange={handleChange} 
                    />
                  )}

                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 cursor-pointer select-none">
                      <input 
                        type="checkbox" 
                        name="remember" 
                        checked={formData.remember} 
                        onChange={handleChange}
                        className="w-4 h-4 rounded border-slate-200 dark:border-slate-800 accent-blue-600 cursor-pointer" 
                      />
                      Remember session
                    </label>
                    <button 
                      type="button" 
                      onClick={() => setView('forgot')}
                      className="text-xs font-bold text-blue-600 hover:text-blue-750 bg-transparent border-none cursor-pointer p-0"
                    >
                      Forgot credentials?
                    </button>
                  </div>

                  {error && (
                    <p className="text-xs text-red-500 font-bold bg-red-50 dark:bg-red-950/20 p-3 rounded-xl border border-red-100 dark:border-red-900/30 text-left">
                      {error}
                    </p>
                  )}

                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 cursor-pointer border-none mt-1 transition-all duration-200 hover:opacity-95 active:scale-[0.99]"
                    style={{ 
                      background: activeRole === 'admin' 
                        ? 'linear-gradient(135deg, #DC2626, #991B1B)' 
                        : 'linear-gradient(135deg, #2563EB, #1D4ED8)', 
                      boxShadow: activeRole === 'admin'
                        ? '0 4px 12px rgba(220,38,38,0.2)'
                        : '0 4px 12px rgba(37,99,235,0.25)', 
                      opacity: isLoading ? 0.75 : 1 
                    }}
                  >
                    {isLoading && (
                      <span className="w-[18px] h-[18px] border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
                    )}
                    {isLoading ? 'Authenticating...' : activeRole === 'admin' ? 'Verify Root Access Key' : 'Access Secure Portal'}
                  </button>
                </form>

                {activeRole !== 'admin' ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center">
                      <button 
                        type="button" 
                        onClick={() => { setActiveRole('admin'); setError(''); }} 
                        className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-400 hover:text-slate-700 dark:hover:text-slate-350 bg-transparent border-none cursor-pointer font-black transition-colors px-3.5 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-900"
                      >
                        <ShieldCheck className="w-4 h-4 text-slate-400" />
                        System Administrator gate
                      </button>
                    </div>

                    <div className="flex items-center gap-3 my-4 select-none">
                      <div className="flex-1 h-px bg-slate-100 dark:bg-slate-800" />
                      <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Enterprise OAuth</span>
                      <div className="flex-1 h-px bg-slate-100 dark:bg-slate-800" />
                    </div>

                    <div className="grid grid-cols-2 gap-2.5">
                      {['Hospital SSO (Simulated)', 'Health Network SSO (Simulated)'].map(sso => (
                        <button 
                          key={sso}
                          type="button"
                          onClick={() => addToast(`${sso} auth initiated (Simulated)`, 'info')}
                          className="flex items-center justify-center gap-2 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-750 dark:text-slate-300 font-bold text-xs cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors shadow-sm"
                        >
                          {sso}
                        </button>
                      ))}
                    </div>

                    <p className="text-center text-xs font-semibold text-slate-500 mt-4 leading-none">
                      New clinical coordinator?{' '}
                      <Link to="/register" className="text-blue-600 font-black hover:text-blue-700">Register Profile</Link>
                    </p>
                  </div>
                ) : (
                  <div className="text-center mt-6">
                    <button 
                      type="button" 
                      onClick={() => { setActiveRole('doctor'); setError(''); }} 
                      className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-755 dark:hover:text-slate-350 bg-transparent border-none cursor-pointer font-bold transition-colors"
                    >
                      <ArrowLeft className="w-4 h-4" /> Return to standard login
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Forgot Credentials View */}
            {view === 'forgot' && (
              <div className="text-center space-y-6">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/20 mx-auto flex items-center justify-center text-blue-600 dark:text-blue-450 border border-blue-100 dark:border-blue-900/50 shadow-sm">
                  <Key className="w-7 h-7" />
                </div>
                <div className="text-center">
                  <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 leading-none">Reset Credentials</h1>
                  <p className="text-xs text-slate-500 mt-2 font-semibold">Enter email to generate custom reset token</p>
                </div>

                <div className="text-left">
                  <AuthInput 
                    label="Registered Email Address" 
                    type="email" 
                    name="email" 
                    placeholder="you@hospital.com" 
                    icon={Mail}
                    value={formData.email} 
                    onChange={handleChange} 
                  />
                </div>

                <button
                  onClick={() => {
                    addToast('Reset link dispatched to clinical email.', 'success');
                    setView('login');
                  }}
                  className="w-full py-3.5 rounded-xl text-white font-bold text-xs uppercase tracking-wider cursor-pointer border-none shadow-md"
                  style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)' }}
                >
                  Send Verification Link
                </button>

                <button 
                  onClick={() => setView('login')}
                  className="text-xs font-bold text-slate-500 hover:text-slate-700 dark:text-slate-400 bg-transparent border-none cursor-pointer"
                >
                  ← Back to Login
                </button>
              </div>
            )}
            
          </div>

        </div>
      </div>
    </div>
  );
};

export default LoginPage;
