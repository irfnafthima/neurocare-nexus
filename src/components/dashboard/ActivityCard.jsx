import React from 'react';
import Card from '../common/Card';

/**
 * Activity log tracker container.
 * Displays activities list or populated mock lists by default.
 * 
 * @param {Object} props
 * @param {Array} [props.activities] - List of activity item objects.
 * @returns {JSX.Element}
 */
export const ActivityCard = ({ activities }) => {
  const defaultActivities = [
    { message: 'Marcus Williams — Heart Rate spike: 118 BPM', timestamp: '2m ago' },
    { message: 'Wearable NeuroPatch #E341 synced successfully', timestamp: '12m ago' },
    { message: 'Prescription updated: Metoprolol 25mg for M. Williams', timestamp: '1h ago' },
    { message: 'Elena Rodriguez — Fall warning threshold trigger', timestamp: '2h ago' },
    { message: 'Telemetry stream calibration complete', timestamp: '4h ago' }
  ];

  const dataList = activities && activities.length > 0 ? activities : defaultActivities;

  return (
    <Card title="Recent Activity" subtitle="Real-time log of device check-ins & status changes">
      <div className="space-y-4 mt-4 select-none">
        {dataList.map((item, idx) => (
          <div key={idx} className="flex gap-3 text-sm pb-3.5 border-b border-slate-100 last:border-0 last:pb-0">
            <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0" />
            <div className="text-left">
              <p className="font-semibold text-slate-800 leading-normal">{item.message}</p>
              <span className="text-[10px] text-slate-400 font-bold block mt-0.5">{item.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default ActivityCard;
