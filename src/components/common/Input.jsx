import React, { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';

/**
 * Reusable form Input component matching Calm Vitality styling.
 * Supports icons, validation error displays, and password visibility toggles.
 */
export const Input = forwardRef(({
  label,
  type = 'text',
  error,
  icon,
  className = '',
  id,
  showPasswordToggle = false,
  ...rest
}, ref) => {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const isPassword = type === 'password';
  const resolvedType = isPassword && showPasswordToggle && showPassword ? 'text' : type;

  return (
    <div className={`w-full flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label 
          htmlFor={inputId} 
          className="text-sm font-semibold text-slate-700"
        >
          {label}
        </label>
      )}
      
      <div className="relative flex items-center">
        {icon && (
          <div className="absolute left-3 text-slate-400 pointer-events-none">
            {icon}
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          type={resolvedType}
          className={`
            w-full py-2.5 text-base border transition-smooth outline-none rounded-lg
            ${icon ? 'pl-10' : 'pl-3'} 
            ${isPassword && showPasswordToggle ? 'pr-10' : 'pr-3'}
            ${error 
              ? 'border-status-emergency focus:ring-1 focus:ring-status-emergency focus:border-status-emergency bg-red-50/20' 
              : 'border-slate-300 focus:ring-1 focus:ring-primary focus:border-primary bg-white'
            }
          `}
          {...rest}
        />

        {isPassword && showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 text-slate-400 hover:text-slate-600 transition-colors focus:outline-none"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        )}
      </div>
      
      {error && (
        <span className="text-sm font-medium text-status-emergency">
          {error}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
