# KOMAS Scripts Directory

Организованные скрипты для управления проектом KOMAS.

## 📁 Структура

```
scripts/
├── install/          # Скрипты установки зависимостей
│   ├── install_backend.bat
│   ├── install_frontend.bat
│   ├── install_core.bat
│   ├── install_*_deps.bat
│   └── reinstall.bat
│
├── tests/            # Скрипты запуска тестов
│   ├── run_tests.bat
│   ├── run_tests_quick.bat
│   ├── test_*.bat
│   └── verify_presets.bat
│
├── management/       # Скрипты управления системой
│   ├── start_all.bat
│   ├── start_backend.bat
│   ├── stop.bat
│   ├── stop_all.bat
│   ├── backup.bat
│   ├── update.bat
│   ├── hotfix.bat
│   ├── git_commit.bat
│   └── clear_calendar_cache.bat
│
└── utils/            # Утилиты и вспомогательные скрипты
    ├── apply_*.py/bat        # Патчи
    ├── fix_*.py              # Исправления
    ├── migrate_*.py/bat      # Миграции БД
    ├── seed_*.py/bat         # Наполнение данных
    └── patch_*.py            # Патчи кода
```

## 🚀 Основные команды

### Из корневой папки:

**Запуск системы:**
```bash
start.bat                  # Запуск всей системы (backend + frontend)
```

**Установка:**
```bash
install.bat                # Полная установка зависимостей
```

### Из scripts/:

**Установка компонентов:**
```bash
install/install_backend.bat      # Только backend
install/install_frontend.bat     # Только frontend
install/install_core.bat          # Только core компоненты
```

**Управление:**
```bash
management/start_all.bat          # Запуск backend + frontend
management/start_backend.bat      # Только backend
management/stop_all.bat           # Остановка всего
management/backup.bat             # Создать бэкап
```

**Тестирование:**
```bash
tests/run_tests.bat              # Все тесты
tests/run_tests_quick.bat        # Быстрые тесты
tests/test_dominant.bat          # Тесты Dominant индикатора
```

**Утилиты:**
```bash
utils/seed_presets.bat           # Наполнить пресеты
utils/migrate_presets.bat        # Миграция БД пресетов
```

## 📝 Примечания

- Все `.bat` файлы для Windows
- Python скрипты (`.py`) можно запускать напрямую
- Основные команды (start.bat, install.bat) находятся в корне проекта
