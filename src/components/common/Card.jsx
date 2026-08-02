import React from 'react';

/**
 * Reusable Card component styled according to Calm Vitality guidelines (rounded-xl, soft shadows, no harsh borders).
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Card content.
 * @param {string} [props.title] - Optional header title.
 * @param {string} [props.subtitle] - Optional header subtitle under title.
 * @param {React.ReactNode} [props.actions] - Optional header actions aligned to the right.
 * @param {boolean} [props.hoverEffect=false] - Apply subtle hover lift transition.
 * @param {string} [props.className=''] - Additional wrapper classes.
 * @returns {JSX.Element}
 */
export const Card = ({
  children,
  title,
  subtitle,
  actions,
  hoverEffect = false,
  className = '',
  ...rest
}) => {
  return (
    <div
      className={`
        bg-white rounded-2xl shadow-sm border border-slate-100 p-6
        ${hoverEffect ? 'hover-lift' : ''}
        ${className}
      `}
      {...rest}
    >
      {(title || subtitle || actions) && (
        <div className="flex items-start justify-between mb-5 pb-3 border-b border-slate-50 gap-4">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-slate-800 tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-slate-500 mt-0.5 leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="text-slate-700">{children}</div>
    </div>
  );
};

export default Card;
