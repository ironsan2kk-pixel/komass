/**
 * KOMAS Trading Server v3.5 - Main App
 * =====================================
 * Главный компонент с навигацией и роутингом
 */
import { Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';

// Pages
import Indicator from './pages/Indicator';
import Data from './pages/Data';
import Signals from './pages/Signals';
import Calendar from './pages/Calendar';
import Settings from './pages/Settings';

const NAV_ITEMS = [
  { path: '/', name: '📊 Индикатор', icon: '📊' },
  { path: '/data', name: '📁 Данные', icon: '📁' },
  { divider: true },
  { path: '/signals', name: '🔔 Сигналы', icon: '🔔' },
  { path: '/calendar', name: '📅 Календарь', icon: '📅' },
  { divider: true },
  { path: '/settings', name: '⚙️ Настройки', icon: '⚙️' },
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-gray-800 transition-all duration-300 flex flex-col border-r border-gray-700`}>
        {/* Logo */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <div>
                <h1 className="text-xl font-bold text-white">KOMAS</h1>
                <p className="text-xs text-gray-400">Trading Server v3.5</p>
              </div>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-white p-2 hover:bg-gray-700 rounded transition-colors"
            >
              {sidebarOpen ? '◀' : '▶'}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item, index) => 
            item.divider ? (
              <div key={index} className="border-t border-gray-700 my-2" />
            ) : (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <span className={`text-lg ${sidebarOpen ? '' : 'mx-auto'}`}>
                  {item.icon}
                </span>
                {sidebarOpen && (
                  <span className="ml-3 text-sm font-medium">
                    {item.name.split(' ').slice(1).join(' ')}
                  </span>
                )}
              </NavLink>
            )
          )}
        </nav>

        {/* Status */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-gray-400">Backend connected</span>
            </div>
          </div>
        )}

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
            <p>© 2024 Komas Trading</p>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Indicator />} />
          <Route path="/data" element={<Data />} />
          <Route path="/signals" element={<Signals />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
