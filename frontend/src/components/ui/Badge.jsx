/**
 * Badge Component - Status and tag indicator
 * 
 * Usage:
 *   <Badge variant="success">Active</Badge>
 *   <Badge variant="danger" size="sm">Error</Badge>
 * 
 * Variants: primary, secondary, success, danger, warning, info, gray
 * Sizes: sm, md, lg
 */

const Badge = ({ 
  children, 
  variant = 'primary',
  size = 'md',
  dot = false,
  className = '',
  ...props 
}) => {
  const variants = {
    primary: 'bg-primary-600/20 text-primary-300 border border-primary-600/30',
    secondary: 'bg-dark-600/20 text-gray-300 border border-dark-600/30',
    success: 'bg-success-600/20 text-success-300 border border-success-600/30',
    danger: 'bg-danger-600/20 text-danger-300 border border-danger-600/30',
    warning: 'bg-warning-600/20 text-warning-300 border border-warning-600/30',
    info: 'bg-info-600/20 text-info-300 border border-info-600/30',
    gray: 'bg-gray-600/20 text-gray-300 border border-gray-600/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const dotColors = {
    primary: 'bg-primary-400',
    secondary: 'bg-gray-400',
    success: 'bg-success-400',
    danger: 'bg-danger-400',
    warning: 'bg-warning-400',
    info: 'bg-info-400',
    gray: 'bg-gray-400',
  };

  return (
    <span 
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-md
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};

export default Badge;
