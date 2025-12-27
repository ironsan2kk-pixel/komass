import React, { useRef, useEffect } from 'react';

const LogsPanel = ({ logs = [], onClear, collapsed, onToggle }) => {
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (logsEndRef.current && !collapsed) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, collapsed]);

  useEffect(() => {
    if (logs.length > 0 && logs[logs.length - 1]?.type === 'error' && collapsed) {
      onToggle?.();
    }
  }, [logs, collapsed, onToggle]);

  const getLogIcon = (type) => {
    switch (type) {
      case 'info': return '▶';
      case 'success': return '✔';
      case 'error': return '✗';
      case 'warning': return '⚠';
      case 'optimize': return '🔄';
      case 'trade': return '💰';
      default: return '•';
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'info': return 'text-blue-400';
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'optimize': return 'text-purple-400';
      case 'trade': return 'text-cyan-400';
      default: return 'text-gray-400';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--:--';
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const copyLogs = () => {
    const text = logs.map(l => `[${formatTime(l.timestamp)}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
  };

  const errorCount = logs.filter(l => l?.type === 'error').length;
  const lastLog = logs.length > 0 ? logs[logs.length - 1] : null;

  if (collapsed) {
    return (
      <div 
        onClick={onToggle}
        className={`border-t px-4 py-2 cursor-pointer flex items-center justify-between ${
          errorCount > 0 ? 'bg-red-900/30 border-red-700' : 'bg-gray-800 border-gray-700 hover:bg-gray-750'
        }`}
      >
        <div className="flex items-center gap-2">
          <span className="text-gray-500">📋</span>
          <span className="text-gray-400 text-sm">Логи ({logs.length})</span>
          {errorCount > 0 && (
            <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded">
              {errorCount} ошибок
            </span>
          )}
          {lastLog && (
            <span className={`text-xs ${getLogColor(lastLog.type)}`}>
              {lastLog.message?.length > 60 ? lastLog.message.substring(0, 60) + '...' : lastLog.message}
            </span>
          )}
        </div>
        <span className="text-gray-500">▲</span>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border-t border-gray-700">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <div className="flex items-center gap-2 cursor-pointer" onClick={onToggle}>
          <span className="text-gray-500">📋</span>
          <span className="text-gray-300 text-sm font-medium">Логи</span>
          <span className="text-gray-500 text-xs">({logs.length})</span>
          {errorCount > 0 && (
            <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded">
              {errorCount} ошибок
            </span>
          )}
          <span className="text-gray-500">▼</span>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={(e) => { e.stopPropagation(); copyLogs(); }}
            className="px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded"
          >
            📋 Copy
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); onClear?.(); }}
            className="px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      <div className="h-40 overflow-y-auto px-4 py-2 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-4">
            Логи появятся здесь при выполнении операций
          </div>
        ) : (
          logs.map((log, index) => (
            <div 
              key={index} 
              className={`flex items-start gap-2 py-0.5 ${
                log?.type === 'error' ? 'bg-red-900/20' : 'hover:bg-gray-700/30'
              }`}
            >
              <span className="text-gray-500 flex-shrink-0">{formatTime(log?.timestamp)}</span>
              <span className={`flex-shrink-0 ${getLogColor(log?.type)}`}>{getLogIcon(log?.type)}</span>
              <span className={getLogColor(log?.type)}>{log?.message || ''}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default LogsPanel;
