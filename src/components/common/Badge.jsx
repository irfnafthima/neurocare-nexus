import React from 'react';

/**
 * Reusable Badge component for representing semantic statuses.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Label of the badge.
 * @param {'normal'|'warning'|'critical'|'emergency'|'neutral'} [props.status='neutral'] - Theme-related semantic status.
 * @param {string} [props.className=''] - Additional custom Tailwind classes.
 * @returns {JSX.Element}
 */
export const Badge = ({
  children,
  status = 'neutral',
  className = '',
  ...rest
}) => {
  const styles = {
    normal: 'bg-green-50 text-green-700 border-green-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    critical: 'bg-orange-50 text-orange-700 border-orange-200',
    emergency: 'bg-red-50 text-red-700 border-red-200',
    neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border
        ${styles[status]}
        ${className}
      `}
      {...rest}
    >
      {children}
    </span>
  );
};

export default Badge;
