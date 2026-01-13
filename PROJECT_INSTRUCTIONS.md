# KOMAS v4 â€” Project Instructions for Claude

> **GitHub:** https://github.com/ironsan2kk-pixel/komass  
> **Token:** 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  
> **Version:** 4.3  
> **Date:** 27.12.2025

---

## ðŸ”„ WORKFLOW

### At the START of EVERY chat:

```bash
# 1. Check latest commits
curl -H "Authorization: token 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" \
  "https://api.github.com/repos/ironsan2kk-pixel/komass/commits?per_page=5"

# 2. Check current tracker
curl -s "https://raw.githubusercontent.com/ironsan2kk-pixel/komass/main/docs/TRACKER.md"

# 3. If needed - check code files
curl -s "https://raw.githubusercontent.com/ironsan2kk-pixel/komass/main/backend/app/api/indicator_routes.py"
```

### At the END of EVERY chat:

```
1. ZIP archive with changes
2. Update docs/TRACKER.md
3. Update docs/CHAT_REFERENCE.md  
4. Git commit message (ENGLISH)
5. WRITE: "Next chat: #XX â€” Name"
6. Create CHAT_XX_INSTRUCTIONS.md for next chat
```

---

## ðŸ“ GITHUB STRUCTURE

```
komass/
â”œâ”€â”€ docs/                          # DYNAMIC DOCUMENTATION
â”‚   â”œâ”€â”€ TRACKER.md                 # Progress, checklists (update!)
â”‚   â”œâ”€â”€ CHAT_REFERENCE.md          # Chat history (update!)
â”‚   â””â”€â”€ MASTER_PLAN.md             # Full plan
â”‚
â”œâ”€â”€ backend/app/
â”‚   â”œâ”€â”€ main.py                    # FastAPI entry point
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ indicator_routes.py    # TRG logic (2000+ lines)
â”‚   â”‚   â””â”€â”€ data_routes.py         # Binance Futures API
â”‚   â””â”€â”€ indicators/                # NEW in v4
â”‚       â”œâ”€â”€ __init__.py
â”‚       â””â”€â”€ dominant.py            # Dominant indicator
â”‚
â”œâ”€â”€ frontend/src/
â”‚   â”œâ”€â”€ App.jsx                    # Navigation
â”‚   â”œâ”€â”€ api.js                     # API client
â”‚   â”œâ”€â”€ pages/                     # Pages
â”‚   â””â”€â”€ components/Indicator/      # Components
â”‚
â””â”€â”€ *.bat                          # Windows batch files
```

### âš ï¸ IGNORE (not in production):
```
backend/app/core/        # Era 1 experiment
backend/app/plugins/     # Not used
```

---

## ðŸ”§ QA CHECKPOINTS

**Every 4 chats â€” QA Checkpoint:**

```
#24 QA Checkpoint #2
#29 QA Checkpoint #3
#34 QA Checkpoint #4
...
```

### QA Checklist:
```markdown
**Logs:**
- [ ] Backend console
- [ ] Frontend DevTools
- [ ] Network failed requests

**Tests:**
- [ ] Data loading
- [ ] Indicator calculation
- [ ] Optimization
- [ ] All tabs

**Bugs:** record what found/fixed
```

---

## â›” CRITICAL RULES

### FORBIDDEN:
1. Remove functionality without explicit permission
2. Delete components/functions
3. Code as text in chat (ZIP only!)
4. Stubs â€” only full implementation
5. Russian text in .bat files
6. **Inline Python code in .bat files** (use separate .py files)

### REQUIRED:
1. **ZIP archives** for code delivery
2. `encoding='utf-8'` for `open()` on Windows
3. **Git commit in ENGLISH**
4. CRLF line endings for batch files
5. **Write next chat: #XX â€” Name**
6. Update docs/TRACKER.md and docs/CHAT_REFERENCE.md
7. Create CHAT_XX_INSTRUCTIONS.md for next chat

---

## ðŸ“ BAT FILE RULES

### âœ… CORRECT way:

```batch
@echo off
cd /d "%~dp0"
cd backend
call venv\Scripts\activate.bat
python "%~dp0run_tests.py"
pause
```

### âŒ WRONG way:

```batch
@echo off
REM DO NOT DO THIS - inline Python breaks!
python -c "
import pandas as pd
def test():
    print('test')
test()
"
```

### Rules:
1. **English only** in bat files
2. **No inline Python** â€” create separate .py file
3. **No chcp 65001** â€” causes issues
4. **Simple commands only** â€” complex logic in Python
5. **Use %~dp0** for script directory paths
6. **Always use call** for activate.bat

### Template for test bat files:

```batch
@echo off
echo ========================================
echo Running Tests
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%\app
python "%~dp0run_tests.py"

if %ERRORLEVEL% NEQ 0 (
    echo Tests FAILED
    pause
    exit /b 1
)

echo.
echo All tests passed!
pause
```

---

## ðŸ”§ KNOWN SOLUTIONS

| Problem | Solution |
|---------|----------|
| Duplicate timestamps | Deduplicate before sending |
| Mojibake | `encoding='utf-8'` |
| ProcessPoolExecutor crash | Imports at file start |
| White screen | `data?.field ?? default` |
| Bat with Russian | English text only |
| Bat inline Python fails | Separate .py file |

---

## ðŸ“ GIT COMMIT FORMAT

```
<type>: <description in English>

- Detail 1
- Detail 2

Chat #XX: <chat name>
```

Types: `feat`, `fix`, `refactor`, `docs`, `style`, `chore`

---

## ðŸŒ LINKS

| What | Where |
|------|-------|
| Repo | https://github.com/ironsan2kk-pixel/komass |
| Tracker | docs/TRACKER.md |
| History | docs/CHAT_REFERENCE.md |
| API docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| Crypto.com MCP | Format: BTC_USDT (with underscore) |

---

## ðŸ“¦ ZIP ARCHIVE STRUCTURE

Every chat produces a ZIP with:

```
komas_chatXX_name.zip
â”œâ”€â”€ backend/app/...      # Changed backend files
â”œâ”€â”€ frontend/src/...     # Changed frontend files  
â”œâ”€â”€ tests/               # Unit tests
â”œâ”€â”€ docs/                # Updated TRACKER.md, CHAT_REFERENCE.md
â”œâ”€â”€ *.bat                # Simple batch files
â””â”€â”€ *.py                 # Python scripts for complex logic
```

---

## ðŸŽ¯ CHAT INSTRUCTIONS TEMPLATE

Create `CHAT_XX_INSTRUCTIONS.md` for every next chat:

```markdown
# Chat #XX â€” Name

> **Phase:** X â€” Phase Name  
> **Previous:** #XX-1 Name âœ…  
> **Next:** #XX+1 Name

---

## ðŸŽ¯ GOAL

Brief description of what this chat accomplishes.

---

## ðŸ“‹ TASKS

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

---

## ðŸ“ FILES

```
path/to/files/
â”œâ”€â”€ file1.py      # Description
â””â”€â”€ file2.py      # Description
```

---

## ðŸ“ GIT COMMIT

```
type: description

- detail 1
- detail 2

Chat #XX: Name
```

---

**Next chat:** #XX+1 â€” Next Name
```

---

*Dynamic information â€” on GitHub in docs/*
*Version 4.3 â€” Added bat file rules*
