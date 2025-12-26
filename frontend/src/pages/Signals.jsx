/**
 * Signals Page - Торговые сигналы
 */
import { useState } from 'react';

export default function Signals() {
  const [signals] = useState([]);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">🔔 Сигналы</h1>
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <p className="text-gray-400">Сигналы будут отображаться здесь после настройки мониторинга.</p>
      </div>
    </div>
  );
}
