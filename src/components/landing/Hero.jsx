import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/api';
import { formatRelativeTime } from '../../utils/analyticsFormatters';

/**
 * Re-engineered Hero component matching the Figma design.
 * Features a dark slate/blue gradient background, ambient glows,
 * statistics counters, and an interactive mockup patient telemetry monitor card.
 * Integrates live, privacy-safe, PHI-free system alert status from the backend.
 *
 * @returns {JSX.Element}
 */
export const Hero = () => {
  const navigate = useNavigate();

  const [alertStatus, setAlertStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchAlertStatus = async () => {
      try {
        const data = await apiService.getPublicAlertStatus();
        if (isMounted) {
          setAlertStatus(data);
          setError(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(true);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchAlertStatus();
    // Controlled polling: query every 30 seconds for real-time status updates without server strain
    const intervalId = setInterval(fetchAlertStatus, 30000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const stats = [
    { v: '50K+', l: 'Patients Monitored' },
    { v: '200+', l: 'Hospitals' },
    { v: '99.9%', l: 'Uptime SLA' },
    { v: '< 1s', l: 'Alert Latency' }
  ];

  const patients = [
    { name: 'Telemetry Bed 101', risk: 12, hr: 72, color: '#34D399' },
    { name: 'Telemetry Bed 204', risk: 68, hr: 118, color: '#EF4444' },
    { name: 'Telemetry Bed 305', risk: 45, hr: 88, color: '#F59E0B' }
  ];

  return (
    <section className="relative overflow-hidden py-20 lg:py-28 px-6 bg-gradient-to-br from-slate-900 via-blue-950 to-blue-900 text-white select-none">

      {/* Background ambient grids and light glows */}
      <div className="absolute inset-0 opacity-5 bg-[radial-gradient(circle_at_2px_2px,white_1px,transparent_0)] bg-[size:32px_32px] pointer-events-none" />
      <div className="absolute -top-[20%] -right-[10%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.22)_0%,transparent_70%)] pointer-events-none" />
      <div className="absolute -bottom-[20%] -left-[5%] w-[400px] h-[400px] rounded-full bg-[radial-gradient(circle,rgba(16,185,129,0.15)_0%,transparent_70%)] pointer-events-none" />

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center relative z-10">

        {/* Left Column: Headings & Call to Actions */}
        <div className="space-y-6 text-center lg:text-left">

          {/* FDA Compliance Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34D399]" />
            <span>FDA Cleared • HIPAA Compliant • Live in 200+ Hospitals</span>
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.08] tracking-tight text-white drop-shadow-sm">
            The Future of<br />
            <span className="bg-gradient-to-r from-emerald-400 to-sky-400 bg-clip-text text-transparent">
              Remote Patient
            </span><br />
            Monitoring
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-lg mx-auto lg:mx-0">
            AI-powered continuous monitoring with real-time ECG analysis, predictive health alerts, and emergency response - purpose-built for modern healthcare.
          </p>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2">
            <button
              onClick={() => navigate('/register')}
              className="px-7 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-blue-700 font-bold text-[15px] cursor-pointer shadow-[0_8px_24px_rgba(0,0,0,0.2)] transition-smooth"
            >
              🚀 Start Free Trial
            </button>
            <button
              onClick={() => {
                alert('Demo scheduler loaded (Simulated).');
              }}
              className="px-7 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold text-[15px] cursor-pointer transition-smooth"
            >
              📅 Book a Demo
            </button>
          </div>

          {/* Stat indicators grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-8 max-w-md sm:max-w-none mx-auto lg:mx-0">
            {stats.map((st) => (
              <div key={st.l} className="text-center lg:text-left">
                <div className="text-2xl font-black text-white tracking-tight">{st.v}</div>
                <div className="text-xs text-slate-400 font-medium mt-1 leading-normal">{st.l}</div>
              </div>
            ))}
          </div>

        </div>

        {/* Right Column: High fidelity mock dashboard */}
        <div className="flex justify-center relative">

          {/* Outer Relative Wrapper for floating badge without clipping */}
          <div className="relative w-full max-w-md">

            {/* Dashboard Container Wrapper */}
            <div className="w-full rounded-2xl overflow-hidden bg-white/5 border border-white/10 backdrop-blur-md p-5 shadow-[0_32px_80px_rgba(0,0,0,0.4)] text-left">

              {/* Header info */}
              <div className="flex items-center gap-2 mb-4 pr-36">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34D399] animate-pulse-dot shrink-0" />
                <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider truncate">
                  Live ICU Monitoring
                </span>
                <span className="text-[10px] text-slate-500 font-bold hidden sm:inline">•</span>
                <span className="text-[10px] text-emerald-400 font-bold tracking-wider uppercase shrink-0 hidden sm:inline">
                  All Systems Live
                </span>
              </div>

              {/* ECG Lead Telemetry Area */}
              <div className="bg-[#0A0F1A] rounded-xl p-3.5 mb-4 border border-white/5">
                <span className="text-[9px] text-slate-500 font-bold tracking-widest block mb-2 uppercase">
                  Lead II • ECG • 500 Hz
                </span>

                {/* Telemetry SVG wave graph */}
                <div className="overflow-hidden relative h-12 w-full">
                  <svg className="w-full h-full text-emerald-400" viewBox="0 0 400 50" preserveAspectRatio="none">
                    <path
                      d="M0 25 L40 25 L55 20 L60 5 L65 40 L70 25 L100 25 L115 20 L120 5 L125 40 L130 25 L160 25 L175 20 L180 5 L185 40 L190 25 L220 25 L235 20 L240 5 L245 40 L250 25 L280 25 L295 20 L300 3 L305 42 L310 25 L340 25 L355 20 L360 5 L365 40 L370 25 L400 25"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      fill="none"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>

              {/* Live Biometrics Grid (HR, SpO2, Temp) */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Heart Rate', v: '72', u: 'BPM', icon: '❤️', c: 'text-red-400' },
                  { label: 'SpO2', v: '98', u: '%', icon: '💧', c: 'text-blue-400' },
                  { label: 'Temperature', v: '36.8', u: '°C', icon: '🌡️', c: 'text-amber-400' }
                ].map((vital) => (
                  <div
                    key={vital.label}
                    className="bg-white/5 border border-white/8 rounded-xl p-3 flex flex-col justify-between"
                  >
                    <span className="text-base">{vital.icon}</span>
                    <div className={`text-xl font-black ${vital.c} mt-2`}>
                      {vital.v}
                      <span className="text-[10px] text-white/40 ml-0.5">{vital.u}</span>
                    </div>
                    <span className="text-[9px] text-white/40 font-bold mt-1 uppercase">
                      {vital.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Simulated Patients List */}
              <div className="space-y-2">
                {patients.map((pat) => (
                  <div
                    key={pat.name}
                    className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0"
                  >
                    <div
                      style={{ background: pat.color }}
                      className="w-1.5 h-1.5 rounded-full shrink-0"
                    />
                    <span className="text-xs text-white/80 font-semibold flex-1">
                      {pat.name}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {pat.hr} BPM
                    </span>
                    <div
                      style={{ background: `${pat.color}15`, color: pat.color }}
                      className="px-2 py-0.5 rounded-md text-[9px] font-bold"
                    >
                      Risk {pat.risk}%
                    </div>
                  </div>
                ))}
              </div>

            </div>

            {/* Dynamic Real-Time Floating Alert Badge (Sanitized / PHI-free) */}
            {(() => {
              if (loading && !alertStatus && !error) {
                return (
                  <div className="absolute -top-3 right-0 sm:-top-4 sm:-right-4 bg-slate-800/95 backdrop-blur-md rounded-xl px-3.5 py-2 shadow-[0_8px_24px_rgba(0,0,0,0.3)] border border-slate-700/80 text-[11px] font-bold z-20 pointer-events-none text-left">
                    <div className="flex items-center gap-2 text-slate-300">
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-ping" />
                      <span className="font-bold tracking-wide uppercase text-[10px]">Checking System Status...</span>
                    </div>
                  </div>
                );
              }

              if (error && !alertStatus) {
                return (
                  <div className="absolute -top-3 right-0 sm:-top-4 sm:-right-4 bg-slate-800/95 backdrop-blur-md rounded-xl px-3.5 py-2 shadow-[0_8px_24px_rgba(0,0,0,0.3)] border border-amber-500/50 text-[11px] font-bold z-20 pointer-events-none text-left">
                    <div className="flex items-center gap-1.5 text-amber-400">
                      <span>⚠️</span>
                      <span className="font-bold tracking-wide uppercase text-[10px]">Monitoring Status Unavailable</span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5 font-medium">
                      Unable to reach telemetry service
                    </div>
                  </div>
                );
              }

              if (alertStatus?.hasCriticalAlert) {
                return (
                  <div className="absolute -top-3 right-0 sm:-top-4 sm:-right-4 bg-gradient-to-r from-red-600 to-red-500 rounded-xl px-3.5 py-2 shadow-[0_8px_24px_rgba(239,68,68,0.45)] border border-red-400/80 animate-pulse text-[11px] font-bold z-20 pointer-events-none text-left">
                    <div className="flex items-center gap-1.5">
                      <span>🔴</span>
                      <span className="text-white font-extrabold tracking-wide uppercase text-[10px]">
                        Critical Alert {alertStatus.activeCriticalAlerts > 1 ? `(${alertStatus.activeCriticalAlerts})` : ''}
                      </span>
                      {alertStatus.timestamp && (
                        <span className="text-[9px] text-white/75 font-normal ml-auto">
                          {formatRelativeTime(alertStatus.timestamp)}
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-white/95 mt-0.5 font-semibold">
                      Active critical monitoring event detected
                    </div>
                    <div className="text-[9px] text-white/80 font-medium">
                      Requires immediate attention
                    </div>
                  </div>
                );
              }

              return (
                <div className="absolute -top-3 right-0 sm:-top-4 sm:-right-4 bg-gradient-to-r from-emerald-600/90 to-emerald-500/90 backdrop-blur-md rounded-xl px-3.5 py-2 shadow-[0_8px_24px_rgba(16,185,129,0.35)] border border-emerald-400/80 text-[11px] font-bold z-20 pointer-events-none text-left">
                  <div className="flex items-center gap-1.5">
                    <span>🟢</span>
                    <span className="text-white font-extrabold tracking-wide uppercase text-[10px]">All Systems Stable</span>
                  </div>
                  <div className="text-[10px] text-white/95 mt-0.5 font-semibold">
                    No active critical monitoring alerts
                  </div>
                </div>
              );
            })()}

          </div>

        </div>

      </div>
    </section>
  );
};

export default Hero;
