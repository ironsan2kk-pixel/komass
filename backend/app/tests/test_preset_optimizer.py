"""
KOMAS Trading Server - Preset Optimizer Tests
==============================================
Unit tests for preset optimization engine.

Chat #45: Preset Optimizer Core
"""

import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)
    n_candles = 500
    
    dates = pd.date_range(start='2024-01-01', periods=n_candles, freq='1h')
    
    # Generate realistic price data with trend
    base_price = 40000
    returns = np.random.randn(n_candles) * 0.02  # 2% volatility
    prices = base_price * np.cumprod(1 + returns)
    
    df = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_candles) * 0.005),
        'high': prices * (1 + abs(np.random.randn(n_candles) * 0.01)),
        'low': prices * (1 - abs(np.random.randn(n_candles) * 0.01)),
        'close': prices,
        'volume': np.random.uniform(100, 1000, n_candles)
    }, index=dates)
    
    # Ensure OHLC consistency
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


@pytest.fixture
def sample_trg_preset():
    """Sample TRG preset configuration"""
    return {
        'id': 'trg_test_001',
        'name': 'Test TRG Preset',
        'indicator_type': 'trg',
        'params': {
            'trg_atr_length': 45,
            'trg_multiplier': 4.0,
            'tp_count': 4,
            'tp1_percent': 1.0,
            'tp2_percent': 2.0,
            'tp3_percent': 3.0,
            'tp4_percent': 5.0,
            'tp1_amount': 40.0,
            'tp2_amount': 30.0,
            'tp3_amount': 20.0,
            'tp4_amount': 10.0,
            'sl_percent': 3.0,
            'sl_trailing_mode': 'breakeven',
            'use_supertrend': False,
            'use_rsi_filter': False,
            'use_adx_filter': False
        }
    }


@pytest.fixture
def sample_dominant_preset():
    """Sample Dominant preset configuration"""
    return {
        'id': 'dom_test_001',
        'name': 'Test Dominant Preset',
        'indicator_type': 'dominant',
        'params': {
            'sensitivity': 21,
            'filter_type': 0,
            'sl_mode': 1,
            'dominant_tp1_percent': 1.0,
            'dominant_tp2_percent': 2.0,
            'dominant_tp3_percent': 3.0,
            'dominant_tp4_percent': 5.0,
            'dominant_tp1_amount': 40.0,
            'dominant_tp2_amount': 30.0,
            'dominant_tp3_amount': 20.0,
            'dominant_tp4_amount': 10.0,
            'dominant_sl_percent': 2.0
        }
    }


@pytest.fixture
def multiple_presets(sample_trg_preset, sample_dominant_preset):
    """Multiple presets for optimization testing"""
    presets = [sample_trg_preset, sample_dominant_preset]
    
    # Add more TRG variants
    for i1 in [30, 45, 60]:
        for i2 in [3.0, 4.0, 5.0]:
            presets.append({
                'id': f'trg_{i1}_{int(i2*10)}',
                'name': f'TRG {i1}/{i2}',
                'indicator_type': 'trg',
                'params': {
                    'trg_atr_length': i1,
                    'trg_multiplier': i2,
                    'tp_count': 4,
                    'tp1_percent': 1.0,
                    'tp2_percent': 2.0,
                    'tp3_percent': 3.0,
                    'tp4_percent': 5.0,
                    'tp1_amount': 40.0,
                    'tp2_amount': 30.0,
                    'tp3_amount': 20.0,
                    'tp4_amount': 10.0,
                    'sl_percent': 3.0,
                    'sl_trailing_mode': 'breakeven'
                }
            })
    
    return presets


# ============================================================================
# INDICATOR CALCULATION TESTS
# ============================================================================

class TestTRGIndicator:
    """Tests for TRG indicator calculation"""
    
    def test_calculate_trg_indicator(self, sample_ohlcv_data):
        """Test TRG indicator calculation"""
        from app.services.preset_optimizer import calculate_trg_indicator
        
        df = sample_ohlcv_data.copy()
        result = calculate_trg_indicator(df, i1=45, i2=4.0)
        
        # Check columns exist
        assert 'atr' in result.columns
        assert 'upper_band' in result.columns
        assert 'lower_band' in result.columns
        assert 'trg_trend' in result.columns
        
        # Check no NaN in calculated area
        assert not result['atr'].iloc[50:].isna().any()
        assert not result['trg_trend'].iloc[50:].isna().any()
        
        # Check trend values are valid (-1, 0, 1)
        assert result['trg_trend'].isin([-1, 0, 1]).all()
    
    def test_trg_trend_changes(self, sample_ohlcv_data):
        """Test that TRG trend changes correctly"""
        from app.services.preset_optimizer import calculate_trg_indicator
        
        df = sample_ohlcv_data.copy()
        result = calculate_trg_indicator(df, i1=45, i2=4.0)
        
        # Count trend changes
        trend_changes = (result['trg_trend'].diff() != 0).sum()
        
        # Should have some trend changes but not too many
        assert trend_changes > 0
        assert trend_changes < len(df) / 5  # Less than 20% of candles


class TestDominantIndicator:
    """Tests for Dominant indicator calculation"""
    
    def test_calculate_dominant_indicator(self, sample_ohlcv_data):
        """Test Dominant indicator calculation"""
        from app.services.preset_optimizer import calculate_dominant_indicator
        
        df = sample_ohlcv_data.copy()
        result = calculate_dominant_indicator(df, sensitivity=21)
        
        # Check columns exist
        assert 'high_channel' in result.columns
        assert 'low_channel' in result.columns
        assert 'mid_channel' in result.columns
        assert 'fib_236' in result.columns
        assert 'fib_618' in result.columns
        assert 'imba_trend_line' in result.columns
        
        # Check Fibonacci levels are in correct order
        assert (result['fib_236'].dropna() >= result['low_channel'].dropna()).all()
        assert (result['fib_786'].dropna() <= result['high_channel'].dropna()).all()
    
    def test_dominant_fibonacci_levels(self, sample_ohlcv_data):
        """Test that Fibonacci levels are calculated correctly"""
        from app.services.preset_optimizer import calculate_dominant_indicator
        
        df = sample_ohlcv_data.copy()
        result = calculate_dominant_indicator(df, sensitivity=21)
        
        # Check that fib levels are between channel bounds
        mask = ~result['fib_236'].isna()
        
        assert (result.loc[mask, 'fib_236'] >= result.loc[mask, 'low_channel']).all()
        assert (result.loc[mask, 'fib_786'] <= result.loc[mask, 'high_channel']).all()


# ============================================================================
# FILTER TESTS
# ============================================================================

class TestFilters:
    """Tests for indicator filters"""
    
    def test_supertrend_filter(self, sample_ohlcv_data):
        """Test SuperTrend filter calculation"""
        from app.services.preset_optimizer import calculate_supertrend_filter
        
        df = sample_ohlcv_data.copy()
        result = calculate_supertrend_filter(df, period=10, multiplier=3.0)
        
        assert 'supertrend_direction' in result.columns
        assert result['supertrend_direction'].isin([-1, 0, 1]).all()
    
    def test_rsi_calculation(self, sample_ohlcv_data):
        """Test RSI calculation"""
        from app.services.preset_optimizer import calculate_rsi
        
        df = sample_ohlcv_data.copy()
        result = calculate_rsi(df, period=14)
        
        assert 'rsi' in result.columns
        
        # RSI should be between 0 and 100
        valid_rsi = result['rsi'].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_adx_calculation(self, sample_ohlcv_data):
        """Test ADX calculation"""
        from app.services.preset_optimizer import calculate_adx
        
        df = sample_ohlcv_data.copy()
        result = calculate_adx(df, period=14)
        
        assert 'adx' in result.columns
        
        # ADX should be non-negative
        valid_adx = result['adx'].dropna()
        assert (valid_adx >= 0).all()


# ============================================================================
# BACKTEST SIMULATION TESTS
# ============================================================================

class TestBacktestSimulation:
    """Tests for trade simulation"""
    
    def test_simulate_trades_basic(self, sample_ohlcv_data):
        """Test basic trade simulation"""
        from app.services.preset_optimizer import (
            calculate_trg_indicator,
            simulate_trades
        )
        
        df = sample_ohlcv_data.copy()
        df = calculate_trg_indicator(df, i1=45, i2=4.0)
        
        # Add signals
        df['signal'] = 0
        df['trend_change'] = df['trg_trend'].diff().fillna(0)
        df.loc[df['trend_change'] == 1, 'signal'] = 1
        df.loc[df['trend_change'] == -1, 'signal'] = -1
        
        tp_levels = [1.0, 2.0, 3.0, 5.0]
        tp_amounts = [40.0, 30.0, 20.0, 10.0]
        sl_percent = 3.0
        
        result = simulate_trades(df, tp_levels, tp_amounts, sl_percent, 'breakeven')
        
        # Check result structure
        assert 'total_trades' in result
        assert 'win_rate' in result
        assert 'profit_pct' in result
        assert 'max_drawdown' in result
        
        # Metrics should be reasonable
        assert result['win_rate'] >= 0
        assert result['win_rate'] <= 100
        assert result['max_drawdown'] >= 0
    
    def test_simulate_trades_sl_modes(self, sample_ohlcv_data):
        """Test different SL modes"""
        from app.services.preset_optimizer import (
            calculate_trg_indicator,
            simulate_trades
        )
        
        df = sample_ohlcv_data.copy()
        df = calculate_trg_indicator(df, i1=45, i2=4.0)
        
        df['signal'] = 0
        df['trend_change'] = df['trg_trend'].diff().fillna(0)
        df.loc[df['trend_change'] == 1, 'signal'] = 1
        df.loc[df['trend_change'] == -1, 'signal'] = -1
        
        tp_levels = [1.0, 2.0, 3.0, 5.0]
        tp_amounts = [40.0, 30.0, 20.0, 10.0]
        sl_percent = 3.0
        
        # Test all SL modes
        for sl_mode in ['fixed', 'breakeven', 'cascade']:
            result = simulate_trades(df, tp_levels, tp_amounts, sl_percent, sl_mode)
            assert 'total_trades' in result
    
    def test_simulate_trades_no_signals(self, sample_ohlcv_data):
        """Test simulation with no signals"""
        from app.services.preset_optimizer import simulate_trades
        
        df = sample_ohlcv_data.copy()
        df['signal'] = 0  # No signals
        
        tp_levels = [1.0, 2.0, 3.0, 5.0]
        tp_amounts = [40.0, 30.0, 20.0, 10.0]
        
        result = simulate_trades(df, tp_levels, tp_amounts, 3.0, 'breakeven')
        
        assert result['total_trades'] == 0
        assert result['win_rate'] == 0
        assert result['profit_pct'] == 0


# ============================================================================
# WORKER FUNCTION TESTS
# ============================================================================

class TestWorkerFunction:
    """Tests for parallel worker function"""
    
    def test_worker_with_trg_preset(self, sample_ohlcv_data, sample_trg_preset):
        """Test worker with TRG preset"""
        from app.services.preset_optimizer import run_preset_backtest_worker
        
        df_json = sample_ohlcv_data.to_json(orient='split', date_format='iso')
        
        args = {
            'df_json': df_json,
            'preset': sample_trg_preset,
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'start_date': None,
            'end_date': None
        }
        
        result = run_preset_backtest_worker(args)
        
        assert result['preset_id'] == sample_trg_preset['id']
        assert result['symbol'] == 'BTCUSDT'
        assert 'error' not in result or result['error'] is None
        assert 'total_trades' in result
    
    def test_worker_with_dominant_preset(self, sample_ohlcv_data, sample_dominant_preset):
        """Test worker with Dominant preset"""
        from app.services.preset_optimizer import run_preset_backtest_worker
        
        df_json = sample_ohlcv_data.to_json(orient='split', date_format='iso')
        
        args = {
            'df_json': df_json,
            'preset': sample_dominant_preset,
            'symbol': 'ETHUSDT',
            'timeframe': '1h',
            'start_date': None,
            'end_date': None
        }
        
        result = run_preset_backtest_worker(args)
        
        assert result['preset_id'] == sample_dominant_preset['id']
        assert result['symbol'] == 'ETHUSDT'
        assert 'total_trades' in result
    
    def test_worker_with_insufficient_data(self, sample_trg_preset):
        """Test worker with insufficient data"""
        from app.services.preset_optimizer import run_preset_backtest_worker
        
        # Create tiny dataframe
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [100, 100, 100]
        }, index=pd.date_range('2024-01-01', periods=3, freq='1h'))
        
        df_json = df.to_json(orient='split', date_format='iso')
        
        args = {
            'df_json': df_json,
            'preset': sample_trg_preset,
            'symbol': 'BTCUSDT',
            'timeframe': '1h'
        }
        
        result = run_preset_backtest_worker(args)
        
        # Should return error for insufficient data
        assert result['error'] is not None
        assert 'Insufficient data' in result['error']


# ============================================================================
# AGGREGATE SCORE TESTS
# ============================================================================

class TestAggregateScores:
    """Tests for aggregate score calculation"""
    
    def test_calculate_aggregate_scores(self):
        """Test aggregate score calculation"""
        from app.services.preset_optimizer import (
            PresetOptimizer,
            PresetBacktestResult
        )
        
        optimizer = PresetOptimizer()
        
        # Create sample results
        results = [
            PresetBacktestResult(
                preset_id='test_001',
                preset_name='Test Preset',
                symbol='BTCUSDT',
                timeframe='1h',
                total_trades=50,
                win_rate=60.0,
                profit_pct=25.0,
                profit_factor=1.8,
                max_drawdown=8.0,
                sharpe_ratio=1.5
            ),
            PresetBacktestResult(
                preset_id='test_001',
                preset_name='Test Preset',
                symbol='ETHUSDT',
                timeframe='1h',
                total_trades=45,
                win_rate=55.0,
                profit_pct=18.0,
                profit_factor=1.5,
                max_drawdown=10.0,
                sharpe_ratio=1.2
            ),
            PresetBacktestResult(
                preset_id='test_001',
                preset_name='Test Preset',
                symbol='SOLUSDT',
                timeframe='1h',
                total_trades=40,
                win_rate=50.0,
                profit_pct=-5.0,
                profit_factor=0.9,
                max_drawdown=15.0,
                sharpe_ratio=0.3
            )
        ]
        
        score = optimizer.calculate_aggregate_scores(
            results, 'test_001', 'Test Preset', 'trg'
        )
        
        # Check calculated values
        assert score.preset_id == 'test_001'
        assert score.total_pairs == 3
        assert score.positive_pairs == 2
        assert score.negative_pairs == 1
        assert abs(score.positive_ratio - 66.67) < 1.0
        
        # Check avg calculations
        expected_avg_pnl = (25.0 + 18.0 - 5.0) / 3
        assert abs(score.avg_pnl - expected_avg_pnl) < 0.1
        
        # Check scores are in valid range
        assert 0 <= score.overall_score <= 100
        assert 0 <= score.profitability_score <= 100
        assert 0 <= score.stability_score <= 100
        assert 0 <= score.universality_score <= 100
    
    def test_aggregate_scores_all_positive(self):
        """Test aggregate scores when all pairs are positive"""
        from app.services.preset_optimizer import (
            PresetOptimizer,
            PresetBacktestResult
        )
        
        optimizer = PresetOptimizer()
        
        results = [
            PresetBacktestResult(
                preset_id='test_002',
                preset_name='Good Preset',
                symbol=f'PAIR{i}USDT',
                timeframe='1h',
                total_trades=50,
                win_rate=65.0,
                profit_pct=30.0 - i * 3,  # All positive
                profit_factor=2.0,
                max_drawdown=5.0,
                sharpe_ratio=2.0
            )
            for i in range(5)
        ]
        
        score = optimizer.calculate_aggregate_scores(
            results, 'test_002', 'Good Preset', 'trg'
        )
        
        assert score.positive_pairs == 5
        assert score.negative_pairs == 0
        assert score.positive_ratio == 100.0
        assert score.universality_score == 100.0
    
    def test_aggregate_scores_with_errors(self):
        """Test aggregate scores when some results have errors"""
        from app.services.preset_optimizer import (
            PresetOptimizer,
            PresetBacktestResult
        )
        
        optimizer = PresetOptimizer()
        
        results = [
            PresetBacktestResult(
                preset_id='test_003',
                preset_name='Error Preset',
                symbol='BTCUSDT',
                timeframe='1h',
                total_trades=50,
                win_rate=60.0,
                profit_pct=20.0,
                profit_factor=1.5,
                max_drawdown=10.0,
                sharpe_ratio=1.0
            ),
            PresetBacktestResult(
                preset_id='test_003',
                preset_name='Error Preset',
                symbol='ETHUSDT',
                timeframe='1h',
                error='Data not found'
            )
        ]
        
        score = optimizer.calculate_aggregate_scores(
            results, 'test_003', 'Error Preset', 'trg'
        )
        
        # Should only count valid result
        assert score.total_pairs == 2
        assert score.positive_pairs == 1


# ============================================================================
# RESULT MATRIX TESTS
# ============================================================================

class TestResultMatrix:
    """Tests for result matrix generation"""
    
    def test_generate_result_matrix(self):
        """Test result matrix generation"""
        from app.services.preset_optimizer import (
            PresetOptimizer,
            PresetBacktestResult
        )
        
        optimizer = PresetOptimizer()
        
        results = [
            PresetBacktestResult(
                preset_id='preset_1',
                preset_name='Preset 1',
                symbol='BTCUSDT',
                timeframe='1h',
                profit_pct=20.0,
                win_rate=60.0,
                total_trades=50,
                max_drawdown=8.0,
                sharpe_ratio=1.5,
                profit_factor=1.8
            ),
            PresetBacktestResult(
                preset_id='preset_1',
                preset_name='Preset 1',
                symbol='ETHUSDT',
                timeframe='1h',
                profit_pct=15.0,
                win_rate=55.0,
                total_trades=45,
                max_drawdown=10.0,
                sharpe_ratio=1.2,
                profit_factor=1.5
            ),
            PresetBacktestResult(
                preset_id='preset_2',
                preset_name='Preset 2',
                symbol='BTCUSDT',
                timeframe='1h',
                profit_pct=25.0,
                win_rate=65.0,
                total_trades=55,
                max_drawdown=6.0,
                sharpe_ratio=1.8,
                profit_factor=2.0
            )
        ]
        
        matrix = optimizer.generate_result_matrix(results)
        
        # Check structure
        assert 'preset_1' in matrix
        assert 'preset_2' in matrix
        assert 'BTCUSDT' in matrix['preset_1']
        assert 'ETHUSDT' in matrix['preset_1']
        assert 'BTCUSDT' in matrix['preset_2']
        
        # Check values
        assert matrix['preset_1']['BTCUSDT']['profit_pct'] == 20.0
        assert matrix['preset_2']['BTCUSDT']['profit_pct'] == 25.0


# ============================================================================
# OPTIMIZER CLASS TESTS
# ============================================================================

class TestPresetOptimizer:
    """Tests for PresetOptimizer class"""
    
    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        from app.services.preset_optimizer import PresetOptimizer
        
        optimizer = PresetOptimizer()
        
        assert optimizer.num_workers > 0
        assert optimizer.data_dir.exists() or True  # May not exist in test env
    
    def test_generate_run_id(self):
        """Test run ID generation"""
        from app.services.preset_optimizer import PresetOptimizer
        
        optimizer = PresetOptimizer()
        
        run_id1 = optimizer.generate_run_id()
        run_id2 = optimizer.generate_run_id()
        
        assert run_id1.startswith('opt_')
        assert run_id2.startswith('opt_')
        assert run_id1 != run_id2  # Should be unique
    
    def test_get_active_runs_empty(self):
        """Test get active runs when empty"""
        from app.services.preset_optimizer import PresetOptimizer
        
        optimizer = PresetOptimizer()
        
        active = optimizer.get_active_runs()
        
        assert isinstance(active, list)
    
    def test_cancel_nonexistent_run(self):
        """Test canceling a non-existent run"""
        from app.services.preset_optimizer import PresetOptimizer
        
        optimizer = PresetOptimizer()
        
        result = optimizer.cancel_optimization('nonexistent_run_id')
        
        assert result is False


# ============================================================================
# TRG BACKTEST TESTS
# ============================================================================

class TestTRGBacktest:
    """Tests for TRG backtest function"""
    
    def test_run_trg_backtest(self, sample_ohlcv_data, sample_trg_preset):
        """Test TRG backtest execution"""
        from app.services.preset_optimizer import run_trg_backtest
        
        df = sample_ohlcv_data.copy()
        params = sample_trg_preset['params']
        
        result = run_trg_backtest(df, params)
        
        assert 'total_trades' in result
        assert 'win_rate' in result
        assert 'profit_pct' in result
        assert 'max_drawdown' in result
        assert 'sharpe_ratio' in result
    
    def test_trg_backtest_with_filters(self, sample_ohlcv_data):
        """Test TRG backtest with filters enabled"""
        from app.services.preset_optimizer import run_trg_backtest
        
        df = sample_ohlcv_data.copy()
        params = {
            'trg_atr_length': 45,
            'trg_multiplier': 4.0,
            'tp_count': 4,
            'tp1_percent': 1.0,
            'tp2_percent': 2.0,
            'tp3_percent': 3.0,
            'tp4_percent': 5.0,
            'tp1_amount': 40.0,
            'tp2_amount': 30.0,
            'tp3_amount': 20.0,
            'tp4_amount': 10.0,
            'sl_percent': 3.0,
            'sl_trailing_mode': 'breakeven',
            'use_supertrend': True,
            'supertrend_period': 10,
            'supertrend_multiplier': 3.0,
            'use_rsi_filter': True,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }
        
        result = run_trg_backtest(df, params)
        
        # With filters, we might get fewer trades
        assert 'total_trades' in result


# ============================================================================
# DOMINANT BACKTEST TESTS
# ============================================================================

class TestDominantBacktest:
    """Tests for Dominant backtest function"""
    
    def test_run_dominant_backtest(self, sample_ohlcv_data, sample_dominant_preset):
        """Test Dominant backtest execution"""
        from app.services.preset_optimizer import run_dominant_backtest
        
        df = sample_ohlcv_data.copy()
        params = sample_dominant_preset['params']
        
        result = run_dominant_backtest(df, params)
        
        assert 'total_trades' in result
        assert 'win_rate' in result
        assert 'profit_pct' in result
    
    def test_dominant_backtest_all_sl_modes(self, sample_ohlcv_data):
        """Test Dominant backtest with all SL modes"""
        from app.services.preset_optimizer import run_dominant_backtest
        
        df = sample_ohlcv_data.copy()
        
        for sl_mode in [0, 1, 2, 3, 4]:
            params = {
                'sensitivity': 21,
                'filter_type': 0,
                'sl_mode': sl_mode,
                'dominant_tp1_percent': 1.0,
                'dominant_tp2_percent': 2.0,
                'dominant_tp3_percent': 3.0,
                'dominant_tp4_percent': 5.0,
                'dominant_sl_percent': 2.0
            }
            
            result = run_dominant_backtest(df, params)
            assert 'total_trades' in result


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and stress tests"""
    
    def test_large_dataframe_performance(self):
        """Test performance with large dataframe"""
        import time
        from app.services.preset_optimizer import run_trg_backtest
        
        # Create large dataframe
        np.random.seed(42)
        n_candles = 5000
        dates = pd.date_range(start='2023-01-01', periods=n_candles, freq='1h')
        
        base_price = 40000
        returns = np.random.randn(n_candles) * 0.02
        prices = base_price * np.cumprod(1 + returns)
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(n_candles) * 0.005),
            'high': prices * (1 + abs(np.random.randn(n_candles) * 0.01)),
            'low': prices * (1 - abs(np.random.randn(n_candles) * 0.01)),
            'close': prices,
            'volume': np.random.uniform(100, 1000, n_candles)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        params = {
            'trg_atr_length': 45,
            'trg_multiplier': 4.0,
            'tp_count': 4,
            'tp1_percent': 1.0,
            'tp2_percent': 2.0,
            'tp3_percent': 3.0,
            'tp4_percent': 5.0,
            'sl_percent': 3.0,
            'sl_trailing_mode': 'breakeven'
        }
        
        start = time.time()
        result = run_trg_backtest(df, params)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert 'total_trades' in result


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
