import React from 'react';
import { UserCheck, Users, ArrowRight } from 'lucide-react';
import PatientContextSelector from './PatientContextSelector';

export const EmptyPatientState = ({ onSelectPatient }) => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 rounded-2xl p-12 text-center max-w-xl mx-auto shadow-sm space-y-4 my-8 font-sans select-none">
      <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400 mx-auto">
        <Users className="w-7 h-7" />
      </div>
      <div>
        <h2 className="text-lg font-black text-slate-900 dark:text-slate-100 tracking-tight">
          No Patient Selected
        </h2>
        <p className="text-xs text-slate-500 font-semibold mt-1 max-w-md mx-auto leading-relaxed">
          Select one of your authorized assigned patients to review clinical health records, prescriptions, and telemetry data.
        </p>
      </div>

      <div className="pt-2 flex justify-center">
        <PatientContextSelector
          activePatientId=""
          onSelectPatient={onSelectPatient}
        />
      </div>
    </div>
  );
};

export default EmptyPatientState;
