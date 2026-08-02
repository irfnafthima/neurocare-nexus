import React from 'react';
import Card from '../common/Card';

/**
 * Alerts logging container.
 * Displays critical alarms or populated clinical alert logs by default.
 * 
 * @param {Object} props
 * @param {Array} [props.alerts] - List of active alert objects.
 * @returns {JSX.Element}
 */
export const AlertCard = ({ alerts }) => {
  const defaultAlerts = [
    { message: '🚨 CRITICAL: Marcus Williams — AFib Arrhythmia detected', timestamp: '2m ago', isCritical: true },
    { message: '⚠️ WARNING: Elena Rodriguez — Elevated Temp (38.2°C)', timestamp: '15m ago', isCritical: false },
    { message: '⚠️ WARNING: Sarah Johnson — Low sensor signal (RSSI: -85dBm)', timestamp: '1h ago', isCritical: false },
    { message: '🔋 BATTERY: Wearable Patient #4 battery low (< 15%)', timestamp: '3h ago', isCritical: false }
  ];

  const dataList = alerts && alerts.length > 0 ? alerts : defaultAlerts;

  return (
    <Card title="Recent Alerts" subtitle="Urgent triggers from clinical rules or sensors">
      <div className="space-y-4 mt-4 select-none">
        {dataList.map((item, idx) => (
          <div key={idx} className="flex gap-3 text-sm pb-3.5 border-b border-slate-100 last:border-0 last:pb-0">
            <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
              item.isCritical ? 'bg-red-500 shadow-[0_0_6px_#EF4444]' : 'bg-amber-500'
            }`} />
            <div className="text-left">
              <p className="font-semibold text-slate-850 leading-normal">{item.message}</p>
              <span className="text-[10px] text-slate-400 font-bold block mt-0.5">{item.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default AlertCard;
