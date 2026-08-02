import React from 'react';
import Card from '../common/Card';

/**
 * Appointments scheduling container.
 * Displays scheduled clinician interactions or scheduled visits by default.
 * 
 * @param {Object} props
 * @param {Array} [props.appointments] - List of appointment objects.
 * @returns {JSX.Element}
 */
export const AppointmentCard = ({ appointments }) => {
  const defaultAppointments = [
    { details: 'Dr. Rachel Kim — Cardiology consultation with Sarah Johnson', time: 'Today, 02:00 PM' },
    { details: 'Maria Santos, RN — Biometric review with Marcus Williams', time: 'Tomorrow, 10:30 AM' },
    { details: 'Dr. Samuel Torres — EEG interpretation checkup', time: 'Jan 28, 04:00 PM' },
    { details: 'Home Care Nurse — Patch replacement checkup', time: 'Jan 29, 09:00 AM' }
  ];

  const dataList = appointments && appointments.length > 0 ? appointments : defaultAppointments;

  return (
    <Card title="Upcoming Appointments" subtitle="Clinician reviews and home care sessions">
      <div className="space-y-4 mt-4 select-none">
        {dataList.map((item, idx) => (
          <div key={idx} className="flex gap-3 text-sm pb-3.5 border-b border-slate-100 last:border-0 last:pb-0">
            <div className="w-2 h-2 rounded-full bg-blue-600 mt-1.5 shrink-0" />
            <div className="text-left">
              <p className="font-semibold text-slate-800 leading-normal">{item.details}</p>
              <span className="text-[10px] text-slate-400 font-bold block mt-0.5">{item.time}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default AppointmentCard;
