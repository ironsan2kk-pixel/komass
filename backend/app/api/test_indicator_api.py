# -*- coding: utf-8 -*-
"""
Komas Trading Server - Indicator API Tests
==========================================
Comprehensive tests for indicator API endpoints.

Run with: python test_indicator_api.py
"""
import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd


def create_test_data(rows: int = 1000) -> pd.DataFrame:
    """Create synthetic OHLCV data for testing"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=rows, freq='1h')
    
    # Generate realistic price movement
    price = 50000  # Start at $50k
    prices = [price]
    
    for _ in range(rows - 1):
        change = np.random.normal(0, 0.002)  # 0.2% std dev
        price *= (1 + change)
        prices.append(price)
    
    prices = np.array(prices)
    
    # Generate OHLC from close
    opens = prices * (1 + np.random.uniform(-0.001, 0.001, rows))
    highs = np.maximum(opens, prices) * (1 + np.abs(np.random.normal(0, 0.003, rows)))
    lows = np.minimum(opens, prices) * (1 - np.abs(np.random.normal(0, 0.003, rows)))
    volumes = np.random.uniform(100, 10000, rows)
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes
    }, index=dates)
    
    return df


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, name: str):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("KOMAS INDICATOR API - TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    results = TestResults()
    
    # ========================================
    # Test 1: Import API module
    # ========================================
    print("=" * 40)
    print("TEST 1: Import API Module")
    print("=" * 40)
    
    try:
        from app.api.indicator import (
            router,
            IndicatorSettings,
            ReplayRequest,
            HeatmapRequest,
            AutoOptimizeRequest,
            calculate_atr,
            calculate_trg,
            calculate_supertrend,
            calculate_rsi,
            calculate_adx,
            generate_signals,
            run_backtest,
            calculate_statistics,
            prepare_candles,
            prepare_indicators,
            prepare_trade_markers,
            calculate_optimization_score,
            NUM_WORKERS,
        )
        results.add_pass("Import API module")
        results.add_pass(f"Router prefix: {router.prefix}")
        results.add_pass(f"NUM_WORKERS: {NUM_WORKERS}")
    except Exception as e:
        results.add_fail("Import API module", str(e))
        print(f"\nCannot continue without API module. Error: {e}")
        return results
    
    # ========================================
    # Test 2: Pydantic Models
    # ========================================
    print()
    print("=" * 40)
    print("TEST 2: Pydantic Models")
    print("=" * 40)
    
    try:
        # IndicatorSettings
        settings = IndicatorSettings()
        assert settings.symbol == "BTCUSDT"
        assert settings.timeframe == "1h"
        assert settings.trg_atr_length == 45
        assert settings.trg_multiplier == 4.0
        assert settings.tp_count == 4
        assert settings.sl_percent == 6.0
        results.add_pass("IndicatorSettings defaults")
        
        # Custom settings
        custom = IndicatorSettings(
            symbol="ETHUSDT",
            timeframe="4h",
            trg_atr_length=60,
            trg_multiplier=3.5,
            use_supertrend=True
        )
        assert custom.symbol == "ETHUSDT"
        assert custom.use_supertrend == True
        results.add_pass("IndicatorSettings custom")
        
        # ReplayRequest
        replay = ReplayRequest(settings=settings, step=100)
        assert replay.step == 100
        results.add_pass("ReplayRequest")
        
        # HeatmapRequest
        heatmap = HeatmapRequest(settings=settings, i1_min=20, i1_max=80)
        assert heatmap.i1_min == 20
        results.add_pass("HeatmapRequest")
        
        # AutoOptimizeRequest
        optimize = AutoOptimizeRequest(settings=settings, mode="indicator")
        assert optimize.mode == "indicator"
        results.add_pass("AutoOptimizeRequest")
        
    except Exception as e:
        results.add_fail("Pydantic Models", str(e))
    
    # ========================================
    # Test 3: Indicator Calculations
    # ========================================
    print()
    print("=" * 40)
    print("TEST 3: Indicator Calculations")
    print("=" * 40)
    
    df = create_test_data(500)
    
    try:
        # ATR
        atr = calculate_atr(df, 14)
        assert len(atr) == len(df)
        assert not atr.isna().all()
        results.add_pass(f"calculate_atr (mean: {atr.mean():.2f})")
        
        # TRG
        df_trg = calculate_trg(df.copy(), 45, 4.0)
        assert 'trg_atr' in df_trg.columns
        assert 'trg_upper' in df_trg.columns
        assert 'trg_lower' in df_trg.columns
        assert 'trg_line' in df_trg.columns
        assert 'trg_trend' in df_trg.columns
        trends = df_trg['trg_trend'].value_counts()
        results.add_pass(f"calculate_trg (trends: {dict(trends)})")
        
        # SuperTrend
        df_st = calculate_supertrend(df.copy(), 10, 3.0)
        assert 'supertrend' in df_st.columns
        assert 'st_trend' in df_st.columns
        results.add_pass("calculate_supertrend")
        
        # RSI
        df_rsi = calculate_rsi(df.copy(), 14)
        assert 'rsi' in df_rsi.columns
        rsi_valid = df_rsi['rsi'].dropna()
        assert rsi_valid.min() >= 0 and rsi_valid.max() <= 100
        results.add_pass(f"calculate_rsi (range: {rsi_valid.min():.1f}-{rsi_valid.max():.1f})")
        
        # ADX
        df_adx = calculate_adx(df.copy(), 14)
        assert 'adx' in df_adx.columns
        assert 'plus_di' in df_adx.columns
        assert 'minus_di' in df_adx.columns
        results.add_pass("calculate_adx")
        
    except Exception as e:
        results.add_fail("Indicator Calculations", str(e))
    
    # ========================================
    # Test 4: Signal Generation
    # ========================================
    print()
    print("=" * 40)
    print("TEST 4: Signal Generation")
    print("=" * 40)
    
    try:
        settings = IndicatorSettings()
        
        # Basic signals
        df_sig = calculate_trg(df.copy(), 45, 4.0)
        df_sig = generate_signals(df_sig, settings)
        
        assert 'signal' in df_sig.columns
        long_signals = (df_sig['signal'] == 1).sum()
        short_signals = (df_sig['signal'] == -1).sum()
        results.add_pass(f"Basic signals (long: {long_signals}, short: {short_signals})")
        
        # With SuperTrend filter
        settings_st = IndicatorSettings(use_supertrend=True)
        df_sig_st = calculate_trg(df.copy(), 45, 4.0)
        df_sig_st = calculate_supertrend(df_sig_st, 10, 3.0)
        df_sig_st = generate_signals(df_sig_st, settings_st)
        
        long_filtered = (df_sig_st['signal'] == 1).sum()
        short_filtered = (df_sig_st['signal'] == -1).sum()
        results.add_pass(f"SuperTrend filtered (long: {long_filtered}, short: {short_filtered})")
        
        # With RSI filter
        settings_rsi = IndicatorSettings(use_rsi_filter=True)
        df_sig_rsi = calculate_trg(df.copy(), 45, 4.0)
        df_sig_rsi = calculate_rsi(df_sig_rsi, 14)
        df_sig_rsi = generate_signals(df_sig_rsi, settings_rsi)
        results.add_pass("RSI filtered signals")
        
    except Exception as e:
        results.add_fail("Signal Generation", str(e))
    
    # ========================================
    # Test 5: Backtest Engine
    # ========================================
    print()
    print("=" * 40)
    print("TEST 5: Backtest Engine")
    print("=" * 40)
    
    try:
        settings = IndicatorSettings(
            initial_capital=10000,
            tp_count=4,
            sl_percent=6.0,
            leverage=1.0
        )
        
        df_bt = calculate_trg(df.copy(), 45, 4.0)
        df_bt = generate_signals(df_bt, settings)
        
        trades, equity, tp_stats, monthly, param_changes = run_backtest(df_bt, settings)
        
        assert isinstance(trades, list)
        assert isinstance(equity, list)
        assert isinstance(tp_stats, dict)
        assert isinstance(monthly, list)
        
        results.add_pass(f"Backtest completed (trades: {len(trades)})")
        
        if trades:
            # Check trade structure
            trade = trades[0]
            assert 'id' in trade
            assert 'entry_time' in trade
            assert 'exit_time' in trade
            assert 'direction' in trade
            assert 'pnl' in trade
            results.add_pass("Trade structure valid")
            
            # Check equity curve
            assert len(equity) > 0
            assert 'time' in equity[0]
            assert 'value' in equity[0]
            results.add_pass(f"Equity curve (points: {len(equity)})")
            
            # Statistics
            stats = calculate_statistics(trades, equity, settings, monthly)
            assert 'total_trades' in stats
            assert 'win_rate' in stats
            assert 'profit_factor' in stats
            assert 'total_pnl' in stats
            results.add_pass(f"Statistics (WR: {stats['win_rate']}%, PF: {stats['profit_factor']})")
        else:
            results.add_pass("No trades generated (may be due to test data)")
        
    except Exception as e:
        results.add_fail("Backtest Engine", str(e))
    
    # ========================================
    # Test 6: Data Helpers
    # ========================================
    print()
    print("=" * 40)
    print("TEST 6: Data Helpers")
    print("=" * 40)
    
    try:
        # Prepare candles
        candles = prepare_candles(df)
        assert isinstance(candles, list)
        assert len(candles) == len(df)
        assert 'time' in candles[0]
        assert 'open' in candles[0]
        assert 'high' in candles[0]
        assert 'low' in candles[0]
        assert 'close' in candles[0]
        results.add_pass(f"prepare_candles ({len(candles)} candles)")
        
        # Prepare indicators
        df_ind = calculate_trg(df.copy(), 45, 4.0)
        df_ind = generate_signals(df_ind, IndicatorSettings())
        indicators = prepare_indicators(df_ind, IndicatorSettings())
        
        assert isinstance(indicators, dict)
        assert 'trg' in indicators
        assert 'signals' in indicators
        results.add_pass(f"prepare_indicators (keys: {list(indicators.keys())})")
        
        # Prepare trade markers
        if trades:
            markers = prepare_trade_markers(trades)
            assert isinstance(markers, list)
            # Each trade has entry + exit marker
            assert len(markers) >= len(trades)
            results.add_pass(f"prepare_trade_markers ({len(markers)} markers)")
        else:
            results.add_pass("prepare_trade_markers (no trades)")
        
    except Exception as e:
        results.add_fail("Data Helpers", str(e))
    
    # ========================================
    # Test 7: Optimization Score
    # ========================================
    print()
    print("=" * 40)
    print("TEST 7: Optimization Score")
    print("=" * 40)
    
    try:
        settings = IndicatorSettings()
        
        df_opt = calculate_trg(df.copy(), 45, 4.0)
        df_opt = generate_signals(df_opt, settings)
        trades, equity, _, _, _ = run_backtest(df_opt, settings)
        
        # Test different metrics
        for metric in ['profit', 'winrate', 'sharpe', 'combined']:
            score, metrics = calculate_optimization_score(trades, equity, settings, metric)
            assert isinstance(score, (int, float))
            assert 'profit_pct' in metrics
            assert 'win_rate' in metrics
            results.add_pass(f"Metric '{metric}' (score: {score:.2f})")
        
    except Exception as e:
        results.add_fail("Optimization Score", str(e))
    
    # ========================================
    # Test 8: API Router
    # ========================================
    print()
    print("=" * 40)
    print("TEST 8: API Router")
    print("=" * 40)
    
    try:
        # Check routes
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            '/calculate',
            '/candles/{symbol}/{timeframe}',
            '/replay',
            '/heatmap',
            '/auto-optimize-stream',
            '/{plugin_id}/ui-schema',
            '/{plugin_id}/defaults',
            '/{plugin_id}/validate',
            '/plugins',
            '/health',
        ]
        
        for route in expected_routes:
            full_path = f"/api/indicator{route}"
            if any(route in r for r in routes):
                results.add_pass(f"Route: {full_path}")
            else:
                results.add_fail(f"Route: {full_path}", "Not found")
        
    except Exception as e:
        results.add_fail("API Router", str(e))
    
    # ========================================
    # Summary
    # ========================================
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Total:  {results.passed + results.failed}")
    print()
    
    if results.errors:
        print("Errors:")
        for name, error in results.errors:
            print(f"  - {name}: {error}")
    
    print()
    if results.failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️ {results.failed} tests failed")
    
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = run_tests()
    sys.exit(0 if results.failed == 0 else 1)
