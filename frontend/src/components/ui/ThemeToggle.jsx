/**
 * ThemeToggle Component - Dark/Light mode switcher
 * 
 * Usage:
 *   <ThemeToggle />
 */
import { useTheme } from '../../contexts/ThemeContext';
import { Moon, Sun } from 'lucide-react';

const ThemeToggle = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative inline-flex items-center justify-center
        w-10 h-10 rounded-lg
        bg-dark-700 hover:bg-dark-600
        dark:bg-dark-700 dark:hover:bg-dark-600
        light:bg-gray-200 light:hover:bg-gray-300
        border border-dark-600 dark:border-dark-600 light:border-gray-300
        text-gray-400 hover:text-gray-200
        dark:text-gray-400 dark:hover:text-gray-200
        light:text-gray-600 light:hover:text-gray-800
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
        focus:ring-offset-dark-800 dark:focus:ring-offset-dark-800 light:focus:ring-offset-white
        ${className}
      `}
      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      {theme === 'dark' ? (
        <Moon className="w-5 h-5" />
      ) : (
        <Sun className="w-5 h-5" />
      )}
    </button>
  );
};

export default ThemeToggle;
