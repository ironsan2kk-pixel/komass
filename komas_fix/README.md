# KOMAS Dominant Presets Fix

## Problem

Dominant presets were not visible in the UI because:

1. **API endpoint missing**: Frontend called `/api/presets/dominant/list` but this endpoint didn't exist
2. **Routes not registered**: `preset_routes_v3.py` was not registered in `main.py`
3. **Presets not generated**: Dominant presets were never generated in the database

## Solution

This fix includes:

1. **Updated `preset_routes_v3.py`**:
   - Added `/api/presets/dominant/list` convenience endpoint
   - Added `/api/presets/trg/list` convenience endpoint
   - Fixed import error handling
   - Added proper DB function aliases

2. **Updated `main.py`**:
   - Added registration of `preset_routes_v3` router
   - Updated version to 4.0

3. **Preset generator script**:
   - Python script to generate Dominant presets
   - Batch file to run the generator

## Installation

### Step 1: Install the fix

```batch
install_fix.bat
```

This copies the updated files to the backend.

### Step 2: Restart the server

Stop and start the backend server to load the new routes.

### Step 3: Generate Dominant presets

Option A: Run the batch file:
```batch
run_generate_dominant.bat
```

Option B: Use the API:
- POST `/api/presets/generate/dominant`
- Or with SSE streaming: GET `/api/presets/generate/dominant-stream`

Option C: Use the Python script directly:
```bash
cd backend
python -c "from app.presets import DominantPreset; list(DominantPreset.generate_system_presets())"
```

## Verification

After installation, check:

1. Open the UI, switch to Dominant indicator
2. The preset selector should show presets
3. Check logs for "Loaded: Preset routes v3"

## API Endpoints

New endpoints added:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/presets/dominant/list` | GET | List Dominant presets |
| `/api/presets/trg/list` | GET | List TRG presets |
| `/api/presets/generate/dominant` | POST | Generate Dominant presets |
| `/api/presets/generate/dominant-stream` | GET | Generate with SSE progress |

## Files Changed

- `backend/app/main.py` - Added preset_routes_v3 registration
- `backend/app/api/preset_routes_v3.py` - Added dominant/list endpoint

## Git Commit

```
fix(presets): Add dominant/list endpoint and register preset_routes_v3

- Add /api/presets/dominant/list convenience endpoint
- Add /api/presets/trg/list convenience endpoint  
- Register preset_routes_v3 in main.py
- Fix DB function import names
- Add preset generator script

Hotfix: Dominant presets not visible in UI
```
