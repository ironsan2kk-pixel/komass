/**
 * Settings Page - Настройки приложения
 */
import { useState } from 'react';

export default function Settings() {
  const [telegram, setTelegram] = useState({ bot_token: '', chat_id: '' });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">⚙️ Настройки</h1>
      
      {/* Telegram */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">📱 Telegram</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Bot Token</label>
            <input
              type="text"
              value={telegram.bot_token}
              onChange={(e) => setTelegram(prev => ({ ...prev, bot_token: e.target.value }))}
              placeholder="123456:ABC-DEF..."
              className="w-full bg-gray-700 px-3 py-2 rounded-lg"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">Chat ID</label>
            <input
              type="text"
              value={telegram.chat_id}
              onChange={(e) => setTelegram(prev => ({ ...prev, chat_id: e.target.value }))}
              placeholder="-1001234567890"
              className="w-full bg-gray-700 px-3 py-2 rounded-lg"
            />
          </div>
        </div>
        <button className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg">
          💾 Сохранить
        </button>
      </div>

      {/* Database */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">🗄️ База данных</h2>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">
            📦 Backup
          </button>
          <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg">
            🔄 Restore
          </button>
          <button className="px-4 py-2 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded-lg">
            🗑️ Clear Cache
          </button>
        </div>
      </div>
    </div>
  );
}
