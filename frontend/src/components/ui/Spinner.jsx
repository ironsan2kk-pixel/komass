/**
 * Spinner Component - Loading indicator
 * 
 * Usage:
 *   <Spinner size="md" />
 *   <Spinner size="lg" color="primary" />
 */

const Spinner = ({ 
  size = 'md',
  color = 'primary',
  className = '',
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const colors = {
    primary: 'border-primary-600',
    secondary: 'border-gray-600',
    success: 'border-success-600',
    danger: 'border-danger-600',
    warning: 'border-warning-600',
    white: 'border-white',
  };

  return (
    <div 
      className={`
        ${sizes[size]}
        border-4 ${colors[color]} border-t-transparent
        rounded-full animate-spin
        ${className}
      `}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export default Spinner;
