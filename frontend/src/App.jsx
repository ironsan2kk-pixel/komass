import { Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';

// Pages
import Indicator from './pages/Indicator';
import Data from './pages/Data';
import Settings from './pages/Settings';
import Signals from './pages/Signals';
import Bots from './pages/Bots';

const NAV_ITEMS = [
  { path: '/', name: '📊 Индикатор', component: Indicator },
  { path: '/data', name: '📁 Данные', component: Data },
  { divider: true },
  { path: '/signals', name: '🔔 Сигналы', component: Signals },
  { path: '/bots', name: '🤖 Боты', component: Bots },
  { divider: true },
  { path: '/settings', name: '⚙️ Настройки', component: Settings },
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-gray-900 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-gray-800 transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <div>
                <h1 className="text-xl font-bold text-white">KOMAS</h1>
                <p className="text-xs text-gray-400">Trading Server v3.0</p>
              </div>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-white p-2"
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
                  `flex items-center px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : item.highlight
                      ? 'bg-gradient-to-r from-purple-600/30 to-blue-600/30 text-purple-300 hover:from-purple-600/50 hover:to-blue-600/50'
                      : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <span className={sidebarOpen ? '' : 'mx-auto'}>{item.name.split(' ')[0]}</span>
                {sidebarOpen && <span className="ml-2">{item.name.split(' ').slice(1).join(' ')}</span>}
              </NavLink>
            )
          )}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
            <p>© 2025 Komas Trading</p>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          {NAV_ITEMS.filter(item => !item.divider).map(item => (
            <Route key={item.path} path={item.path} element={<item.component />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
