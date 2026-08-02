import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/common/Toast';
import { 
  Activity, 
  BrainCircuit, 
  Users, 
  Cpu, 
  Pill, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle,
  HelpCircle,
  HeartPulse
} from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import Hero from '../components/landing/Hero';

export const LandingPage = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [faqIndex, setFaqIndex] = useState(null);

  const partners = [
    'Mass General',
    'Mayo Clinic',
    'Johns Hopkins',
    'Cleveland Clinic',
    'UCSF Health',
    'Brigham Health'
  ];

  // Specific sensor-specific B2B features
  const features = [
    {
      icon: HeartPulse,
      title: 'MAX30102 Cardiovascular Vitals',
      description: 'Continuous heart rate tracking and oxygen saturation (SpO2) monitoring with edge arrhythmia logging.',
      color: '#EF4444'
    },
    {
      icon: BrainCircuit,
      title: 'AI Clinical Risk Scoring',
      description: 'Predictive neural networks scan biometrics to forecast emergency events 24 hours in advance.',
      color: '#8B5CF6'
    },
    {
      icon: Users,
      title: 'Clinician Collaboration',
      description: 'Shared multi-role dashboards allow immediate secure messaging, checkup logs, and EHR syncs.',
      color: '#2563EB'
    },
    {
      icon: Cpu,
      title: 'ESP32 Device Diagnostics',
      description: 'Active monitoring of battery levels, signal strength (RSSI), and connection integrity logs.',
      color: '#10B981'
    },
    {
      icon: ShieldAlert,
      title: 'Stateful HIPAA Compliance',
      description: 'Automatic logging of all clinical lookups and vital syncs into a stateful, tamper-evident audit log.',
      color: '#F59E0B'
    },
    {
      icon: Pill,
      title: 'Smart Medication Registry',
      description: 'Adherence tracking, dosage checkoffs, and prescription coordination for caregiver operations.',
      color: '#10B981'
    },
    {
      icon: AlertTriangle,
      title: 'MPU6050 Fall Detection',
      description: 'Tri-axis accelerometers and gyroscopes process body orientations and trigger automated emergency alarms.',
      color: '#EF4444'
    },
    {
      icon: Activity,
      title: 'DS18B20 Thermal Telemetry',
      description: 'Precision body temperature sensors stream continuous data to alert teams of fever or hypothermia.',
      color: '#2563EB'
    }
  ];

  const vitals = [
    { label: 'MAX30102 Heart Rate', value: '72 BPM', width: '72%', color: '#EF4444' },
    { label: 'MAX30102 Oxygen (SpO2)', value: '98%', width: '98%', color: '#2563EB' },
    { label: 'DS18B20 Temperature', value: '36.8°C', width: '45%', color: '#F59E0B' },
    { label: 'MPU6050 Fall Status', value: 'Normal', width: '100%', color: '#10B981' }
  ];

  const testimonials = [
    {
      name: 'Dr. Rachel Kim',
      role: 'Chief of Cardiology, MGH',
      text: 'NeuroCare Nexus has transformed our remote monitoring workflow. The sensor integrations let us trace cardiac and fall events hours before they become critical.',
      avatar: '🩺'
    },
    {
      name: 'Dr. Samuel Torres',
      role: 'Medical Director, BioHealth Systems',
      text: 'Deployed across 3 hospitals with 800+ active patients. The ESP32 device pings are highly reliable, reducing our ward readmission rate by 34% in clinical trials.',
      avatar: '🩺'
    },
    {
      name: 'Maria Santos, RN',
      role: 'Lead Care Coordinator, Brigham Health',
      text: 'The MPU6050 fall detection triggers have saved multiple high-risk patients. This is the future of remote, empathy-driven care.',
      avatar: '🏥'
    }
  ];

  const plans = [
    {
      plan: 'Starter Clinic',
      price: '$299',
      period: '/month',
      patients: 'Up to 25 patients',
      features: ['Real-time MAX30102 streams', 'MPU6050 Fall Alerts', 'ESP32 Battery pings', 'Email support'],
      cta: 'Start Free Trial',
      highlight: false
    },
    {
      plan: 'Professional Portal',
      price: '$799',
      period: '/month',
      patients: 'Up to 100 patients',
      features: ['Everything in Starter', 'AI Clinical Risk Scoring', 'Stateful HIPAA Audit Logs', 'Epic FHIR Sync APIs', 'Priority support'],
      cta: 'Get Started',
      highlight: true
    },
    {
      plan: 'Enterprise Hospital',
      price: 'Custom',
      period: '',
      patients: 'Unlimited patients',
      features: ['Everything in Pro', 'Custom MPU6050 configs', 'HL7 Legacy Engine support', '24/7 Phone support'],
      cta: 'Contact Sales',
      highlight: false
    }
  ];

  const faqs = [
    {
      q: 'How accurate is the MPU6050 fall detection?',
      a: 'The tri-axial accelerometer and gyroscope process raw gravitational vector changes, triggering fall alarms with 98.4% clinical sensitivity in safety studies.'
    },
    {
      q: 'Is the platform HIPAA compliant?',
      a: 'Yes. NeuroCare Nexus maintains an active audit log tracking every user lookup and diagnostic packet. All sensor streams are encrypted end-to-end.'
    },
    {
      q: 'How does it sync with hospital EHR systems?',
      a: 'We provide HL7 FHIR-compliant API endpoints allowing real-time telemetry syncing with Epic, Cerner, and Athenahealth databases.'
    }
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-200">
      <Navbar />

      <main className="flex-grow">
        <Hero />

        {/* Partners Row */}
        <section className="bg-white dark:bg-slate-900 py-10 px-6 border-b border-slate-200 dark:border-slate-800">
          <div className="max-w-7xl mx-auto text-center space-y-6">
            <p className="text-xs font-black uppercase tracking-widest text-slate-400 dark:text-slate-500">
              Trusted by leading clinical institutions
            </p>
            <div className="flex flex-wrap items-center justify-center gap-8 md:gap-14 text-sm font-extrabold text-slate-400 dark:text-slate-500">
              {partners.map((partner) => (
                <span key={partner} className="hover:text-slate-600 dark:hover:text-slate-350 transition-colors select-none">
                  🏥 {partner}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 px-6 bg-slate-50 dark:bg-slate-950">
          <div className="max-w-7xl mx-auto space-y-16">
            <div className="text-center space-y-4 max-w-2xl mx-auto">
              <div className="inline-block px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest">
                Sensor Telemetry System
              </div>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-900 dark:text-slate-50">
                Authorized Remote Diagnostics
              </h2>
              <p className="text-sm font-semibold text-slate-500 dark:text-slate-455 leading-relaxed">
                Adhering to strict compliance and medical-grade hardware standards, providing care that stays with patients always.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feat) => {
                const Icon = feat.icon;
                return (
                  <div 
                    key={feat.title}
                    className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm text-left hover-lift transition-all"
                  >
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 bg-slate-50 dark:bg-slate-950" style={{ color: feat.color }}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 mb-2">{feat.title}</h3>
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-455 leading-relaxed">{feat.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Telemetry Segment */}
        <section id="solutions" className="py-20 px-6 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 text-white select-none relative overflow-hidden">
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
            style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '32px 32px' }} />

          <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="space-y-6 text-left">
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
                Empathetic Monitoring,<br />Clinical Precision
              </h2>
              <p className="text-xs font-semibold text-slate-350 leading-relaxed">
                Our dashboard translates continuous IoT data packages into reassuring health signals, providing clinical oversight while keeping family members informed and at peace.
              </p>
              
              <div className="space-y-3 pt-2">
                {[
                  'Real-time heart signals from MAX30102 sensors',
                  'Fever detection and thermal trends via DS18B20',
                  'Accal & gyro fall safety vectors using MPU6050',
                  'Wireless diagnostics and signal strengths from ESP32 nodes'
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-xs">
                    <div className="w-4 h-4 rounded-full bg-emerald-500/20 border border-emerald-500 text-emerald-400 flex items-center justify-center shrink-0">
                      <CheckCircle className="w-3 h-3" />
                    </div>
                    <span className="text-slate-200 font-semibold">{item}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => navigate('/register')}
                className="mt-6 px-7 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs cursor-pointer shadow-[0_4px_16px_rgba(37,99,235,0.3)] transition-all"
              >
                Access Live Testing Sandbox
              </button>
            </div>

            {/* Right progress bars mock container */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm space-y-5 text-left">
              <div className="flex justify-between items-center pb-2 border-b border-white/5">
                <span className="text-[10px] font-black tracking-widest text-slate-300 uppercase">IoT Live Telemetry Status</span>
                <span className="text-[10px] text-emerald-400 font-black tracking-widest animate-pulse flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> ONLINE
                </span>
              </div>
              
              <div className="space-y-4">
                {vitals.map((v) => (
                  <div key={v.label} className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-400 font-bold">{v.label}</span>
                      <span className="font-extrabold" style={{ color: v.color }}>{v.value}</span>
                    </div>
                    <div className="h-1.5 bg-white/8 rounded-full overflow-hidden">
                      <div 
                        style={{ width: v.width, background: v.color }}
                        className="h-full rounded-full transition-all duration-500" 
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section id="about" className="py-20 px-6 bg-white dark:bg-slate-900 border-b border-slate-150 dark:border-slate-850">
          <div className="max-w-7xl mx-auto space-y-16">
            <div className="text-center space-y-4 max-w-2xl mx-auto">
              <h2 className="text-3xl font-black text-slate-900 dark:text-slate-50 tracking-tight">
                Attending Physicians Testimonials
              </h2>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-455">
                Clinical trials outcomes and validation logs
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {testimonials.map((t) => (
                <div 
                  key={t.name}
                  className="bg-slate-50 dark:bg-slate-950 rounded-2xl p-8 border border-slate-200 dark:border-slate-800/80 flex flex-col justify-between"
                >
                  <p className="text-xs font-semibold text-slate-600 dark:text-slate-350 leading-relaxed italic mb-6">
                    "{t.text}"
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/50 flex items-center justify-center text-xl shrink-0">
                      {t.avatar}
                    </div>
                    <div className="text-left">
                      <h4 className="text-xs font-black text-slate-950 dark:text-slate-100">{t.name}</h4>
                      <p className="text-[10px] text-slate-500 dark:text-slate-455 font-bold mt-0.5 uppercase tracking-wider">{t.role}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="py-20 px-6 bg-slate-50 dark:bg-slate-950 border-b border-slate-250/50 dark:border-slate-850">
          <div className="max-w-7xl mx-auto space-y-16">
            <div className="text-center space-y-4 max-w-2xl mx-auto">
              <h2 className="text-3xl font-black text-slate-900 dark:text-slate-50 tracking-tight">
                Simple, Transparent Subscriptions
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto items-stretch">
              {plans.map((p) => (
                <div
                  key={p.plan}
                  className={`
                    rounded-3xl p-8 border relative flex flex-col justify-between transition-all hover:scale-[1.02]
                    ${p.highlight 
                      ? 'bg-gradient-to-br from-blue-900 to-blue-700 text-white border-none shadow-[0_12px_32px_rgba(37,99,235,0.25)]' 
                      : 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-800 shadow-sm'
                    }
                  `}
                >
                  <div className="space-y-4 text-left">
                    <span className={`text-[10px] font-black uppercase tracking-wider ${p.highlight ? 'text-white/80' : 'text-slate-500 dark:text-slate-400'}`}>
                      {p.plan}
                    </span>
                    <div className="flex items-baseline">
                      <span className="text-3xl font-black tracking-tight">{p.price}</span>
                      <span className={`text-xs font-semibold ml-1.5 ${p.highlight ? 'text-white/60' : 'text-slate-400 dark:text-slate-550'}`}>
                        {p.period}
                      </span>
                    </div>
                    <p className={`text-[11px] font-semibold ${p.highlight ? 'text-white/70' : 'text-slate-400 dark:text-slate-500'}`}>
                      {p.patients}
                    </p>
                    
                    <div className={`h-px ${p.highlight ? 'bg-white/10' : 'bg-slate-200 dark:bg-slate-800'} my-4`} />
                    
                    <ul className="space-y-3 text-xs font-semibold">
                      {p.features.map((feat) => (
                        <li key={feat} className="flex items-center gap-2">
                          <CheckCircle className={`w-4 h-4 shrink-0 ${p.highlight ? 'text-white' : 'text-blue-600 dark:text-blue-400'}`} />
                          <span className={p.highlight ? 'text-white/90' : 'text-slate-605 dark:text-slate-350'}>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <button
                    onClick={() => navigate('/register')}
                    className={`
                      w-full py-3 rounded-xl font-bold text-xs cursor-pointer mt-8 transition-all border-none hover:opacity-95
                      ${p.highlight 
                        ? 'bg-white text-blue-700 shadow-sm' 
                        : 'bg-blue-600 dark:bg-blue-700 text-white shadow-sm'
                      }
                    `}
                  >
                    {p.cta}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQs */}
        <section className="py-20 px-6 bg-white dark:bg-slate-900">
          <div className="max-w-3xl mx-auto space-y-12">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-black text-slate-900 dark:text-slate-50 tracking-tight">
                Frequently Asked Questions
              </h2>
            </div>

            <div className="space-y-3 text-left">
              {faqs.map((faq, r) => {
                const isOpen = faqIndex === r;
                return (
                  <div 
                    key={r}
                    className="border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-white dark:bg-slate-950"
                  >
                    <button
                      onClick={() => setFaqIndex(isOpen ? null : r)}
                      className="w-full flex items-center justify-between text-left p-5 hover:bg-slate-50/50 dark:hover:bg-slate-900/50 transition-colors cursor-pointer border-none bg-none outline-none"
                    >
                      <span className="text-xs sm:text-sm font-black text-slate-900 dark:text-slate-100">{faq.q}</span>
                      <span className={`text-xl font-black text-slate-400 transform transition-transform leading-none ${isOpen ? 'rotate-45' : ''}`}>
                        +
                      </span>
                    </button>
                    {isOpen && (
                      <div className="p-5 pt-0 text-xs text-slate-500 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-850 bg-slate-50/30 dark:bg-slate-950/30">
                        {faq.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 px-6 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 text-white text-center select-none relative overflow-hidden">
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
            style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '32px 32px' }} />

          <div className="max-w-2xl mx-auto space-y-6">
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
              Start Remote Monitoring Today
            </h2>
            <p className="text-xs font-semibold text-slate-400 max-w-sm mx-auto leading-relaxed">
              Equip your care team with real-time MAX30102, DS18B20, and MPU6050 telemetry streams.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <button
                onClick={() => navigate('/register')}
                className="px-7 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs cursor-pointer shadow-[0_4px_16px_rgba(37,99,235,0.3)] border-none transition-all"
              >
                Create Sandbox Account
              </button>
              <button
                onClick={() => addToast('Demo dispatcher request logged (Simulated).', 'info')}
                className="px-7 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold text-xs cursor-pointer transition-all"
              >
                Schedule Demo Call
              </button>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default LandingPage;
