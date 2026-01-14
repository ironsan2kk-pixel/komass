# 🚀 KOMAS v4.0 - Быстрый старт

> **⚠️ ВАЖНО: PAPER TRADING ONLY**
> Все операции выполняются только с историческими данными для бэктестинга.

## 📋 Требования

- Python 3.11+
- Node.js 18+
- 2GB RAM минимум

---

## 🔧 Установка и запуск

### 1️⃣ Backend (API сервер)

```bash
# Перейти в папку backend
cd backend

# Установить зависимости
python3 -m pip install --user \
  fastapi==0.104.1 \
  uvicorn[standard]==0.24.0 \
  sqlalchemy==2.0.23 \
  aiosqlite==0.19.0 \
  pandas==2.1.4 \
  numpy==1.26.2 \
  pyarrow==14.0.2 \
  httpx==0.25.2 \
  aiohttp==3.9.1 \
  websockets==12.0 \
  ccxt==4.1.89 \
  apscheduler==3.10.4 \
  python-telegram-bot==20.7 \
  beautifulsoup4==4.12.2 \
  lxml==4.9.4 \
  python-dotenv==1.0.0 \
  pydantic==2.5.2 \
  pydantic-settings==2.1.0 \
  plotly==5.18.0 \
  python-multipart==0.0.6

# Запустить сервер
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Проверка:** Откройте http://localhost:8000/health - должен вернуть `{"status":"healthy"}`

---

### 2️⃣ Frontend (React приложение)

```bash
# Перейти в папку frontend
cd frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev
```

**Проверка:** Откройте http://localhost:5173 - должна загрузиться главная страница KOMAS

---

## ✅ Проверка работоспособности

### Backend запущен:
```bash
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"healthy","app":"Komas Trading Server","version":"4.0",...}
```

### Боты API работает:
```bash
curl http://localhost:8000/api/bots/
# Ожидаемый ответ: {"bots":[...],"total":...}
```

### Логи backend:
```bash
tail -f backend/logs/komas_$(date +%Y-%m-%d).log
```

---

## 🐛 Решение проблем

### ❌ "No module named uvicorn"
**Причина:** Пакеты не установлены или установлены для другой версии Python
**Решение:**
```bash
python3 -m pip install --user uvicorn fastapi
```

### ❌ "Failed building wheel for ta, deap"
**Причина:** Старые версии пакетов с проблемами сборки
**Решение:** Установите основные пакеты без `ta` и `deap` (см. команду выше). Функционал бэктестинга будет работать, но некоторые индикаторы могут быть недоступны.

### ❌ Backend запущен, но frontend не подключается
**Причина:** Неверный API URL
**Решение:** Проверьте `frontend/.env` - должно быть `VITE_API_URL=http://localhost:8000`

### ❌ "Connection refused" при запросах к API
**Причина:** Backend не запущен
**Решение:** Запустите backend сервер (см. шаг 1️⃣)

---

## 📚 Дальнейшие шаги

1. **Загрузите исторические данные:**
   Страница `Data` → Выберите символ → Скачать данные

2. **Создайте пресет:**
   Страница `Presets` → Seed TRG/Dominant → Выберите пресет

3. **Запустите оптимизатор:**
   Страница `Optimizer` → Выберите пресеты → Запустить Multi-Pair

4. **Создайте бота:**
   Страница `Bots` → Создать → Выберите стратегию

---

## 📁 Структура проекта

```
komass/
├── backend/              # FastAPI сервер (Python)
│   ├── app/             # Код приложения
│   ├── data/            # Parquet файлы с данными
│   ├── logs/            # Логи сервера
│   └── requirements.txt # Зависимости Python
├── frontend/            # React приложение (Vite)
│   ├── src/            # Исходный код
│   └── package.json    # Зависимости Node.js
└── docs/               # Документация

```

---

## 🔐 Настройка API ключей (опционально)

> **⚠️ НАПОМИНАНИЕ:** API ключи НЕ используются для реальной торговли.
> Они нужны только для загрузки исторических данных с Binance.

1. Создайте API ключи на Binance (только чтение)
2. Перейдите в `Settings` → API Keys
3. Введите ключи (хранятся локально в браузере)

---

## 📞 Поддержка

- **Логи backend:** `backend/logs/komas_*.log`
- **Логи ошибок:** `backend/logs/errors_*.log`
- **Консоль браузера:** F12 → Console (для frontend ошибок)

---

*Создано: 14.01.2026*
*Версия: KOMAS v4.0*
*Режим: Paper Trading Only*
