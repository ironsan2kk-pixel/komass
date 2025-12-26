/**
 * Logs Panel Component
 * ====================
 * Панель логов с авто-открытием при ошибках
 */
import { useEffect, useRef } from 'react';

const LOG_COLORS = {
  info: 'text-blue-400',
  success: 'text-green-400',
  error: 'text-red-400',
  warning: 'text-yellow-400',
  optimize: 'text-purple-400',
};

const LOG_ICONS = {
  info: 'ℹ️',
  success: '✅',
  error: '❌',
  warning: '⚠️',
  optimize: '🔥',
};

export default function LogsPanel({ logs, expanded, onToggle, onClear }) {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current && expanded) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, expanded]);

  // Count errors
  const errorCount = logs.filter(l => l.type === 'error').length;

  // Copy all logs
  const copyLogs = () => {
    const text = logs.map(l => `[${l.time}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
  };

  // Get last log for preview
  const lastLog = logs[logs.length - 1];

  return (
    <div className={`bg-gray-800 border-t border-gray-700 transition-all ${
      expanded ? 'h-48' : 'h-10'
    }`}>
      {/* Header */}
      <div
        className="h-10 px-4 flex items-center justify-between cursor-pointer hover:bg-gray-700/50"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">📋 Логи</span>
          
          {/* Error badge */}
          {errorCount > 0 && (
            <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded text-xs font-medium">
              {errorCount} ошибок
            </span>
          )}

          {/* Last log preview (when collapsed) */}
          {!expanded && lastLog && (
            <span className={`text-xs truncate max-w-md ${LOG_COLORS[lastLog.type]}`}>
              {LOG_ICONS[lastLog.type]} {lastLog.message}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {expanded && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); copyLogs(); }}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
                title="Копировать"
              >
                📋 Copy
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onClear(); }}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
                title="Очистить"
              >
                🗑️ Clear
              </button>
            </>
          )}
          <span className="text-gray-400">{expanded ? '▼' : '▲'}</span>
        </div>
      </div>

      {/* Logs list */}
      {expanded && (
        <div
          ref={scrollRef}
          className="h-[calc(100%-2.5rem)] overflow-y-auto px-4 py-2 font-mono text-xs"
        >
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-4">
              Нет логов
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`flex items-start gap-2 ${LOG_COLORS[log.type]}`}
                >
                  <span className="text-gray-500 flex-shrink-0">[{log.time}]</span>
                  <span>{LOG_ICONS[log.type]}</span>
                  <span className="break-all">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
