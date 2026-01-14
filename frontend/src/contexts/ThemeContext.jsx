/**
 * Theme Context - Dark/Light mode management
 * 
 * Usage:
 *   import { ThemeProvider, useTheme } from './contexts/ThemeContext';
 * 
 *   function App() {
 *     return (
 *       <ThemeProvider>
 *         <YourApp />
 *       </ThemeProvider>
 *     );
 *   }
 * 
 *   function Component() {
 *     const { theme, toggleTheme } = useTheme();
 *     return <button onClick={toggleTheme}>{theme}</button>;
 *   }
 */
import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  // Initialize theme from localStorage or default to 'dark'
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved || 'dark';
  });

  // Update document class and localStorage when theme changes
  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    // Add current theme class
    root.classList.add(theme);
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const setDarkTheme = () => setTheme('dark');
  const setLightTheme = () => setTheme('light');

  const value = {
    theme,
    toggleTheme,
    setDarkTheme,
    setLightTheme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
