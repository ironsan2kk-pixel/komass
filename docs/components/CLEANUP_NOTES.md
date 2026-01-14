# Komas v3.0 - Cleanup Notes

## Файлы для удаления

### 1. Calendar.jsx
**Путь:** `frontend/src/pages/Calendar.jsx`  
**Причина:** Удалён по запросу пользователя в чате #18  
**Действие:** Удалить файл и убрать импорт из App.jsx

### 2. Старые версии Master Plan
**Путь:** Корень проекта  
**Файлы:**
- `KOMAS_MASTER_PLAN_v1*.md`
- `KOMAS_MASTER_PLAN_v2.0*.md` - `v2.11.md`

**Оставить:** Только `KOMAS_MASTER_PLAN_v2.12.md` (актуальная версия)

---

## Команды для cleanup

### Удаление Calendar.jsx
```batch
del frontend\src\pages\Calendar.jsx
```

### Очистка __pycache__
```batch
for /d /r "backend" %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"
```

### Очистка старых логов
```batch
forfiles /p "logs" /d -7 /c "cmd /c del @path"
```

---

## Git команды после cleanup

```batch
git add .
git commit -m "chore: cleanup - remove Calendar.jsx, update .gitignore"
git push origin main
```

---

## Проверка после cleanup

1. ✅ Проект запускается: `start.bat`
2. ✅ Все страницы работают (Indicator, Data, Signals, Bots, Settings)
3. ✅ Нет ошибок в консоли
4. ✅ API отвечает: http://localhost:8000/health
