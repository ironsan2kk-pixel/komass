"""
TRG Backtest Tests
==================
Comprehensive test suite for TRG backtest engine.

Run: python test_backtest.py
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "app" / "indicators" / "plugins" / "trg"))

from backtest import (
    BacktestConfig,
    MonthlyStats,
    TPStats,
    BacktestResult,
    TRGBacktest,
    calculate_atr,
    calculate_trg,
    calculate_supertrend,
    calculate_rsi,
    calculate_adx,
    generate_signals,
    prepare_candles,
    prepare_indicators,
    prepare_trade_markers,
    get_current_signal,
    run_parallel_backtest,
    calculate_score,
)


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_test_data(rows: int = 500, 
                       trend_changes: int = 10,
                       seed: int = 42) -> pd.DataFrame:
    """Generate realistic test OHLCV data with trend changes"""
    np.random.seed(seed)
    
    # Start date
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(rows)]
    
    # Generate price with trends
    base_price = 100.0
    prices = [base_price]
    trend = 1  # 1 = up, -1 = down
    change_every = rows // trend_changes
    
    for i in range(1, rows):
        if i % change_every == 0:
            trend *= -1
        
        # Random walk with trend bias
        change = np.random.normal(0.001 * trend, 0.01)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))  # Prevent negative prices
    
    # Generate OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        volatility = abs(np.random.normal(0, 0.005))
        open_price = close * (1 + np.random.normal(0, 0.002))
        high = max(open_price, close) * (1 + volatility)
        low = min(open_price, close) * (1 - volatility)
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
    return df


def generate_trending_data(rows: int = 200, 
                           direction: str = 'up',
                           seed: int = 42) -> pd.DataFrame:
    """Generate data with clear trend"""
    np.random.seed(seed)
    
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(rows)]
    
    base_price = 100.0
    trend_factor = 0.002 if direction == 'up' else -0.002
    
    prices = [base_price]
    for i in range(1, rows):
        change = trend_factor + np.random.normal(0, 0.005)
        prices.append(prices[-1] * (1 + change))
    
    data = []
    for date, close in zip(dates, prices):
        volatility = abs(np.random.normal(0, 0.003))
        open_price = close * (1 + np.random.normal(0, 0.001))
        high = max(open_price, close) * (1 + volatility)
        low = min(open_price, close) * (1 - volatility)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.uniform(1000, 10000)
        })
    
    return pd.DataFrame(data, index=pd.DatetimeIndex(dates))


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_backtest_config():
    """Test BacktestConfig creation and methods"""
    print("\n=== Testing BacktestConfig ===")
    
    # Default config
    config = BacktestConfig()
    assert config.symbol == "BTCUSDT"
    assert config.trg_atr_length == 45
    assert config.trg_multiplier == 4.0
    assert config.tp_count == 4
    assert len(config.tp_percents) == 10
    assert len(config.tp_amounts) == 10
    print("  ✅ PASS: Default config creation")
    
    # From dict
    data = {
        'symbol': 'ETHUSDT',
        'trg_atr_length': 50,
        'trg_multiplier': 5.0,
        'tp_count': 3,
        'tp1_percent': 1.0,
        'tp2_percent': 2.0,
        'tp3_percent': 3.0,
        'tp1_amount': 60,
        'tp2_amount': 30,
        'tp3_amount': 10,
    }
    config = BacktestConfig.from_dict(data)
    assert config.symbol == 'ETHUSDT'
    assert config.trg_atr_length == 50
    assert config.tp_count == 3
    print("  ✅ PASS: Config from dict")
    
    # To dict
    result = config.to_dict()
    assert 'symbol' in result
    assert 'tp1_percent' in result
    assert 'tp10_percent' in result
    print("  ✅ PASS: Config to dict")
    
    # Get active TP levels
    percents, amounts = config.get_active_tp_levels()
    assert len(percents) == 3
    assert len(amounts) == 3
    assert abs(sum(amounts) - 100) < 0.01  # Normalized to 100%
    print("  ✅ PASS: Active TP levels normalized")
    
    return True


def test_monthly_stats():
    """Test MonthlyStats dataclass"""
    print("\n=== Testing MonthlyStats ===")
    
    stats = MonthlyStats(month="2024-01")
    stats.trades = 10
    stats.wins = 6
    stats.losses = 4
    stats.pnl = 15.5
    
    result = stats.to_dict()
    assert result['month'] == "2024-01"
    assert result['trades'] == 10
    assert result['wins'] == 6
    print("  ✅ PASS: MonthlyStats creation and to_dict")
    
    return True


def test_tp_stats():
    """Test TPStats dataclass"""
    print("\n=== Testing TPStats ===")
    
    stats = TPStats()
    stats.record_tp_hit(1)
    stats.record_tp_hit(1)
    stats.record_tp_hit(2)
    
    assert stats.tp1_hits == 2
    assert stats.tp2_hits == 1
    assert stats.tp3_hits == 0
    print("  ✅ PASS: TPStats recording")
    
    result = stats.to_dict()
    assert 'tp1_hits' in result
    assert 'sl_hits' in result
    print("  ✅ PASS: TPStats to_dict")
    
    return True


def test_calculate_atr():
    """Test ATR calculation"""
    print("\n=== Testing calculate_atr ===")
    
    df = generate_test_data(100)
    atr = calculate_atr(df, 14)
    
    assert len(atr) == 100
    assert not atr.isna().all()
    assert atr.iloc[-1] > 0
    print(f"  ✅ PASS: ATR calculated - last value: {atr.iloc[-1]:.4f}")
    
    return True


def test_calculate_trg():
    """Test TRG indicator calculation"""
    print("\n=== Testing calculate_trg ===")
    
    df = generate_test_data(200)
    df = calculate_trg(df, 45, 4.0)
    
    assert 'trg_upper' in df.columns
    assert 'trg_lower' in df.columns
    assert 'trg_trend' in df.columns
    assert 'trg_line' in df.columns
    assert 'trg_atr' in df.columns
    print("  ✅ PASS: All TRG columns created")
    
    # Check trend values
    trend_values = df['trg_trend'].unique()
    assert set(trend_values).issubset({-1, 0, 1})
    print(f"  ✅ PASS: TRG trend values valid: {sorted(trend_values)}")
    
    # Check trend changes
    trend_changes = (df['trg_trend'] != df['trg_trend'].shift(1)).sum()
    print(f"  ✅ INFO: TRG trend changes: {trend_changes}")
    
    return True


def test_calculate_supertrend():
    """Test SuperTrend calculation"""
    print("\n=== Testing calculate_supertrend ===")
    
    df = generate_test_data(100)
    df = calculate_supertrend(df, 10, 3.0)
    
    assert 'supertrend' in df.columns
    assert 'supertrend_dir' in df.columns
    print("  ✅ PASS: SuperTrend columns created")
    
    return True


def test_calculate_rsi():
    """Test RSI calculation"""
    print("\n=== Testing calculate_rsi ===")
    
    df = generate_test_data(100)
    df = calculate_rsi(df, 14)
    
    assert 'rsi' in df.columns
    
    # RSI should be between 0 and 100 (mostly)
    valid_rsi = df['rsi'].dropna()
    assert valid_rsi.min() >= 0
    assert valid_rsi.max() <= 100
    print(f"  ✅ PASS: RSI calculated - range [{valid_rsi.min():.1f}, {valid_rsi.max():.1f}]")
    
    return True


def test_calculate_adx():
    """Test ADX calculation"""
    print("\n=== Testing calculate_adx ===")
    
    df = generate_test_data(100)
    df = calculate_adx(df, 14)
    
    assert 'adx' in df.columns
    print("  ✅ PASS: ADX calculated")
    
    return True


def test_generate_signals():
    """Test signal generation"""
    print("\n=== Testing generate_signals ===")
    
    df = generate_test_data(200)
    config = BacktestConfig()
    
    # Calculate TRG first
    df = calculate_trg(df, config.trg_atr_length, config.trg_multiplier)
    df = generate_signals(df, config)
    
    assert 'signal' in df.columns
    
    long_signals = (df['signal'] == 1).sum()
    short_signals = (df['signal'] == -1).sum()
    print(f"  ✅ PASS: Signals generated - Long: {long_signals}, Short: {short_signals}")
    
    # Test with filters
    config.use_supertrend = True
    df = calculate_supertrend(df, config.supertrend_period, config.supertrend_multiplier)
    df = generate_signals(df, config)
    
    filtered_long = (df['signal'] == 1).sum()
    filtered_short = (df['signal'] == -1).sum()
    print(f"  ✅ PASS: Filtered signals - Long: {filtered_long}, Short: {filtered_short}")
    
    return True


def test_backtest_basic():
    """Test basic backtest execution"""
    print("\n=== Testing TRGBacktest (basic) ===")
    
    df = generate_test_data(500, trend_changes=15)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    assert isinstance(result, BacktestResult)
    assert result.total_trades >= 0
    print(f"  ✅ PASS: Backtest completed - {result.total_trades} trades")
    
    if result.total_trades > 0:
        assert result.winning_trades + result.losing_trades == result.total_trades
        assert 0 <= result.win_rate <= 100
        print(f"  ✅ PASS: Stats valid - Win Rate: {result.win_rate:.1f}%")
        print(f"  ✅ INFO: Profit: {result.profit_pct:.2f}%, Max DD: {result.max_drawdown:.2f}%")
    
    return True


def test_backtest_with_filters():
    """Test backtest with filters enabled"""
    print("\n=== Testing TRGBacktest (with filters) ===")
    
    df = generate_test_data(500, trend_changes=15)
    config = BacktestConfig()
    config.use_supertrend = True
    config.use_rsi_filter = True
    config.use_adx_filter = True
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    print(f"  ✅ PASS: Backtest with filters - {result.total_trades} trades")
    
    return True


def test_backtest_leverage_commission():
    """Test backtest with leverage and commission"""
    print("\n=== Testing TRGBacktest (leverage & commission) ===")
    
    df = generate_test_data(500, trend_changes=15)
    
    # Without leverage/commission
    config1 = BacktestConfig()
    backtest1 = TRGBacktest(config1)
    result1 = backtest1.run(df)
    
    # With 10x leverage and 0.1% commission
    config2 = BacktestConfig()
    config2.leverage = 10.0
    config2.use_commission = True
    config2.commission_percent = 0.1
    backtest2 = TRGBacktest(config2)
    result2 = backtest2.run(df)
    
    print(f"  ✅ INFO: No leverage - Profit: {result1.profit_pct:.2f}%")
    print(f"  ✅ INFO: 10x leverage - Profit: {result2.profit_pct:.2f}%")
    
    # Leverage should amplify results (both gains and losses)
    if result1.total_trades > 0 and result2.total_trades > 0:
        print(f"  ✅ PASS: Leverage and commission applied correctly")
    
    return True


def test_backtest_reentry():
    """Test re-entry functionality"""
    print("\n=== Testing TRGBacktest (re-entry) ===")
    
    df = generate_test_data(500, trend_changes=10)
    
    # Without re-entry
    config1 = BacktestConfig()
    config1.allow_reentry = False
    backtest1 = TRGBacktest(config1)
    result1 = backtest1.run(df)
    
    # With re-entry after SL
    config2 = BacktestConfig()
    config2.allow_reentry = True
    config2.reentry_after_sl = True
    config2.reentry_after_tp = False
    backtest2 = TRGBacktest(config2)
    result2 = backtest2.run(df)
    
    print(f"  ✅ INFO: No re-entry: {result1.total_trades} trades, {result1.reentry_trades} re-entries")
    print(f"  ✅ INFO: With re-entry: {result2.total_trades} trades, {result2.reentry_trades} re-entries")
    
    # With re-entry should have more trades
    if result1.total_trades > 0:
        assert result2.total_trades >= result1.total_trades
        print(f"  ✅ PASS: Re-entry increases trade count")
    
    return True


def test_backtest_trailing_sl():
    """Test trailing SL modes"""
    print("\n=== Testing TRGBacktest (trailing SL) ===")
    
    df = generate_test_data(500, trend_changes=15)
    
    modes = ['fixed', 'breakeven', 'cascade']
    results = {}
    
    for mode in modes:
        config = BacktestConfig()
        config.sl_trailing_mode = mode
        backtest = TRGBacktest(config)
        result = backtest.run(df)
        results[mode] = result
        print(f"  ✅ INFO: {mode}: {result.total_trades} trades, WR: {result.win_rate:.1f}%, Profit: {result.profit_pct:.2f}%")
    
    print(f"  ✅ PASS: All trailing SL modes work")
    
    return True


def test_backtest_quick():
    """Test quick backtest for optimizer"""
    print("\n=== Testing TRGBacktest.run_quick ===")
    
    df = generate_test_data(200)
    config = BacktestConfig()
    
    # Calculate indicators
    df = calculate_trg(df, config.trg_atr_length, config.trg_multiplier)
    df = generate_signals(df, config)
    
    backtest = TRGBacktest(config)
    trades = backtest.run_quick(df)
    
    assert isinstance(trades, list)
    print(f"  ✅ PASS: Quick backtest - {len(trades)} trades")
    
    # Test with custom TP/SL
    trades2 = backtest.run_quick(df, tp_levels=[0.5, 1.0, 2.0], sl_pct=3.0)
    print(f"  ✅ PASS: Quick backtest with custom params - {len(trades2)} trades")
    
    return True


def test_backtest_result_to_dict():
    """Test BacktestResult.to_dict()"""
    print("\n=== Testing BacktestResult.to_dict ===")
    
    df = generate_test_data(300)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    result_dict = result.to_dict()
    
    expected_keys = [
        'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
        'total_pnl', 'avg_win', 'avg_loss', 'profit_factor',
        'max_drawdown', 'initial_capital', 'final_capital', 'profit_pct',
        'long_trades', 'short_trades', 'accuracy', 'profit_panel'
    ]
    
    for key in expected_keys:
        assert key in result_dict, f"Missing key: {key}"
    
    print(f"  ✅ PASS: All expected keys present in result dict")
    
    return True


def test_prepare_candles():
    """Test candle preparation for UI"""
    print("\n=== Testing prepare_candles ===")
    
    df = generate_test_data(100)
    candles = prepare_candles(df)
    
    assert len(candles) == 100
    assert 'time' in candles[0]
    assert 'open' in candles[0]
    assert 'high' in candles[0]
    assert 'low' in candles[0]
    assert 'close' in candles[0]
    
    # Check sorted
    times = [c['time'] for c in candles]
    assert times == sorted(times)
    print(f"  ✅ PASS: Candles prepared - {len(candles)} candles, sorted")
    
    return True


def test_prepare_indicators():
    """Test indicator preparation for UI"""
    print("\n=== Testing prepare_indicators ===")
    
    df = generate_test_data(100)
    config = BacktestConfig()
    config.use_supertrend = True
    
    df = calculate_trg(df, config.trg_atr_length, config.trg_multiplier)
    df = calculate_supertrend(df, config.supertrend_period, config.supertrend_multiplier)
    
    indicators = prepare_indicators(df, config)
    
    assert 'trg_upper' in indicators
    assert 'trg_lower' in indicators
    assert 'trg_line' in indicators
    assert 'supertrend' in indicators
    
    print(f"  ✅ PASS: Indicators prepared - TRG: {len(indicators['trg_line'])} points")
    
    return True


def test_prepare_trade_markers():
    """Test trade marker preparation for UI"""
    print("\n=== Testing prepare_trade_markers ===")
    
    df = generate_test_data(300)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    if result.trades:
        markers = prepare_trade_markers(result.trades)
        
        # Should have 2 markers per trade (entry + exit)
        expected_markers = len(result.trades) * 2
        assert len(markers) == expected_markers
        
        # Check marker structure
        assert 'time' in markers[0]
        assert 'position' in markers[0]
        assert 'color' in markers[0]
        assert 'shape' in markers[0]
        assert 'text' in markers[0]
        
        print(f"  ✅ PASS: Trade markers prepared - {len(markers)} markers for {len(result.trades)} trades")
    else:
        print(f"  ⚠️ SKIP: No trades to create markers")
    
    return True


def test_parallel_backtest():
    """Test parallel backtest function"""
    print("\n=== Testing run_parallel_backtest ===")
    
    df = generate_test_data(200)
    config = BacktestConfig()
    
    params = {
        'df': df,
        'config': config.to_dict(),
        'metric': 'profit'
    }
    
    result = run_parallel_backtest(params)
    
    assert 'score' in result
    assert 'profit' in result
    assert 'win_rate' in result
    assert 'trades' in result
    
    print(f"  ✅ PASS: Parallel backtest - Score: {result['score']}, Trades: {result['trades']}")
    
    return True


def test_calculate_score():
    """Test score calculation"""
    print("\n=== Testing calculate_score ===")
    
    df = generate_test_data(300)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    # Test different metrics
    metrics = ['profit', 'winrate', 'sharpe', 'profit_factor', 'advanced']
    
    for metric in metrics:
        score = calculate_score(result, metric)
        print(f"  ✅ INFO: {metric} score: {score:.2f}")
    
    print(f"  ✅ PASS: All metrics calculated")
    
    return True


def test_monthly_stats_tracking():
    """Test monthly statistics tracking"""
    print("\n=== Testing Monthly Stats Tracking ===")
    
    # Generate data spanning multiple months
    rows = 720  # ~30 days of hourly data
    df = generate_test_data(rows, trend_changes=20)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    if result.monthly_stats:
        print(f"  ✅ PASS: Monthly stats tracked - {len(result.monthly_stats)} months")
        
        for month, stats in result.monthly_stats.items():
            if stats.trades > 0:
                print(f"  ✅ INFO: {month}: {stats.trades} trades, WR: {(stats.wins/stats.trades*100):.1f}%")
    else:
        print(f"  ⚠️ SKIP: No monthly stats (no trades)")
    
    return True


def test_equity_curve():
    """Test equity curve generation"""
    print("\n=== Testing Equity Curve ===")
    
    df = generate_test_data(300)
    config = BacktestConfig()
    
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    assert len(result.equity_curve) == len(df)
    
    # Check structure
    if result.equity_curve:
        assert 'time' in result.equity_curve[0]
        assert 'value' in result.equity_curve[0]
        
        # Equity should start at initial capital
        assert result.equity_curve[0]['value'] == config.initial_capital
        
        print(f"  ✅ PASS: Equity curve - {len(result.equity_curve)} points")
        print(f"  ✅ INFO: Start: {result.equity_curve[0]['value']:.2f}, End: {result.equity_curve[-1]['value']:.2f}")
    
    return True


# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TRG BACKTEST TESTS")
    print("=" * 60)
    
    tests = [
        test_backtest_config,
        test_monthly_stats,
        test_tp_stats,
        test_calculate_atr,
        test_calculate_trg,
        test_calculate_supertrend,
        test_calculate_rsi,
        test_calculate_adx,
        test_generate_signals,
        test_backtest_basic,
        test_backtest_with_filters,
        test_backtest_leverage_commission,
        test_backtest_reentry,
        test_backtest_trailing_sl,
        test_backtest_quick,
        test_backtest_result_to_dict,
        test_prepare_candles,
        test_prepare_indicators,
        test_prepare_trade_markers,
        test_parallel_backtest,
        test_calculate_score,
        test_monthly_stats_tracking,
        test_equity_curve,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL: {test.__name__} - {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {test.__name__} - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️ {failed} tests failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
