# Komas WebSocket Module — Real-time Data Streaming

## Обзор

Модуль WebSocket обеспечивает подключение к Binance WebSocket API для получения данных в реальном времени:
- Цены (ticker)
- Свечи (klines)
- Сделки (trades)
- Стакан (book ticker)

## Архитектура

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
├──────────────────────────────────────────────────────────────┤
│  EventSource → SSE Endpoints (/api/ws/sse/*)                 │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│                  FastAPI Backend                             │
├──────────────────────────────────────────────────────────────┤
│  api/ws.py → REST/SSE endpoints                              │
│       │                                                      │
│       ▼                                                      │
│  core/data/websocket.py → BinanceWebSocket client            │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│              Binance WebSocket Streams                       │
│  wss://stream.binance.com:9443/stream                        │
└──────────────────────────────────────────────────────────────┘
```

## Файлы

```
backend/app/
├── core/
│   └── data/
│       ├── __init__.py      # Экспорты модуля
│       └── websocket.py     # BinanceWebSocket клиент (~550 строк)
└── api/
    └── ws.py                # REST/SSE API (~450 строк)
```

## API Endpoints

### REST Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/ws/status` | Статус подключения |
| POST | `/api/ws/connect` | Подключиться к Binance |
| POST | `/api/ws/disconnect` | Отключиться |
| POST | `/api/ws/subscribe` | Подписаться на стримы |
| POST | `/api/ws/unsubscribe` | Отписаться |
| GET | `/api/ws/prices` | Кэшированные цены |
| GET | `/api/ws/streams` | Активные стримы |

### SSE Endpoints (Server-Sent Events)

| Endpoint | Параметры | Описание |
|----------|-----------|----------|
| `/api/ws/sse/prices` | `symbols=BTCUSDT,ETHUSDT` | Стрим цен |
| `/api/ws/sse/klines` | `symbol=BTCUSDT&interval=1m` | Стрим свечей |
| `/api/ws/sse/trades` | `symbol=BTCUSDT` | Стрим сделок |

### Quick Actions

| Endpoint | Описание |
|----------|----------|
| POST `/api/ws/quick/start-prices` | Быстрый старт стрима цен |
| POST `/api/ws/quick/stop` | Остановить всё |

## Использование

### Пример: Подключение и подписка

```bash
# 1. Подключиться
curl -X POST http://localhost:8000/api/ws/connect

# 2. Подписаться на цены
curl -X POST http://localhost:8000/api/ws/subscribe \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT"], "stream_type": "ticker"}'

# 3. Получить статус
curl http://localhost:8000/api/ws/status
```

### Пример: SSE во Frontend (JavaScript)

```javascript
// Подключение к SSE
const eventSource = new EventSource(
  'http://localhost:8000/api/ws/sse/prices?symbols=BTCUSDT,ETHUSDT'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Price update:', data);
  
  // data.type = 'ticker'
  // data.data.symbol = 'BTCUSDT'
  // data.data.price = 42500.50
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};

// Закрыть соединение
// eventSource.close();
```

### Пример: React Hook

```jsx
import { useEffect, useState } from 'react';

function useBinancePrice(symbols) {
  const [prices, setPrices] = useState({});
  
  useEffect(() => {
    const symbolsStr = symbols.join(',');
    const es = new EventSource(
      `http://localhost:8000/api/ws/sse/prices?symbols=${symbolsStr}`
    );
    
    es.onmessage = (event) => {
      const { data } = JSON.parse(event.data);
      setPrices(prev => ({
        ...prev,
        [data.symbol]: data.price
      }));
    };
    
    return () => es.close();
  }, [symbols.join(',')]);
  
  return prices;
}

// Использование
function PriceDisplay() {
  const prices = useBinancePrice(['BTCUSDT', 'ETHUSDT']);
  
  return (
    <div>
      <p>BTC: ${prices.BTCUSDT?.toFixed(2)}</p>
      <p>ETH: ${prices.ETHUSDT?.toFixed(2)}</p>
    </div>
  );
}
```

## Формат данных

### Ticker Update

```json
{
  "type": "ticker",
  "data": {
    "type": "ticker",
    "symbol": "BTCUSDT",
    "price": 42500.50,
    "open": 42000.00,
    "high": 43000.00,
    "low": 41500.00,
    "volume": 15000.5,
    "quote_volume": 637507500.0,
    "price_change": 500.50,
    "price_change_percent": 1.19,
    "timestamp": 1703520000000
  },
  "timestamp": "2025-12-25T12:00:00.000Z"
}
```

### Kline Update

```json
{
  "type": "kline",
  "data": {
    "type": "kline",
    "symbol": "BTCUSDT",
    "interval": "1m",
    "timestamp": 1703520000000,
    "open": 42500.00,
    "high": 42550.00,
    "low": 42480.00,
    "close": 42530.00,
    "volume": 125.5,
    "is_closed": true,
    "trades": 1250,
    "quote_volume": 5337415.00
  },
  "timestamp": "2025-12-25T12:01:00.000Z"
}
```

### Trade Update

```json
{
  "type": "trade",
  "data": {
    "type": "trade",
    "symbol": "BTCUSDT",
    "trade_id": 123456789,
    "price": 42500.00,
    "quantity": 0.5,
    "timestamp": 1703520000000,
    "is_buyer_maker": false
  },
  "timestamp": "2025-12-25T12:00:00.500Z"
}
```

## Особенности BinanceWebSocket

### Auto-Reconnect

- Автоматическое переподключение при обрыве
- Экспоненциальная задержка (1с → 60с max)
- Настраиваемое количество попыток

### Callbacks

```python
from app.core.data.websocket import BinanceWebSocket

ws = BinanceWebSocket()

# Глобальные callbacks
ws.on_connect(lambda: print("Connected!"))
ws.on_disconnect(lambda: print("Disconnected!"))
ws.on_error(lambda e: print(f"Error: {e}"))
ws.on_message(lambda data: print(f"Message: {data}"))

# Подключение
await ws.connect()

# Подписка с callback
async def handle_price(data):
    print(f"{data['symbol']}: ${data['price']}")

await ws.subscribe_ticker("BTCUSDT", handle_price)

# Запуск event loop
await ws.run_forever()
```

### Stream Types

| Type | Method | Описание |
|------|--------|----------|
| ticker | `subscribe_ticker()` | 24h ticker |
| mini_ticker | `subscribe_ticker(mini=True)` | Упрощённый ticker |
| kline | `subscribe_kline()` | Свечи |
| trade | `subscribe_trade()` | Отдельные сделки |
| agg_trade | `subscribe_trade(aggregate=True)` | Агрегированные сделки |
| book_ticker | `subscribe_book_ticker()` | Best bid/ask |

## Установка

```bash
# Запустить батник
install_ws_deps.bat

# Или вручную
pip install websockets>=12.0
```

## Тестирование

```bash
# Запустить сервер
start.bat

# Проверить статус
curl http://localhost:8000/api/ws/status

# Быстрый старт цен
curl -X POST "http://localhost:8000/api/ws/quick/start-prices?symbols=BTCUSDT,ETHUSDT"

# Открыть SSE в браузере
# http://localhost:8000/api/ws/sse/prices?symbols=BTCUSDT
```

## Troubleshooting

### Connection Failed

1. Проверить интернет соединение
2. Проверить доступность `stream.binance.com`
3. Попробовать VPN (некоторые регионы блокируют Binance)

### No Data Received

1. Проверить что подписка активна: `GET /api/ws/streams`
2. Проверить правильность символа (BTCUSDT, не BTC_USDT)
3. Проверить логи: `GET /api/logs/today`

### SSE Disconnects

- SSE имеет таймаут 30 секунд heartbeat
- При отключении — переподключиться автоматически
- Использовать EventSource reconnect в браузере
