/**
 * Button Component - Reusable button with variants and sizes
 * 
 * Usage:
 *   <Button variant="primary" size="md" onClick={handleClick}>
 *     Click me
 *   </Button>
 * 
 * Variants: primary, secondary, success, danger, warning, ghost, outline
 * Sizes: sm, md, lg
 */
import { forwardRef } from 'react';

const Button = forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  ...props
}, ref) => {
  // Base styles
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg';

  // Variant styles
  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus:ring-primary-500 shadow-md hover:shadow-lg',
    secondary: 'bg-dark-700 text-gray-200 hover:bg-dark-600 active:bg-dark-500 focus:ring-dark-500 shadow-md hover:shadow-lg',
    success: 'bg-success-600 text-white hover:bg-success-700 active:bg-success-800 focus:ring-success-500 shadow-md hover:shadow-lg',
    danger: 'bg-danger-600 text-white hover:bg-danger-700 active:bg-danger-800 focus:ring-danger-500 shadow-md hover:shadow-lg',
    warning: 'bg-warning-600 text-white hover:bg-warning-700 active:bg-warning-800 focus:ring-warning-500 shadow-md hover:shadow-lg',
    ghost: 'bg-transparent text-gray-300 hover:bg-dark-700/50 active:bg-dark-700 focus:ring-dark-500',
    outline: 'bg-transparent border-2 border-primary-600 text-primary-400 hover:bg-primary-600/10 active:bg-primary-600/20 focus:ring-primary-500',
  };

  // Size styles
  const sizes = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2.5',
  };

  // Width
  const widthStyles = fullWidth ? 'w-full' : '';

  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`
        ${baseStyles}
        ${variants[variant]}
        ${sizes[size]}
        ${widthStyles}
        ${className}
      `}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {icon && iconPosition === 'left' && !loading && icon}
      {children}
      {icon && iconPosition === 'right' && !loading && icon}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;
