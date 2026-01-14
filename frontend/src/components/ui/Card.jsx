/**
 * Card Component - Reusable card container
 * 
 * Usage:
 *   <Card>
 *     <Card.Header>Title</Card.Header>
 *     <Card.Body>Content</Card.Body>
 *     <Card.Footer>Footer</Card.Footer>
 *   </Card>
 * 
 * Variants: default, bordered, elevated, glass
 */

const Card = ({ 
  children, 
  variant = 'default',
  padding = 'md',
  className = '',
  ...props 
}) => {
  const variants = {
    default: 'bg-dark-800 border border-dark-700',
    bordered: 'bg-dark-800 border-2 border-primary-600/30',
    elevated: 'bg-dark-800 border border-dark-700 shadow-xl',
    glass: 'bg-dark-800/50 backdrop-blur-md border border-dark-700/50',
  };

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div 
      className={`rounded-lg ${variants[variant]} ${paddings[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

// Card Header
Card.Header = ({ children, className = '', ...props }) => (
  <div className={`pb-3 border-b border-dark-700 mb-4 ${className}`} {...props}>
    {children}
  </div>
);

// Card Body
Card.Body = ({ children, className = '', ...props }) => (
  <div className={`${className}`} {...props}>
    {children}
  </div>
);

// Card Footer
Card.Footer = ({ children, className = '', ...props }) => (
  <div className={`pt-3 border-t border-dark-700 mt-4 ${className}`} {...props}>
    {children}
  </div>
);

// Card Title
Card.Title = ({ children, className = '', ...props }) => (
  <h3 className={`text-lg font-semibold text-white ${className}`} {...props}>
    {children}
  </h3>
);

// Card Description
Card.Description = ({ children, className = '', ...props }) => (
  <p className={`text-sm text-gray-400 ${className}`} {...props}>
    {children}
  </p>
);

export default Card;
