/**
 * Input Component - Reusable input field
 * 
 * Usage:
 *   <Input 
 *     label="Email"
 *     type="email"
 *     placeholder="Enter your email"
 *     error="Invalid email"
 *     helperText="We'll never share your email"
 *   />
 */
import { forwardRef } from 'react';

const Input = forwardRef(({
  label,
  type = 'text',
  error,
  helperText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  className = '',
  containerClassName = '',
  ...props
}, ref) => {
  const baseStyles = 'bg-dark-700 border text-gray-100 placeholder-gray-500 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark-800';
  
  const stateStyles = error
    ? 'border-danger-600 focus:ring-danger-500 focus:border-danger-600'
    : 'border-dark-600 focus:ring-primary-500 focus:border-primary-500 hover:border-dark-500';

  const withIconPadding = leftIcon ? 'pl-10' : rightIcon ? 'pr-10' : '';

  return (
    <div className={`${fullWidth ? 'w-full' : ''} ${containerClassName}`}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          {label}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        {/* Left Icon */}
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
            {leftIcon}
          </div>
        )}

        {/* Input Field */}
        <input
          ref={ref}
          type={type}
          className={`
            ${baseStyles}
            ${stateStyles}
            ${withIconPadding}
            px-4 py-2
            ${fullWidth ? 'w-full' : ''}
            ${className}
          `}
          {...props}
        />

        {/* Right Icon */}
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400">
            {rightIcon}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-1.5 text-sm text-danger-400 flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}

      {/* Helper Text */}
      {helperText && !error && (
        <p className="mt-1.5 text-sm text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
