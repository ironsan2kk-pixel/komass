# Komas Trading Server v3.0

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Node.js](https://img.shields.io/badge/node.js-20+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Platform](https://img.shields.io/badge/platform-Windows%20Server-lightgrey)

**Комплексная система для автоматизированной торговли криптовалютами**

[Установка](#-установка) • [Запуск](#-запуск) • [API](#-api-документация) • [Архитектура](#-архитектура)

</div>

---

## 📋 Описание

Komas Trading Server — это профессиональная торговая платформа, включающая:

- **TRG Indicator** — ATR-based тренд-детектор с 10 уровнями Take Profit
- **Backtesting Engine** — точный бэктест с учётом комиссий и проскальзывания
- **Multi-Mode Optimizer** — оптимизация параметров с многоядерной обработкой
- **Telegram Notifications** — уведомления о сигналах в реальном времени
- **Bots System** — автоматическое исполнение стратегий 24/7

### Ключевые возможности

| Функция | Описание |
|---------|----------|
| 📊 TRG Indicator | ATR-based индикатор (Pine Script → Python) |
| 📈 10 Take Profits | Каскадное закрытие позиций |
| 🛡️ 3 SL режима | Fixed / Breakeven / Cascade Trailing |
| 🔍 4 фильтра | SuperTrend, RSI, ADX, Volume |
| ⚡ SSE Streaming | Real-time прогресс оптимизации |
| 🤖 Telegram Bot | Уведомления в Cornix формате |
| 🚀 Multi-Core | ProcessPoolExecutor для оптимизации |

---

## 🔧 Требования

### Обязательные

| Компонент | Версия | Ссылка |
|-----------|--------|--------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Git | latest | [git-scm.com](https://git-scm.com/) |

### Рекомендуемые

- Windows 10/11 или Windows Server 2019+
- 8 GB RAM (16 GB для full optimization)
- SSD для быстрой работы с данными
- 4+ ядер CPU для многопоточной оптимизации

---

## 📦 Установка

### Быстрый старт

```batch
# Клонирование репозитория
git clone https://github.com/ironsan2kk-pixel/komass.git
cd komass

# Установка
install.bat
```

### Ручная установка

```batch
# Backend
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## 🚀 Запуск

### Батник (рекомендуется)

```batch
# Запуск
start.bat

# Остановка
stop.bat

# Перезапуск
stop.bat && start.bat
```

### Ручной запуск

**Terminal 1 - Backend:**
```batch
cd backend
call venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```batch
cd frontend
npm run dev
```

### URL-адреса

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## 🏗️ Архитектура

```
komas_indicator/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI приложение
│       ├── api/
│       │   ├── data_routes.py       # Binance API
│       │   ├── indicator_routes.py  # Индикатор + Бэктест
│       │   ├── signals_routes.py    # Сигналы
│       │   ├── bots_routes.py       # Боты
│       │   ├── settings_routes.py   # Настройки
│       │   └── notifications_routes.py  # Telegram
│       ├── core/
│       │   ├── config.py            # Конфигурация
│       │   ├── logger.py            # Логирование
│       │   ├── database.py          # SQLite
│       │   ├── data/                # Binance + WebSocket
│       │   ├── notifications/       # Telegram Bot
│       │   └── bots/                # Bot Manager
│       ├── indicators/
│       │   ├── base/                # Base classes
│       │   ├── loader.py            # Plugin Loader
│       │   └── registry.py          # Registry
│       └── plugins/
│           └── trg/                 # TRG Plugin
├── frontend/
│   └── src/
│       ├── App.jsx              # Навигация
│       ├── pages/
│       │   ├── Indicator.jsx        # Главная (6 вкладок)
│       │   ├── Data.jsx             # Данные
│       │   ├── Signals.jsx          # Сигналы
│       │   ├── Bots.jsx             # Боты
│       │   └── Settings.jsx         # Настройки
│       └── components/
│           └── Indicator/           # Компоненты
├── data/                    # Parquet файлы (OHLCV)
├── logs/                    # Логи приложения
├── backups/                 # Резервные копии
├── install.bat             
├── start.bat               
├── stop.bat                
├── reinstall.bat           
├── update.bat              
└── backup.bat              
```

---

## 📡 API Документация

### Data API (`/api/data/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/symbols` | Список доступных торговых пар |
| GET | `/timeframes` | Список таймфреймов |
| POST | `/download` | Загрузка данных с Binance |
| GET | `/available` | Загруженные файлы |

**Пример: Загрузка данных**
```bash
curl -X POST http://localhost:8000/api/data/download \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "timeframe": "1h", "days": 365}'
```

### Indicator API (`/api/indicator/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/calculate` | Расчёт индикатора + бэктест |
| GET | `/auto-optimize-stream` | SSE оптимизация |
| POST | `/heatmap` | Генерация heatmap i1/i2 |
| GET | `/ui-schema` | UI схема для фронтенда |

**Пример: Расчёт**
```bash
curl -X POST http://localhost:8000/api/indicator/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "trg_atr_length": 45,
    "trg_multiplier": 4.0,
    "tp_count": 4,
    "tp1_percent": 1.05,
    "tp1_amount": 50,
    "sl_percent": 6.0,
    "sl_trailing_mode": "breakeven"
  }'
```

### Signals API (`/api/signals/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список сигналов |
| POST | `/` | Создать сигнал |
| GET | `/active` | Активные сигналы |
| GET | `/stats` | Статистика |
| POST | `/export` | Экспорт CSV/JSON |

### Bots API (`/api/bots/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Список ботов |
| POST | `/` | Создать бота |
| POST | `/{id}/start` | Запустить бота |
| POST | `/{id}/stop` | Остановить бота |
| GET | `/{id}/stats` | Статистика бота |

### Notifications API (`/api/notifications/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/config` | Текущая конфигурация |
| POST | `/config` | Сохранить конфигурацию |
| POST | `/test` | Тест отправки |
| POST | `/start` | Запустить бота |
| POST | `/stop` | Остановить бота |

---

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `backend/.env`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Database
DATABASE_URL=sqlite:///./komas.db

# Binance (опционально, для приватных эндпоинтов)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Settings
LOG_LEVEL=INFO
DEBUG=false
```

### TRG Параметры по умолчанию

| Параметр | Default | Range | Описание |
|----------|---------|-------|----------|
| i1 (ATR Length) | 45 | 10-200 | Длина ATR |
| i2 (Multiplier) | 4.0 | 1-10 | Множитель |
| TP Count | 4 | 1-10 | Количество TP |
| SL Percent | 6.0 | 1-50 | Stop Loss % |
| SL Mode | breakeven | fixed/breakeven/cascade | Режим трейлинга |

---

## 🔧 Обслуживание

### Батники

| Батник | Описание |
|--------|----------|
| `install.bat` | Полная установка (venv + npm) |
| `start.bat` | Запуск backend + frontend |
| `stop.bat` | Остановка всех процессов |
| `reinstall.bat` | Переустановка зависимостей |
| `update.bat` | Обновление зависимостей |
| `backup.bat` | Бэкап данных и БД |

### Логирование

Логи сохраняются в `logs/`:
- `komas_YYYY-MM-DD.log` — все логи
- `errors_YYYY-MM-DD.log` — только ошибки

API для логов:
- `GET /api/logs/list` — список файлов
- `GET /api/logs/today?lines=100` — последние записи
- `GET /api/logs/errors?lines=50` — ошибки
- `GET /api/logs/clear?days=7` — очистка старых

---

## 🖼️ Скриншоты

### Главная страница (Indicator)
<!-- ![Indicator Page](docs/screenshots/indicator.png) -->
*6 вкладок: График, Статистика, Сделки, Месяцы, Оптимизация, Heatmap*

### Оптимизация
<!-- ![Optimization](docs/screenshots/optimization.png) -->
*SSE streaming с многоядерной обработкой*

### Heatmap
<!-- ![Heatmap](docs/screenshots/heatmap.png) -->
*Тепловая карта i1/i2 параметров*

---

## 📝 Changelog

### v3.0.0 (2025-12-26)
- ✅ TRG Plugin (indicator, trading, filters, optimizer, backtest)
- ✅ Multi-mode optimization (indicator, tp, sl, filters, full)
- ✅ SSE streaming для real-time прогресса
- ✅ Telegram уведомления (Simple/Cornix/Custom)
- ✅ Bots System (24/7 мониторинг)
- ✅ 6-tab Indicator UI
- ✅ Heatmap i1/i2 визуализация
- ✅ Full API documentation

---

## 🤝 Contributing

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing`)
5. Откройте Pull Request

---

## 📄 License

MIT License — см. файл [LICENSE](LICENSE)

---

## 👤 Author

**ironsan2kk-pixel**

- GitHub: [@ironsan2kk-pixel](https://github.com/ironsan2kk-pixel)

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

</div>
