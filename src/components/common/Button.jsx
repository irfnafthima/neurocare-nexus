import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Reusable Button component styled according to the Calm Vitality design system.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Text or element inside the button.
 * @param {'primary'|'secondary'|'outline'|'danger'} [props.variant='primary'] - Button style variant.
 * @param {'sm'|'md'|'lg'} [props.size='md'] - Button size.
 * @param {boolean} [props.isLoading=false] - If true, displays a loading spinner and disables interaction.
 * @param {boolean} [props.disabled=false] - Disables interaction if true.
 * @param {function} [props.onClick] - Click handler function.
 * @param {'button'|'submit'|'reset'} [props.type='button'] - HTML button type.
 * @param {React.ReactNode} [props.icon] - Optional icon to render before children.
 * @param {string} [props.className=''] - Additional CSS classes.
 * @returns {JSX.Element}
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  onClick,
  type = 'button',
  icon,
  className = '',
  ...rest
}) => {
  const baseStyle = 'inline-flex items-center justify-center font-medium rounded-button transition-smooth focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-primary hover:bg-primary-dark text-white focus:ring-primary',
    secondary: 'bg-accent hover:bg-accent-dark text-slate-900 focus:ring-accent',
    outline: 'border border-primary text-primary hover:bg-teal-50 focus:ring-primary',
    danger: 'bg-status-emergency hover:bg-red-700 text-white focus:ring-status-emergency',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const isDisabled = disabled || isLoading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        ${baseStyle}
        ${variants[variant]}
        ${sizes[size]}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      {...rest}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      ) : icon ? (
        <span className="mr-2">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};

export default Button;
