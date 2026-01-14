"""
Patch: Add GET endpoint for SSE optimization
=============================================
The frontend uses EventSource which only supports GET requests.
This patch adds a GET version that parses query parameters.

Add this code BEFORE the existing @router.post("/auto-optimize-stream") decorator
"""

# ================================================================================
# ADD THIS NEW ENDPOINT BEFORE THE EXISTING POST VERSION
# ================================================================================

@router.get("/auto-optimize-stream")
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
            yield f"data: {json_lib.dumps({'type': 'error', 'message': 'Оптимизация для Dominant индикатора пока не реализована. Используйте пресеты из библиотеки (125 готовых конфигураций).'})}\n\n"
        
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


# ================================================================================
# KEEP THE EXISTING POST VERSION BELOW (unchanged)
# ================================================================================
