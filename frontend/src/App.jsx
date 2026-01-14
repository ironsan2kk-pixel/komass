/**
 * App.jsx - Main Application with Navigation
 *
 * Updated in Chat #49:
 * - Added Optimizer page to navigation
 *
 * Phase 12 Updates:
 * - Integrated ThemeProvider for dark/light mode support
 * - Added ThemeToggle in sidebar
 * - Updated colors to use design system
 *
 * Pages:
 * - Indicator (TRG/Dominant)
 * - Data
 * - Presets
 * - Optimizer (NEW)
 * - Signals
 * - Bots
 * - Settings
 */
import { Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { ThemeToggle } from './components/ui';
import ErrorBoundary from './components/ErrorBoundary';

// Pages
import Dashboard from './pages/Dashboard';
import Indicator from './pages/Indicator';
import Data from './pages/Data';
import Presets from './pages/Presets';
import Optimizer from './pages/Optimizer';
import Settings from './pages/Settings';
import Signals from './pages/Signals';
import Bots from './pages/Bots';

const NAV_ITEMS = [
  { path: '/', name: '🏠 Dashboard', component: Dashboard },
  { path: '/indicator', name: '📊 Индикатор', component: Indicator },
  { path: '/data', name: '📁 Данные', component: Data },
  { path: '/presets', name: '🎛️ Пресеты', component: Presets },
  { path: '/optimizer', name: '🔬 Оптимизация', component: Optimizer, highlight: true },
  { divider: true },
  { path: '/signals', name: '🔔 Сигналы', component: Signals },
  { path: '/bots', name: '🤖 Боты', component: Bots },
  { divider: true },
  { path: '/settings', name: '⚙️ Настройки', component: Settings },
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-dark-900 dark:bg-dark-900 light:bg-gray-50 flex">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-dark-800 dark:bg-dark-800 light:bg-white light:border-r light:border-gray-200 transition-all duration-300 flex flex-col`}>
          {/* Logo */}
          <div className="p-4 border-b border-dark-700 dark:border-dark-700 light:border-gray-200">
            <div className="flex items-center justify-between">
              {sidebarOpen && (
                <div>
                  <h1 className="text-xl font-bold text-white dark:text-white light:text-gray-900">KOMAS</h1>
                  <p className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">Trading Server v4.0</p>
                  <div className="mt-2 px-2 py-1 bg-yellow-600/20 border border-yellow-600/40 rounded text-xs text-yellow-400 font-medium">
                    📊 PAPER TRADING ONLY
                  </div>
                </div>
              )}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="text-gray-400 hover:text-white dark:text-gray-400 dark:hover:text-white light:text-gray-600 light:hover:text-gray-900 p-2"
              >
                {sidebarOpen ? '◀' : '▶'}
              </button>
            </div>
          </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item, index) =>
            item.divider ? (
              <div key={index} className="border-t border-dark-700 dark:border-dark-700 light:border-gray-200 my-2" />
            ) : (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white dark:bg-primary-600 light:bg-primary-500'
                      : item.highlight
                      ? 'bg-gradient-to-r from-accent-600/30 to-primary-600/30 text-accent-300 hover:from-accent-600/50 hover:to-primary-600/50'
                      : 'text-gray-400 hover:bg-dark-700 hover:text-white dark:text-gray-400 dark:hover:bg-dark-700 dark:hover:text-white light:text-gray-600 light:hover:bg-gray-100 light:hover:text-gray-900'
                  }`
                }
              >
                <span className={sidebarOpen ? '' : 'mx-auto'}>{item.name.split(' ')[0]}</span>
                {sidebarOpen && <span className="ml-2">{item.name.split(' ').slice(1).join(' ')}</span>}
              </NavLink>
            )
          )}
        </nav>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-dark-700 dark:border-dark-700 light:border-gray-200">
          <div className="flex items-center justify-center">
            <ThemeToggle />
          </div>
        </div>

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-dark-700 dark:border-dark-700 light:border-gray-200 text-xs text-gray-500 dark:text-gray-500 light:text-gray-600">
            <p>© 2025 Komas Trading</p>
            <p className="mt-1 text-gray-600 dark:text-gray-600 light:text-gray-500">v4.0 - Phase 12</p>
          </div>
        )}
      </aside>

      {/* Main Content */}
        <main className="flex-1 overflow-auto bg-dark-900 dark:bg-dark-900 light:bg-gray-50">
          <ErrorBoundary>
            <Routes>
              {NAV_ITEMS.filter(item => !item.divider).map(item => (
                <Route key={item.path} path={item.path} element={<item.component />} />
              ))}
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </ThemeProvider>
  );
}
