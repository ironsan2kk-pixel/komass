/**
 * Alert Component - Notification/message box
 * 
 * Usage:
 *   <Alert variant="success">Operation completed!</Alert>
 *   <Alert variant="danger" onClose={() => setShow(false)}>
 *     Error occurred!
 *   </Alert>
 */
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

const Alert = ({
  children,
  variant = 'info',
  onClose,
  icon: CustomIcon,
  className = '',
}) => {
  const variants = {
    success: {
      bg: 'bg-success-600/10 border-success-600/30',
      text: 'text-success-300',
      icon: CheckCircle,
    },
    danger: {
      bg: 'bg-danger-600/10 border-danger-600/30',
      text: 'text-danger-300',
      icon: AlertCircle,
    },
    warning: {
      bg: 'bg-warning-600/10 border-warning-600/30',
      text: 'text-warning-300',
      icon: AlertTriangle,
    },
    info: {
      bg: 'bg-info-600/10 border-info-600/30',
      text: 'text-info-300',
      icon: Info,
    },
  };

  const config = variants[variant];
  const Icon = CustomIcon || config.icon;

  return (
    <div 
      className={`
        ${config.bg}
        border rounded-lg p-4
        flex items-start gap-3
        ${className}
      `}
      role="alert"
    >
      {/* Icon */}
      <Icon className={`w-5 h-5 ${config.text} flex-shrink-0 mt-0.5`} />

      {/* Content */}
      <div className={`flex-1 ${config.text} text-sm`}>
        {children}
      </div>

      {/* Close Button */}
      {onClose && (
        <button
          onClick={onClose}
          className={`${config.text} hover:opacity-70 transition-opacity flex-shrink-0`}
          aria-label="Close alert"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default Alert;
