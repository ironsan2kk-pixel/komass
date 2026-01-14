/**
 * Tooltip Component - Hover tooltip
 * 
 * Usage:
 *   <Tooltip content="This is a tooltip">
 *     <button>Hover me</button>
 *   </Tooltip>
 */
import { useState } from 'react';

const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 200,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

  const showTooltip = () => {
    const id = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    setIsVisible(false);
  };

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrows = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-dark-700 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-dark-700 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-dark-700 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-dark-700 border-t-transparent border-b-transparent border-l-transparent',
  };

  if (!content) return children;

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}
      
      {isVisible && (
        <div 
          className={`
            absolute ${positions[position]} z-50
            px-3 py-2 
            text-sm text-white
            bg-dark-700 dark:bg-dark-700 light:bg-gray-800
            border border-dark-600 dark:border-dark-600 light:border-gray-700
            rounded-lg shadow-lg
            whitespace-nowrap
            animate-fade-in
            ${className}
          `}
          role="tooltip"
        >
          {content}
          {/* Arrow */}
          <div 
            className={`
              absolute w-0 h-0
              border-4
              ${arrows[position]}
            `}
          />
        </div>
      )}
    </div>
  );
};

export default Tooltip;
