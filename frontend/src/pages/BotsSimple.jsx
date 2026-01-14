/**
 * BotsSimple.jsx - Simplified Bots page for debugging
 */
import { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

export default function BotsSimple() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('[BotsSimple] Component mounted');
    fetchData();
  }, []);

  const fetchData = async () => {
    console.log('[BotsSimple] Fetching from:', `${API_URL}/api/bots/`);

    try {
      const response = await fetch(`${API_URL}/api/bots/`);
      console.log('[BotsSimple] Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json = await response.json();
      console.log('[BotsSimple] Data received:', json);

      setData(json);
      setError(null);
    } catch (err) {
      console.error('[BotsSimple] Error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
        <h1>Loading...</h1>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', color: 'white' }}>
        <h1 style={{ color: '#ef4444' }}>❌ Error</h1>
        <p style={{ fontSize: '18px' }}>{error}</p>
        <button
          onClick={fetchData}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', color: 'white' }}>
      <h1 style={{ color: '#22c55e' }}>✅ Success!</h1>
      <h2>Bots Data:</h2>
      <pre style={{
        background: '#2a2a2a',
        padding: '20px',
        borderRadius: '8px',
        overflow: 'auto',
        fontSize: '14px'
      }}>
        {JSON.stringify(data, null, 2)}
      </pre>

      {data && data.bots && data.bots.length > 0 && (
        <div style={{ marginTop: '30px' }}>
          <h3>Bot List:</h3>
          {data.bots.map(bot => (
            <div key={bot.id} style={{
              background: '#374151',
              padding: '15px',
              margin: '10px 0',
              borderRadius: '8px'
            }}>
              <div style={{ fontWeight: 'bold', fontSize: '18px' }}>{bot.name}</div>
              <div style={{ color: '#9ca3af' }}>Status: {bot.status}</div>
              <div style={{ color: '#9ca3af' }}>Capital: ${bot.current_capital}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
