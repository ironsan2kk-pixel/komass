import { Routes, Route, NavLink } from 'react-router-dom';
import { useState } from 'react';
import { 
  BarChart2, Database, Bell, Calendar, Settings,
  ChevronLeft, ChevronRight
} from 'lucide-react';

// Pages
import Indicator from './pages/Indicator';
import Data from './pages/Data';
import Signals from './pages/Signals';
import CalendarPage from './pages/Calendar';
import SettingsPage from './pages/Settings';

const NAV_ITEMS = [
  { 
    path: '/', 
    name: 'Индикатор', 
    icon: BarChart2,
    component: Indicator 
  },
  { 
    path: '/data', 
    name: 'Данные', 
    icon: Database,
    component: Data 
  },
  { divider: true },
  { 
    path: '/signals', 
    name: 'Сигналы', 
    icon: Bell,
    component: Signals 
  },
  { 
    path: '/calendar', 
    name: 'Календарь', 
    icon: Calendar,
    component: CalendarPage 
  },
  { divider: true },
  { 
    path: '/settings', 
    name: 'Настройки', 
    icon: Settings,
    component: SettingsPage 
  },
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
              className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              {sidebarOpen ? <ChevronLeft className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item, index) => 
            item.divider ? (
              <div key={index} className="border-t border-gray-700 my-3" />
            ) : (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                      : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
                  }`
                }
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && (
                  <span className="font-medium">{item.name}</span>
                )}
              </NavLink>
            )
          )}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-xs text-gray-500">Система активна</span>
            </div>
            <p className="text-xs text-gray-600 mt-2">© 2024 Komas Trading</p>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-900">
        <Routes>
          {NAV_ITEMS.filter(item => !item.divider).map(item => (
            <Route key={item.path} path={item.path} element={<item.component />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
