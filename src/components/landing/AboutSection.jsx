import React from 'react';
import { Target, Heart, Shield } from 'lucide-react';

/**
 * About section for the landing page.
 * Details the corporate mission and values of NeuroCare Nexus.
 * 
 * @returns {JSX.Element}
 */
export const AboutSection = () => {
  return (
    <section id="about" className="py-20 bg-white border-t border-b border-slate-100">
      <div className="max-w-4xl mx-auto px-4 text-center space-y-8">
        
        {/* Badge */}
        <div className="inline-flex items-center gap-1 bg-teal-50 text-primary border border-teal-100 px-3 py-1 rounded-full text-sm font-semibold">
          <Target className="w-4 h-4" />
          <span>Our Core Mission</span>
        </div>

        {/* Section Heading */}
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
          Bridging Clinical Intelligence and Comfort at Home
        </h2>

        {/* 2-3 Sentence Mission Intro */}
        <p className="text-lg sm:text-xl text-slate-600 leading-relaxed max-w-3xl mx-auto">
          At NeuroCare Nexus, we are dedicated to transforming remote home healthcare by integrating secure, real-time IoT wearables with predictive artificial intelligence. Our mission is to empower patient independence and support caregivers with active, predictive clinical insight, preventing critical events before they occur.
        </p>

        {/* Micro pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-6 max-w-xl mx-auto text-left">
          <div className="flex gap-3">
            <div className="text-primary shrink-0"><Heart className="w-6 h-6" /></div>
            <div>
              <h4 className="font-bold text-slate-800">Compassionate Care</h4>
              <p className="text-sm text-slate-500 leading-normal">Fostering warmth, trust, and continuous guidance for vulnerable populations.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="text-primary shrink-0"><Shield className="w-6 h-6" /></div>
            <div>
              <h4 className="font-bold text-slate-800">Security & Privacy</h4>
              <p className="text-sm text-slate-500 leading-normal">Keeping clinical data encrypted, private, and fully HIPAA compliant.</p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};

export default AboutSection;
