/**
 * Calendar Page - Экономический календарь
 */
import { useState } from 'react';

export default function Calendar() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">📅 Экономический календарь</h1>
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <p className="text-gray-400">Экономические события будут отображаться здесь.</p>
      </div>
    </div>
  );
}
