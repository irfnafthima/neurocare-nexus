import React from 'react';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';

/**
 * Re-themed Footer component aligned with the Figma mockup structure.
 * Features a 5-column link directory, social SVG nodes, and bottom FDA compliance list.
 * 
 * @returns {JSX.Element}
 */
export const Footer = () => {
  const currentYear = new Date().getFullYear();

  const handleScrollTo = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const columns = [
    {
      title: 'Company',
      links: ['About', 'Careers', 'Press', 'Blog', 'Contact']
    },
    {
      title: 'Product',
      links: ['Features', 'Pricing', 'Security', 'API Docs', 'Changelog']
    },
    {
      title: 'Resources',
      links: ['Documentation', 'Case Studies', 'Webinars', 'Support', 'Status']
    },
    {
      title: 'Legal',
      links: ['Privacy Policy', 'Terms of Service', 'HIPAA Policy', 'Cookie Policy']
    }
  ];

  return (
    <footer className="bg-slate-900 text-slate-400 py-16 px-6 border-t border-slate-800">
      <div className="max-w-7xl mx-auto">
        
        {/* Footer Link Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 mb-12">
          
          {/* Brand Info Column */}
          <div className="lg:col-span-1 space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white">
                <Activity className="w-4 h-4" />
              </div>
              <span className="text-base font-extrabold tracking-tight text-white">
                NeuroCare Nexus
              </span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              AI-powered remote patient monitoring for the modern healthcare system.
            </p>
            
            {/* Social Icons row */}
            <div className="flex gap-3">
              {['fb', 'in', 'tw', 'yt'].map((social) => (
                <div 
                  key={social}
                  className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-500 hover:text-white cursor-pointer transition-colors text-xs font-bold"
                  onClick={() => alert(`Redirecting to ${social.toUpperCase()} profile (Simulated).`)}
                >
                  {social === 'fb' && 'FB'}
                  {social === 'in' && 'IN'}
                  {social === 'tw' && 'TW'}
                  {social === 'yt' && 'YT'}
                </div>
              ))}
            </div>
          </div>

          {/* Nav Links Columns */}
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">
                {col.title}
              </h4>
              <ul className="space-y-3 text-sm">
                {col.links.map((link) => (
                  <li key={link}>
                    <button
                      onClick={() => {
                        if (link === 'Features' || link === 'Pricing' || link === 'About' || link === 'Contact') {
                          handleScrollTo(link.toLowerCase());
                        } else {
                          alert(`Navigating to ${link} section (Simulated).`);
                        }
                      }}
                      className="hover:text-white transition-colors text-left"
                    >
                      {link}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}

        </div>

        {/* Bottom Section: Divider & Certifications */}
        <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
          <span className="text-slate-500">
            &copy; {currentYear} NeuroCare Nexus, Inc. All rights reserved.
          </span>

          <div className="flex items-center gap-4 flex-wrap justify-center">
            {['FDA Cleared', 'HIPAA', 'SOC 2', 'ISO 13485', 'CE Mark'].map((badge) => (
              <span key={badge} className="text-slate-500 font-semibold flex items-center gap-1">
                <span>•</span> {badge}
              </span>
            ))}
          </div>
        </div>

      </div>
    </footer>
  );
};

export default Footer;
