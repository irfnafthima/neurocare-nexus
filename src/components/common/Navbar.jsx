import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';

/**
 * Figma-aligned Navbar component.
 * Sticky translucent white backdrop with NeuroCare logo, nav links, and CTA buttons.
 */
export const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const navLinks = ['Features', 'Solutions', 'AI Monitoring', 'Pricing', 'About'];

  const handleAnchor = (label) => {
    setMobileOpen(false);
    const id = label.toLowerCase().replace(/\s+/g, '-');
    const el = document.getElementById(id) || document.getElementById(label.toLowerCase());
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header
      className="sticky top-0 z-50 transition-all duration-300"
      style={{
        background: scrolled ? 'rgba(255,255,255,0.96)' : 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: scrolled ? '1px solid #E2E8F0' : '1px solid transparent',
        boxShadow: scrolled ? '0 2px 24px rgba(0,0,0,0.06)' : 'none'
      }}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 no-underline shrink-0">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 4C7.58 4 4 7.58 4 12c0 2.5 1.2 4.7 3.1 6.1L12 21l4.9-2.9C18.8 16.7 20 14.5 20 12c0-4.42-3.58-8-8-8z" fill="white" fillOpacity="0.9" />
              <path d="M8 12h2l1-2.5 2 5 1-2.5h2" stroke="#2563EB" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <div className="text-[14px] font-extrabold text-slate-900 leading-none tracking-tight">NeuroCare Nexus</div>
            <div className="text-[8px] text-slate-400 font-semibold tracking-widest uppercase leading-none mt-0.5">AI Patient Monitoring</div>
          </div>
        </Link>

        {/* Desktop nav links */}
        <nav className="hidden md:flex items-center gap-7">
          {navLinks.map(link => (
            <button
              key={link}
              onClick={() => handleAnchor(link)}
              className="text-[14px] font-medium text-slate-600 hover:text-blue-600 bg-transparent border-none cursor-pointer transition-colors p-0"
            >
              {link}
            </button>
          ))}
        </nav>

        {/* Desktop CTA buttons */}
        <div className="hidden md:flex items-center gap-2.5">
          <Link to="/login">
            <button
              className="px-4 py-2 rounded-xl text-[13px] font-semibold text-slate-700 bg-white border border-slate-200 hover:border-slate-300 cursor-pointer transition-colors"
            >
              Log In
            </button>
          </Link>
          <Link to="/register">
            <button
              className="px-4 py-2 rounded-xl text-[13px] font-bold text-white cursor-pointer border-none"
              style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)', boxShadow: '0 4px 12px rgba(37,99,235,0.3)' }}
            >
              Get Started Free
            </button>
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-xl border border-slate-200 bg-white text-slate-600 cursor-pointer"
          aria-label="Toggle menu"
        >
          {mobileOpen ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white px-6 py-4 space-y-1">
          {navLinks.map(link => (
            <button key={link} onClick={() => handleAnchor(link)}
              className="w-full text-left py-2.5 text-[14px] font-medium text-slate-700 hover:text-blue-600 bg-transparent border-none cursor-pointer transition-colors">
              {link}
            </button>
          ))}
          <div className="pt-3 flex gap-2">
            <Link to="/login" className="flex-1" onClick={() => setMobileOpen(false)}>
              <button className="w-full py-2.5 rounded-xl text-[13px] font-semibold text-slate-700 bg-white border border-slate-200 cursor-pointer">
                Log In
              </button>
            </Link>
            <Link to="/register" className="flex-1" onClick={() => setMobileOpen(false)}>
              <button className="w-full py-2.5 rounded-xl text-[13px] font-bold text-white cursor-pointer border-none"
                style={{ background: 'linear-gradient(135deg, #2563EB, #1D4ED8)' }}>
                Get Started
              </button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
