import React from 'react';
import Card from '../common/Card';

/**
 * Metric StatCard for Dashboard tracking with live trend signals.
 * 
 * @param {Object} props
 * @param {string} props.title - Metric title (e.g., 'Active Patients').
 * @param {React.ReactNode} props.icon - Lucide icon component.
 * @param {string|number} props.value - Calculated metric total.
 * @param {string} [props.trend] - Percentage change (e.g., '+12%').
 * @param {string} [props.trendLabel] - Trend descriptor (e.g., 'from last week').
 * @param {boolean} [props.isPositive=true] - Positive/Negative color coding.
 * @returns {JSX.Element}
 */
export const StatCard = ({ title, icon, value, trend, trendLabel, isPositive = true }) => {
  return (
    <Card className="relative overflow-hidden transition-smooth border border-slate-200 bg-white rounded-2xl p-5 shadow-sm hover:shadow-md select-none">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
          {title}
        </span>
        <div className="w-10 h-10 rounded-xl bg-blue-50 text-primary flex items-center justify-center border border-blue-100/50">
          {icon}
        </div>
      </div>
      
      <div className="mt-4 flex flex-col">
        <span className="text-3xl font-black text-slate-900 tracking-tight">
          {value}
        </span>
        
        {trend && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs">
            <span className={`font-bold px-2 py-0.5 rounded-md ${
              isPositive 
                ? 'bg-emerald-50 text-emerald-600' 
                : 'bg-red-50 text-red-600'
            }`}>
              {trend}
            </span>
            <span className="text-slate-400 font-semibold">{trendLabel}</span>
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatCard;
