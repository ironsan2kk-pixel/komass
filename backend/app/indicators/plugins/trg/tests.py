"""
Komas Trading System - TRG Plugin Tests
========================================

Тесты для TRG индикатора и генератора сигналов.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Fix import path - get current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add current directory to path for relative imports
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def create_test_data(n_candles: int = 500, trend: str = "mixed") -> pd.DataFrame:
    """
    Создаёт тестовые OHLCV данные.
    
    Args:
        n_candles: Количество свечей
        trend: "up", "down", "mixed"
        
    Returns:
        DataFrame с OHLCV
    """
    np.random.seed(42)
    
    # Базовая цена
    base_price = 100.0
    
    # Генерируем движение цены с сильными трендами
    close = np.zeros(n_candles)
    close[0] = base_price
    
    # Create trending data with reversals
    trend_period = 50
    for i in range(1, n_candles):
        period_num = i // trend_period
        if trend == "up":
            t = 0.008
        elif trend == "down":
            t = -0.008
        else:  # mixed
            if period_num % 2 == 0:
                t = 0.012  # Strong up
            else:
                t = -0.015  # Strong down
        
        noise = np.random.randn() * 0.005
        close[i] = close[i-1] * (1 + t + noise)
    
    # OHLC
    high = close * (1 + np.abs(np.random.randn(n_candles)) * 0.01)
    low = close * (1 - np.abs(np.random.randn(n_candles)) * 0.01)
    open_prices = np.roll(close, 1)
    open_prices[0] = base_price
    
    # Volume
    volume = np.random.randint(1000, 10000, n_candles).astype(float)
    
    # DateTime index
    dates = pd.date_range(
        start=datetime.now() - timedelta(hours=n_candles),
        periods=n_candles,
        freq="1h"
    )
    
    return pd.DataFrame({
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)


def test_trg_indicator():
    """Тест TRGIndicator"""
    print("\n" + "="*60)
    print("TEST: TRGIndicator")
    print("="*60)
    
    # Import from current directory
    from indicator import TRGIndicator, TRGParameters, TrendDirection
    
    # 1. Создание индикатора
    print("\n1. Creating indicator...")
    indicator = TRGIndicator(atr_length=20, multiplier=1.5)
    print(f"   ✓ Created: {indicator}")
    
    # 2. Валидация параметров
    print("\n2. Parameter validation...")
    params = TRGParameters(atr_length=45, multiplier=4.0)
    is_valid, errors = params.validate()
    assert is_valid, f"Validation failed: {errors}"
    print(f"   ✓ Parameters valid")
    
    # 3. Создание тестовых данных
    print("\n3. Creating test data...")
    df = create_test_data(500, trend="mixed")
    print(f"   ✓ Created {len(df)} candles")
    print(f"   Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 4. Расчёт индикатора
    print("\n4. Calculating TRG...")
    result = indicator.calculate(df)
    print(f"   ✓ Calculated")
    print(f"   - Total candles: {result.total_candles}")
    print(f"   - Trend changes: {result.trend_changes}")
    print(f"   - Long periods: {result.long_periods}")
    print(f"   - Short periods: {result.short_periods}")
    
    # 5. Проверка колонок
    print("\n5. Checking output columns...")
    required_cols = ["trg_upper", "trg_lower", "trg_line", "trg_trend", "trg_atr"]
    for col in required_cols:
        assert col in result.df.columns, f"Missing column: {col}"
    print(f"   ✓ All columns present: {required_cols}")
    
    # 6. Проверка значений
    print("\n6. Checking values...")
    assert not result.df["trg_upper"].isna().all(), "trg_upper is all NaN"
    assert not result.df["trg_lower"].isna().all(), "trg_lower is all NaN"
    assert result.df["trg_trend"].isin([TrendDirection.SHORT, TrendDirection.NONE, TrendDirection.LONG]).all()
    print(f"   ✓ Values are valid")
    print(f"   Trend distribution: {result.df['trg_trend'].value_counts().to_dict()}")
    
    # 7. Инкрементальный расчёт
    print("\n7. Testing incremental calculation...")
    last_values = {
        "trg_upper": result.last_upper,
        "trg_lower": result.last_lower,
        "trg_trend": result.last_trend,
        "trg_atr": result.last_atr,
        "prev_close": float(result.df["close"].iloc[-1]),
    }
    new_candle = {
        "open": result.df["close"].iloc[-1],
        "high": result.df["close"].iloc[-1] * 1.005,
        "low": result.df["close"].iloc[-1] * 0.995,
        "close": result.df["close"].iloc[-1] * 1.002,
        "volume": 5000.0,
    }
    new_values = indicator.calculate_incremental(new_candle, last_values)
    assert "trg_upper" in new_values
    assert "trg_trend" in new_values
    print(f"   ✓ Incremental calculation works")
    
    print("\n✅ TRGIndicator: ALL TESTS PASSED")
    return True


def test_signal_generator():
    """Тест TRGSignalGenerator"""
    print("\n" + "="*60)
    print("TEST: TRGSignalGenerator")
    print("="*60)
    
    from signals import (
        TRGSignalGenerator, 
        SignalGeneratorConfig,
        SignalType,
    )
    
    # 1. Создание генератора
    print("\n1. Creating signal generator...")
    generator = TRGSignalGenerator(atr_length=20, multiplier=1.5)
    print(f"   ✓ Created: {generator}")
    
    # 2. С конфигом
    print("\n2. Creating with config...")
    config = SignalGeneratorConfig(
        atr_length=20,
        multiplier=1.5,
        use_supertrend=True,
        use_rsi_filter=True,
    )
    generator_with_filters = TRGSignalGenerator.from_config(config)
    print(f"   ✓ Created: {generator_with_filters}")
    
    # 3. Генерация сигналов
    print("\n3. Generating signals...")
    df = create_test_data(500, trend="mixed")
    result = generator.generate(df)
    print(f"   ✓ Generated")
    print(f"   - Total signals: {result.total_signals}")
    print(f"   - Long signals: {result.long_signals}")
    print(f"   - Short signals: {result.short_signals}")
    
    # 4. Проверка сигналов
    print("\n4. Checking signals...")
    assert "signal" in result.df.columns
    signal_values = result.df["signal"].unique()
    print(f"   ✓ Signal values: {list(signal_values)}")
    
    # 5. Генерация с фильтрами
    print("\n5. Generating with filters...")
    result_filtered = generator_with_filters.generate(df)
    print(f"   - Total signals: {result_filtered.total_signals}")
    print(f"   - Filtered out: {result_filtered.filtered_signals}")
    
    # 6. Проверка фильтрации
    print("\n6. Checking filter columns...")
    if config.use_supertrend:
        assert "supertrend" in result_filtered.df.columns
        print(f"   ✓ SuperTrend column present")
    if config.use_rsi_filter:
        assert "rsi" in result_filtered.df.columns
        print(f"   ✓ RSI column present")
    
    # 7. Получение текущего сигнала
    print("\n7. Getting current signal...")
    current = generator.get_current_signal(result.df)
    if current:
        print(f"   ✓ Current signal: {current.type.name} at {current.price:.2f}")
    else:
        print(f"   ✓ No current signal (expected)")
    
    print("\n✅ TRGSignalGenerator: ALL TESTS PASSED")
    return True


def test_compatibility():
    """Тест совместимости со старым API"""
    print("\n" + "="*60)
    print("TEST: Backward Compatibility")
    print("="*60)
    
    from indicator import calculate_trg
    from signals import generate_signals, count_signals
    
    # 1. calculate_trg function
    print("\n1. Testing calculate_trg...")
    df = create_test_data(200)
    df_result = calculate_trg(df, atr_length=20, multiplier=1.5)
    assert "trg_trend" in df_result.columns
    print(f"   ✓ calculate_trg works")
    
    # 2. generate_signals function
    print("\n2. Testing generate_signals...")
    df_signals = generate_signals(df, atr_length=20, multiplier=1.5)
    assert "signal" in df_signals.columns
    print(f"   ✓ generate_signals works")
    
    # 3. count_signals function
    print("\n3. Testing count_signals...")
    counts = count_signals(df_signals)
    assert "long" in counts
    assert "short" in counts
    print(f"   ✓ count_signals: {counts}")
    
    print("\n✅ Backward Compatibility: ALL TESTS PASSED")
    return True


def test_plugin_info():
    """Тест метаинформации плагина"""
    print("\n" + "="*60)
    print("TEST: Plugin Info")
    print("="*60)
    
    # Import directly - we're in the right directory
    from indicator import TRGIndicator
    from signals import TRGSignalGenerator
    
    # 1. Plugin info - import __init__ directly
    print("\n1. Getting plugin info...")
    
    # Read plugin info from manifest.json instead
    import json
    manifest_path = os.path.join(current_dir, "manifest.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    assert manifest["id"] == "trg"
    print(f"   ✓ Plugin ID: {manifest['id']}")
    print(f"   ✓ Version: {manifest['version']}")
    
    # 2. Entry points
    print("\n2. Testing entry points...")
    assert TRGIndicator.__name__ == "TRGIndicator"
    assert TRGSignalGenerator.__name__ == "TRGSignalGenerator"
    print(f"   ✓ Indicator class: {TRGIndicator.__name__}")
    print(f"   ✓ Signal class: {TRGSignalGenerator.__name__}")
    
    # 3. Test creating instances
    print("\n3. Creating instances...")
    indicator = TRGIndicator(atr_length=45, multiplier=4.0)
    generator = TRGSignalGenerator(atr_length=45, multiplier=4.0)
    print(f"   ✓ Indicator: {indicator}")
    print(f"   ✓ Generator: {generator}")
    
    print("\n✅ Plugin Info: ALL TESTS PASSED")
    return True


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("KOMAS TRG PLUGIN - TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Plugin directory: {current_dir}")
    
    # Change to script directory for relative imports
    original_dir = os.getcwd()
    os.chdir(current_dir)
    
    tests = [
        ("TRGIndicator", test_trg_indicator),
        ("TRGSignalGenerator", test_signal_generator),
        ("Backward Compatibility", test_compatibility),
        ("Plugin Info", test_plugin_info),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, "✅ PASSED" if result else "❌ FAILED"))
        except Exception as e:
            results.append((name, f"❌ ERROR: {e}"))
            import traceback
            traceback.print_exc()
    
    # Restore original directory
    os.chdir(original_dir)
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, status in results:
        print(f"  {name}: {status}")
        if "PASSED" not in status:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
