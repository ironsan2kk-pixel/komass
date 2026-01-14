"""
Apply SSE GET endpoint patch for EventSource compatibility (FIXED)
==================================================================
Fixes the f-string syntax issue with Russian text
"""
import os
import re

def apply_patch():
    # Find indicator_routes.py
    possible_paths = [
        'backend/app/api/indicator_routes.py',
        'app/api/indicator_routes.py',
        'indicator_routes.py',
    ]
    
    filepath = None
    for p in possible_paths:
        if os.path.exists(p):
            filepath = p
            break
    
    if not filepath:
        print("ERROR: Cannot find indicator_routes.py")
        return False
    
    print(f"Found: {filepath}")
    
    # Check for backup first
    backup_path = filepath + '.bak'
    if os.path.exists(backup_path):
        print(f"Restoring from backup: {backup_path}")
        with open(backup_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # Check if patch already applied correctly
    if 'auto_optimize_stream_get' in content and 'SyntaxError' not in content:
        print("Patch already applied!")
        return True
    
    # Find the POST endpoint
    post_pattern = r'@router\.post\("/auto-optimize-stream"\)\nasync def auto_optimize_stream\('
    
    if not re.search(post_pattern, content):
        print("ERROR: Could not find POST endpoint pattern")
        return False
    
    # New GET endpoint code - FIXED f-string escaping
    get_endpoint = '''@router.get("/auto-optimize-stream")
async def auto_optimize_stream_get(
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    mode: str = "indicator",
    metric: str = "advanced",
    indicator_type: str = "trg",
    # TRG params
    i1: int = 45,
    i2: float = 4.0,
    # Dominant params
    dominant_sensitivity: int = 21,
    dominant_filter_type: int = 0,
    dominant_sl_mode: int = 0,
    # TP params
    tp_count: int = 4,
    tp1: float = 1.05,
    tp2: float = 1.95,
    tp3: float = 3.75,
    tp4: float = 6.0,
    # SL params
    sl: float = 6.0,
    sl_mode: str = "breakeven",
    # Filters
    use_st: bool = False,
    st_period: int = 10,
    st_mult: float = 3.0,
    use_rsi: bool = False,
    rsi_period: int = 14,
    use_adx: bool = False,
    adx_threshold: int = 25,
    # Other
    allow_reentry: bool = False,
    leverage: int = 1,
    use_commission: bool = False,
    commission: float = 0.1,
    # Full mode depth
    full_mode_depth: str = "medium",
    # Period
    start_date: str = None,
    end_date: str = None,
):
    """GET version of auto-optimize-stream for EventSource compatibility"""
    
    # Check if Dominant indicator - optimization not yet supported
    if indicator_type == "dominant":
        async def generate_dominant_error():
            error_msg = "Оптимизация для Dominant индикатора пока не реализована. Используйте пресеты из библиотеки (125 готовых конфигураций)."
            yield f"data: {json_lib.dumps({'type': 'error', 'message': error_msg})}" + chr(10) + chr(10)
        
        return StreamingResponse(
            generate_dominant_error(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    # Build settings object from query params
    settings = IndicatorSettings(
        symbol=symbol,
        timeframe=timeframe,
        indicator_type=indicator_type,
        trg_atr_length=i1,
        trg_multiplier=i2,
        dominant_sensitivity=dominant_sensitivity,
        dominant_filter_type=dominant_filter_type,
        dominant_sl_mode=dominant_sl_mode,
        tp_count=tp_count,
        tp1_percent=tp1,
        tp2_percent=tp2,
        tp3_percent=tp3,
        tp4_percent=tp4,
        sl_percent=sl,
        sl_trailing_mode=sl_mode,
        use_supertrend=use_st,
        supertrend_period=st_period,
        supertrend_multiplier=st_mult,
        use_rsi_filter=use_rsi,
        rsi_period=rsi_period,
        use_adx_filter=use_adx,
        adx_threshold=adx_threshold,
        allow_reentry=allow_reentry,
        leverage=leverage,
        use_commission=use_commission,
        commission_percent=commission,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Create request object and call POST version logic
    request = AutoOptimizeMode(
        mode=mode,
        settings=settings,
        metric=metric,
        full_mode_depth=full_mode_depth,
    )
    
    # Call the existing POST handler
    return await auto_optimize_stream(request)


'''
    
    # Insert GET endpoint before POST endpoint
    new_content = re.sub(
        post_pattern,
        get_endpoint + '@router.post("/auto-optimize-stream")\nasync def auto_optimize_stream(',
        content
    )
    
    if new_content == content:
        print("ERROR: Replacement failed")
        return False
    
    # Save new backup
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Backup saved: {backup_path}")
    
    # Write patched file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Patch applied successfully!")
    print("Restart backend to apply changes.")
    return True


if __name__ == '__main__':
    import sys
    if not apply_patch():
        sys.exit(1)
