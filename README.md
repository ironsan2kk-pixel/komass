# KOMAS Chat #18: Data Period Selection

## What's New

This update adds the ability to select a date range for backtesting.

### Features

1. **Period Selection in Sidebar**
   - New "📅 Период данных" section in settings sidebar
   - Date picker inputs for start and end dates
   - Quick preset buttons: Всё, 1 год, 6 мес, 3 мес, 1 мес

2. **Backend Support**
   - API now returns `data_range` object with:
     - `available_start` / `available_end` - full data range
     - `used_start` / `used_end` - filtered range
     - `total_candles` / `used_candles` - candle counts

3. **Visual Indicators**
   - Period badge in header when custom range is set
   - Data range info in Stats panel
   - Available range shown in sidebar

### Files Modified

- `backend/app/api/indicator_routes.py` - Added data_range to response
- `frontend/src/components/Indicator/SettingsSidebar.jsx` - Added period selection UI
- `frontend/src/pages/Indicator.jsx` - Added dataRange state and display
- `frontend/src/components/Indicator/StatsPanel.jsx` - Added period info display

## Installation

1. Copy this folder to your komas_indicator directory
2. Run `install_chat18.bat`
3. Restart the server

## Testing

After installation, run `test_chat18.bat` to verify the changes work correctly.

## Rollback

If needed, restore files from `backup_chat18/` folder:
```batch
copy backup_chat18\indicator_routes.py.bak backend\app\api\indicator_routes.py
copy backup_chat18\SettingsSidebar.jsx.bak frontend\src\components\Indicator\SettingsSidebar.jsx
copy backup_chat18\Indicator.jsx.bak frontend\src\pages\Indicator.jsx
copy backup_chat18\StatsPanel.jsx.bak frontend\src\components\Indicator\StatsPanel.jsx
```

## Git Commit Message

```
feat(backtest): add data period selection for backtesting

- Add start_date/end_date inputs to sidebar
- Add quick period presets (1m, 3m, 6m, 1y, all)
- Return data_range info in API response
- Show used period in stats panel and header
- Validate date ranges on frontend

Chat #18
```
