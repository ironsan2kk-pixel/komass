# KOMAS Fixes v3.5.1

## Что изменено:

### 1. `backend/app/main.py`
- ✅ Добавлена загрузка **ВСЕХ** роутеров:
  - `data_routes` (был)
  - `indicator_routes` (был)
  - `signals` (ДОБАВЛЕН)
  - `plugins` (ДОБАВЛЕН)
  - `ws` (ДОБАВЛЕН)
  - `db_routes` (ДОБАВЛЕН)
- ✅ Версия обновлена до 3.5.1
- ✅ Добавлен endpoint `/api/info` для просмотра всех роутов
- ✅ Добавлен endpoint `/api/logs/download/{filename}`
- ✅ Добавлен endpoint `/api/logs/clear`

### 2. `.gitignore` (НОВЫЙ)
- Исключает `venv/` (296MB)
- Исключает `node_modules/` (103MB)
- Исключает `__pycache__/`
- Исключает логи и временные файлы

### 3. `backend/app/indicators/plugins/trg/ui_schema.py`
- Скопирован из `plugins/trg/ui_schema.py`
- Теперь в правильной папке

---

## Как применить:

1. Распакуй архив
2. Скопируй файлы с заменой:
   - `.gitignore` → в корень проекта
   - `backend/app/main.py` → с заменой
   - `backend/app/indicators/plugins/trg/ui_schema.py` → с заменой/добавлением

3. В GitHub Desktop увидишь изменения
4. Commit: "Fix: Add all API routes, .gitignore, ui_schema"
5. Push

---

## После применения:

Запусти сервер и проверь:
- http://localhost:8000/docs — все endpoints должны быть видны
- http://localhost:8000/api/info — список загруженных роутов
- http://localhost:8000/health — статус сервера
