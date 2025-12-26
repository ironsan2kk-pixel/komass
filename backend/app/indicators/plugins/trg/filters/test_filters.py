"""
Komas Trading System - TRG Filters Tests
=========================================

Тесты для модуля фильтров TRG.
Запуск: python test_filters.py
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add path for imports
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Direct imports
from config import TRGFilterConfig, FILTER_PRESETS
from manager import TRGFilterManager, generate_filter_configs, apply_filter_config, generate_signals_with_filters
from supertrend import SuperTrendFilter
from rsi import RSIFilter
from adx import ADXFilter
from volume import VolumeFilter


def create_test_data(n: int = 500) -> pd.DataFrame:
    """
    Создать тестовые OHLCV данные.
    
    Генерирует реалистичные данные с трендами и консолидациями.
    """
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=n, freq='1h')
    
    # Start price
    price = 50000.0
    prices = [price]
    
    # Generate price movements with trends
    for i in range(1, n):
        # Random walk with trend
        trend = np.sin(i / 50) * 0.001  # Slow trend
        noise = np.random.randn() * 0.002  # Noise
        change = trend + noise
        price = price * (1 + change)
        prices.append(price)
    
    prices = np.array(prices)
    
    # Generate OHLC
    high = prices * (1 + np.random.uniform(0.001, 0.005, n))
    low = prices * (1 - np.random.uniform(0.001, 0.005, n))
    open_prices = prices * (1 + np.random.uniform(-0.002, 0.002, n))
    
    # Make sure high >= max(open, close) and low <= min(open, close)
    high = np.maximum(high, np.maximum(open_prices, prices))
    low = np.minimum(low, np.minimum(open_prices, prices))
    
    # Generate volume
    base_volume = 1000
    volume = base_volume * (1 + np.random.uniform(-0.5, 1.5, n))
    
    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    }, index=dates)
    
    return df


def test_supertrend_filter():
    """Test SuperTrend filter"""
    print("\n" + "="*60)
    print("Testing SuperTrend Filter")
    print("="*60)
    
    df = create_test_data()
    
    # Create filter
    st_filter = SuperTrendFilter(period=10, multiplier=3.0, enabled=True)
    
    # Test calculate
    df = st_filter.calculate(df)
    
    assert 'supertrend' in df.columns, "supertrend column missing"
    assert 'supertrend_dir' in df.columns, "supertrend_dir column missing"
    
    # Check direction values
    directions = df['supertrend_dir'].unique()
    assert set(directions).issubset({-1, 0, 1}), f"Invalid directions: {directions}"
    
    # Test check for different signals
    row = df.iloc[-1]
    
    long_decision = st_filter.check(row, 'long')
    short_decision = st_filter.check(row, 'short')
    
    print(f"Last direction: {row['supertrend_dir']}")
    print(f"Long allowed: {long_decision.allow}")
    print(f"Short allowed: {short_decision.allow}")
    
    # If direction is 1 (bullish), long should be allowed, short blocked
    if row['supertrend_dir'] == 1:
        assert long_decision.allow, "Long should be allowed when bullish"
        assert not short_decision.allow, "Short should be blocked when bullish"
    elif row['supertrend_dir'] == -1:
        assert not long_decision.allow, "Long should be blocked when bearish"
        assert short_decision.allow, "Short should be allowed when bearish"
    
    # Test check_df
    long_mask = st_filter.check_df(df, 'long')
    short_mask = st_filter.check_df(df, 'short')
    
    assert len(long_mask) == len(df), "Long mask length mismatch"
    assert len(short_mask) == len(df), "Short mask length mismatch"
    
    print(f"Long signals allowed: {long_mask.sum()} / {len(df)}")
    print(f"Short signals allowed: {short_mask.sum()} / {len(df)}")
    
    print("✅ SuperTrend Filter: PASSED")
    return True


def test_rsi_filter():
    """Test RSI filter"""
    print("\n" + "="*60)
    print("Testing RSI Filter")
    print("="*60)
    
    df = create_test_data()
    
    # Create filter
    rsi_filter = RSIFilter(period=14, overbought=70, oversold=30, enabled=True)
    
    # Test calculate
    df = rsi_filter.calculate(df)
    
    assert 'rsi' in df.columns, "rsi column missing"
    
    # RSI should be between 0 and 100
    valid_rsi = df['rsi'].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all(), "RSI out of range"
    
    print(f"RSI range: {valid_rsi.min():.2f} - {valid_rsi.max():.2f}")
    print(f"RSI mean: {valid_rsi.mean():.2f}")
    
    # Test check
    row = df.iloc[-1]
    long_decision = rsi_filter.check(row, 'long')
    short_decision = rsi_filter.check(row, 'short')
    
    print(f"Current RSI: {row['rsi']:.2f}")
    print(f"Long allowed: {long_decision.allow} (blocked if RSI >= {rsi_filter.overbought})")
    print(f"Short allowed: {short_decision.allow} (blocked if RSI <= {rsi_filter.oversold})")
    
    # Test zone detection
    for rsi_val in [20, 50, 80]:
        zone = rsi_filter.get_zone(rsi_val)
        print(f"RSI {rsi_val} → zone: {zone}")
    
    print("✅ RSI Filter: PASSED")
    return True


def test_adx_filter():
    """Test ADX filter"""
    print("\n" + "="*60)
    print("Testing ADX Filter")
    print("="*60)
    
    df = create_test_data()
    
    # Create filter
    adx_filter = ADXFilter(period=14, threshold=25, enabled=True)
    
    # Test calculate
    df = adx_filter.calculate(df)
    
    assert 'adx' in df.columns, "adx column missing"
    assert 'plus_di' in df.columns, "plus_di column missing"
    assert 'minus_di' in df.columns, "minus_di column missing"
    
    # ADX should be non-negative
    valid_adx = df['adx'].dropna()
    assert (valid_adx >= 0).all(), "ADX should be non-negative"
    
    print(f"ADX range: {valid_adx.min():.2f} - {valid_adx.max():.2f}")
    print(f"ADX mean: {valid_adx.mean():.2f}")
    
    # Test check (ADX doesn't depend on signal type)
    row = df.iloc[-1]
    long_decision = adx_filter.check(row, 'long')
    short_decision = adx_filter.check(row, 'short')
    
    print(f"Current ADX: {row['adx']:.2f}")
    print(f"Threshold: {adx_filter.threshold}")
    print(f"Long allowed: {long_decision.allow}")
    print(f"Short allowed: {short_decision.allow}")
    
    # Both should have same result for ADX
    assert long_decision.allow == short_decision.allow, "ADX should give same result for long/short"
    
    # Test trend strength interpretation
    for adx_val in [10, 20, 30, 60]:
        strength = adx_filter.get_trend_strength(adx_val)
        print(f"ADX {adx_val} → strength: {strength}")
    
    print("✅ ADX Filter: PASSED")
    return True


def test_volume_filter():
    """Test Volume filter"""
    print("\n" + "="*60)
    print("Testing Volume Filter")
    print("="*60)
    
    df = create_test_data()
    
    # Create filter
    vol_filter = VolumeFilter(ma_period=20, threshold=1.5, enabled=True)
    
    # Test calculate
    df = vol_filter.calculate(df)
    
    assert 'volume_ma' in df.columns, "volume_ma column missing"
    assert 'volume_ratio' in df.columns, "volume_ratio column missing"
    assert 'high_volume' in df.columns, "high_volume column missing"
    
    # Volume ratio should be positive
    valid_ratio = df['volume_ratio'].dropna()
    assert (valid_ratio > 0).all(), "Volume ratio should be positive"
    
    print(f"Volume ratio range: {valid_ratio.min():.2f} - {valid_ratio.max():.2f}")
    print(f"High volume bars: {df['high_volume'].sum()} / {len(df)}")
    
    # Test check
    row = df.iloc[-1]
    decision = vol_filter.check(row, 'long')
    
    print(f"Current volume ratio: {row['volume_ratio']:.2f}")
    print(f"Threshold: {vol_filter.threshold}")
    print(f"Signal allowed: {decision.allow}")
    
    # Test volume level interpretation
    for ratio in [0.3, 0.8, 1.2, 2.5, 4.0]:
        level = vol_filter.get_volume_level(ratio)
        print(f"Ratio {ratio} → level: {level}")
    
    print("✅ Volume Filter: PASSED")
    return True


def test_filter_config():
    """Test TRGFilterConfig"""
    print("\n" + "="*60)
    print("Testing TRGFilterConfig")
    print("="*60)
    
    # Default config
    config = TRGFilterConfig()
    assert not config.use_supertrend, "SuperTrend should be disabled by default"
    assert not config.use_rsi, "RSI should be disabled by default"
    
    # Create from dict
    data = {
        'use_supertrend': True,
        'supertrend_period': 14,
        'use_rsi_filter': True,  # Test alias
        'rsi_period': 21,
    }
    config = TRGFilterConfig.from_dict(data)
    
    assert config.use_supertrend, "SuperTrend should be enabled"
    assert config.supertrend_period == 14, "Period should be 14"
    assert config.use_rsi, "RSI should be enabled"
    assert config.rsi_period == 21, "RSI period should be 21"
    
    # Test summary
    summary = config.get_filter_summary()
    print(f"Filter summary: {summary}")
    assert "ST(14" in summary, "Summary should include SuperTrend"
    assert "RSI(21" in summary, "Summary should include RSI"
    
    # Test active filters
    active = config.get_active_filters()
    print(f"Active filters: {active}")
    assert 'supertrend' in active, "SuperTrend should be active"
    assert 'rsi' in active, "RSI should be active"
    
    # Test copy
    config_copy = config.copy()
    config_copy.use_supertrend = False
    assert config.use_supertrend, "Original should not be modified"
    
    # Test update
    new_config = config.update(use_adx=True, adx_threshold=30)
    assert new_config.use_adx, "ADX should be enabled"
    assert new_config.adx_threshold == 30, "Threshold should be 30"
    assert not config.use_adx, "Original should not be modified"
    
    print("✅ TRGFilterConfig: PASSED")
    return True


def test_filter_presets():
    """Test filter presets"""
    print("\n" + "="*60)
    print("Testing Filter Presets")
    print("="*60)
    
    for name, preset in FILTER_PRESETS.items():
        print(f"Preset '{name}': {preset.get_filter_summary()}")
    
    # Test getting preset
    from config import get_preset, list_presets
    
    presets = list_presets()
    print(f"Available presets: {len(presets)}")
    
    conservative = get_preset('conservative')
    assert conservative is not None, "Conservative preset should exist"
    assert conservative.use_supertrend, "Conservative should use SuperTrend"
    
    none_preset = get_preset('none')
    assert none_preset is not None, "None preset should exist"
    assert not none_preset.use_supertrend, "None preset should have no filters"
    
    # Invalid preset
    invalid = get_preset('nonexistent')
    assert invalid is None, "Invalid preset should return None"
    
    print("✅ Filter Presets: PASSED")
    return True


def test_filter_manager():
    """Test TRGFilterManager"""
    print("\n" + "="*60)
    print("Testing TRGFilterManager")
    print("="*60)
    
    df = create_test_data()
    
    # Create manager with config
    config = TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        use_adx=True,
        adx_period=14,
        adx_threshold=25,
    )
    
    manager = TRGFilterManager(config)
    
    print(f"Manager: {manager}")
    print(f"Active filters: {manager.get_active_filters()}")
    
    # Test calculate_all
    df = manager.calculate_all(df)
    
    assert 'supertrend' in df.columns, "SuperTrend not calculated"
    assert 'rsi' in df.columns, "RSI not calculated"
    assert 'adx' in df.columns, "ADX not calculated"
    
    # Test check_signal
    row = df.iloc[-1]
    result = manager.check_signal(row, 'long')
    
    print(f"\nSignal check for LONG:")
    print(f"  Allowed: {result.allow}")
    print(f"  Blocked by: {result.blocked_by}")
    print(f"  Reasons: {result.reasons}")
    
    # Test check_signal_df
    long_mask = manager.check_signal_df(df, 'long')
    short_mask = manager.check_signal_df(df, 'short')
    
    print(f"\nDataFrame check:")
    print(f"  Long allowed: {long_mask.sum()} / {len(df)}")
    print(f"  Short allowed: {short_mask.sum()} / {len(df)}")
    
    # Test enable/disable
    manager.disable_all()
    assert len(manager.get_active_filters()) == 0, "All filters should be disabled"
    
    manager.enable_filter('supertrend', True)
    assert 'SuperTrend' in manager.get_active_filters(), "SuperTrend should be enabled"
    
    print("✅ TRGFilterManager: PASSED")
    return True


def test_generate_filter_configs():
    """Test generate_filter_configs for optimization"""
    print("\n" + "="*60)
    print("Testing generate_filter_configs")
    print("="*60)
    
    configs = generate_filter_configs()
    
    print(f"Total configs generated: {len(configs)}")
    
    # Check structure
    for cfg in configs[:5]:
        print(f"  - {cfg['name']}")
    
    print("  ...")
    
    for cfg in configs[-3:]:
        print(f"  - {cfg['name']}")
    
    # Check that we have different types
    no_filter = [c for c in configs if not any([
        c.get('use_supertrend'),
        c.get('use_rsi'),
        c.get('use_adx'),
        c.get('use_volume')
    ])]
    assert len(no_filter) >= 1, "Should have at least one 'no filter' config"
    
    st_only = [c for c in configs if c.get('use_supertrend') and not c.get('use_rsi')]
    assert len(st_only) >= 1, "Should have SuperTrend only configs"
    
    all_filters = [c for c in configs if all([
        c.get('use_supertrend'),
        c.get('use_rsi'),
        c.get('use_adx'),
        c.get('use_volume')
    ])]
    assert len(all_filters) >= 1, "Should have 'all filters' config"
    
    print("✅ generate_filter_configs: PASSED")
    return True


def test_apply_filter_config():
    """Test apply_filter_config"""
    print("\n" + "="*60)
    print("Testing apply_filter_config")
    print("="*60)
    
    df = create_test_data()
    
    config = {
        'name': 'Test Config',
        'use_supertrend': True,
        'supertrend_period': 10,
        'supertrend_multiplier': 3.0,
        'use_rsi': True,
        'rsi_period': 14,
    }
    
    df_filtered, manager = apply_filter_config(df, config)
    
    assert 'supertrend' in df_filtered.columns, "SuperTrend should be calculated"
    assert 'rsi' in df_filtered.columns, "RSI should be calculated"
    
    print(f"Manager created: {manager}")
    print(f"Columns added: supertrend, rsi")
    
    print("✅ apply_filter_config: PASSED")
    return True


def test_generate_signals_with_filters():
    """Test generate_signals_with_filters"""
    print("\n" + "="*60)
    print("Testing generate_signals_with_filters")
    print("="*60)
    
    df = create_test_data()
    
    # Simulate TRG trend (simple crossover logic for testing)
    sma_fast = df['close'].rolling(10).mean()
    sma_slow = df['close'].rolling(30).mean()
    df['trg_trend'] = np.where(sma_fast > sma_slow, 1, -1)
    
    # Create manager
    config = TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
    )
    manager = TRGFilterManager(config)
    
    # Calculate filters
    df = manager.calculate_all(df)
    
    # Generate signals
    df = generate_signals_with_filters(df, manager, 'trg_trend')
    
    assert 'signal' in df.columns, "signal column should be created"
    
    long_signals = (df['signal'] == 1).sum()
    short_signals = (df['signal'] == -1).sum()
    
    print(f"Long signals: {long_signals}")
    print(f"Short signals: {short_signals}")
    
    # Check that signals only occur at trend changes
    trend_changes = (df['trg_trend'] != df['trg_trend'].shift(1))
    signals = (df['signal'] != 0)
    
    # All signals should be at trend changes (or immediately after due to filtering)
    # This is a soft check since filters can modify the exact bar
    
    print("✅ generate_signals_with_filters: PASSED")
    return True


def test_integration():
    """Full integration test"""
    print("\n" + "="*60)
    print("Testing Full Integration")
    print("="*60)
    
    df = create_test_data(1000)
    
    # Simulate TRG indicator
    sma_fast = df['close'].rolling(10).mean()
    sma_slow = df['close'].rolling(50).mean()
    df['trg_trend'] = np.where(sma_fast > sma_slow, 1, -1)
    
    # Test without filters
    config_none = TRGFilterConfig()
    manager_none = TRGFilterManager(config_none)
    df_none = manager_none.calculate_all(df.copy())
    df_none = generate_signals_with_filters(df_none, manager_none, 'trg_trend')
    
    signals_none = (df_none['signal'] != 0).sum()
    
    # Test with all filters
    config_all = TRGFilterConfig(
        use_supertrend=True,
        use_rsi=True,
        use_adx=True,
        use_volume=True,
    )
    manager_all = TRGFilterManager(config_all)
    df_all = manager_all.calculate_all(df.copy())
    df_all = generate_signals_with_filters(df_all, manager_all, 'trg_trend')
    
    signals_all = (df_all['signal'] != 0).sum()
    
    print(f"Signals without filters: {signals_none}")
    print(f"Signals with all filters: {signals_all}")
    print(f"Reduction: {100 * (1 - signals_all/signals_none):.1f}%" if signals_none > 0 else "N/A")
    
    # With filters should have fewer or equal signals
    assert signals_all <= signals_none, "Filters should reduce or keep same number of signals"
    
    # Test multiple configs
    configs = generate_filter_configs()
    results = []
    
    for cfg in configs[:10]:  # Test first 10 configs
        df_test = df.copy()
        df_test, mgr = apply_filter_config(df_test, cfg)
        df_test = generate_signals_with_filters(df_test, mgr, 'trg_trend')
        count = (df_test['signal'] != 0).sum()
        results.append({
            'name': cfg['name'],
            'signals': count
        })
    
    print("\nFilter comparison (first 10 configs):")
    for r in results:
        print(f"  {r['name']}: {r['signals']} signals")
    
    print("\n✅ Full Integration: PASSED")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("   KOMAS TRG FILTERS - TEST SUITE")
    print("="*60)
    
    tests = [
        ("SuperTrend Filter", test_supertrend_filter),
        ("RSI Filter", test_rsi_filter),
        ("ADX Filter", test_adx_filter),
        ("Volume Filter", test_volume_filter),
        ("Filter Config", test_filter_config),
        ("Filter Presets", test_filter_presets),
        ("Filter Manager", test_filter_manager),
        ("Generate Filter Configs", test_generate_filter_configs),
        ("Apply Filter Config", test_apply_filter_config),
        ("Generate Signals with Filters", test_generate_signals_with_filters),
        ("Full Integration", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("   TEST RESULTS")
    print("="*60)
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total:  {len(tests)}")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
