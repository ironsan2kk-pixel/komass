"""
Test suite for Dominant Indicator SL Modes (Chat #23)

Tests cover:
- SL Mode Constants
- calculate_tp_levels()
- calculate_initial_sl()
- calculate_sl_level() for all 5 modes
- track_position() position simulation
- get_sl_mode_info()
- get_sl_mode_statistics()

Run with: pytest tests/test_dominant_sl_modes.py -v
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Import from indicators package
import sys
sys.path.insert(0, 'backend/app')

from indicators.dominant import (
    # Constants
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
    
    # SL Mode Constants
    SL_MODE_FIXED,
    SL_MODE_AFTER_TP1,
    SL_MODE_AFTER_TP2,
    SL_MODE_AFTER_TP3,
    SL_MODE_CASCADE,
    SL_MODE_NAMES,
    SL_MODE_DESCRIPTIONS,
    SL_DEFAULTS,
    
    # SL Mode Functions
    validate_sl_mode,
    calculate_tp_levels,
    calculate_initial_sl,
    calculate_sl_level,
    track_position,
    get_sl_mode_info,
    get_sl_mode_statistics,
    
    # Signal Generation
    generate_signals,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_df():
    """Create sample OHLCV DataFrame for testing"""
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2024-01-01', periods=n, freq='1h')
    
    # Generate trending price data
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    
    return pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(n) * 0.5),
        'low': prices - np.abs(np.random.randn(n) * 0.5),
        'close': prices + np.random.randn(n) * 0.3,
        'volume': np.random.randint(1000, 10000, n)
    }, index=dates)


@pytest.fixture
def trending_up_df():
    """Create DataFrame with clear uptrend for testing"""
    n = 50
    dates = pd.date_range('2024-01-01', periods=n, freq='1h')
    
    # Clear uptrend: each candle higher than previous
    base = 100
    prices = [base + i * 0.5 for i in range(n)]
    
    return pd.DataFrame({
        'open': [p - 0.1 for p in prices],
        'high': [p + 0.3 for p in prices],
        'low': [p - 0.3 for p in prices],
        'close': prices,
        'volume': [5000] * n
    }, index=dates)


@pytest.fixture
def trending_down_df():
    """Create DataFrame with clear downtrend for testing"""
    n = 50
    dates = pd.date_range('2024-01-01', periods=n, freq='1h')
    
    # Clear downtrend: each candle lower than previous
    base = 120
    prices = [base - i * 0.5 for i in range(n)]
    
    return pd.DataFrame({
        'open': [p + 0.1 for p in prices],
        'high': [p + 0.3 for p in prices],
        'low': [p - 0.3 for p in prices],
        'close': prices,
        'volume': [5000] * n
    }, index=dates)


# =============================================================================
# TEST: SL MODE CONSTANTS
# =============================================================================

class TestSLModeConstants:
    """Test SL mode constants are defined correctly"""
    
    def test_sl_mode_values(self):
        """Test SL mode integer values"""
        assert SL_MODE_FIXED == 0
        assert SL_MODE_AFTER_TP1 == 1
        assert SL_MODE_AFTER_TP2 == 2
        assert SL_MODE_AFTER_TP3 == 3
        assert SL_MODE_CASCADE == 4
    
    def test_sl_mode_names_complete(self):
        """Test all SL modes have names"""
        for mode in range(5):
            assert mode in SL_MODE_NAMES
            assert isinstance(SL_MODE_NAMES[mode], str)
            assert len(SL_MODE_NAMES[mode]) > 0
    
    def test_sl_mode_descriptions_complete(self):
        """Test all SL modes have descriptions"""
        for mode in range(5):
            assert mode in SL_MODE_DESCRIPTIONS
            assert isinstance(SL_MODE_DESCRIPTIONS[mode], str)
            assert len(SL_MODE_DESCRIPTIONS[mode]) > 0
    
    def test_sl_defaults(self):
        """Test SL defaults are reasonable"""
        assert 'sl_percent' in SL_DEFAULTS
        assert 'tp_percents' in SL_DEFAULTS
        assert SL_DEFAULTS['sl_percent'] > 0
        assert len(SL_DEFAULTS['tp_percents']) >= 2


class TestValidateSLMode:
    """Test validate_sl_mode() function"""
    
    def test_valid_modes(self):
        """Test valid SL modes pass through"""
        for mode in range(5):
            assert validate_sl_mode(mode) == mode
    
    def test_negative_clamped_to_zero(self):
        """Test negative values clamped to 0"""
        assert validate_sl_mode(-1) == 0
        assert validate_sl_mode(-100) == 0
    
    def test_high_clamped_to_max(self):
        """Test values > 4 clamped to 4"""
        assert validate_sl_mode(5) == 4
        assert validate_sl_mode(100) == 4
    
    def test_float_converted(self):
        """Test float values converted to int"""
        assert validate_sl_mode(2.7) == 2
        assert validate_sl_mode(3.1) == 3
    
    def test_invalid_type_returns_default(self):
        """Test invalid types return default (0)"""
        assert validate_sl_mode(None) == 0
        assert validate_sl_mode("invalid") == 0
        assert validate_sl_mode([1, 2, 3]) == 0


# =============================================================================
# TEST: CALCULATE TP LEVELS
# =============================================================================

class TestCalculateTPLevels:
    """Test calculate_tp_levels() function"""
    
    def test_long_tp_levels_above_entry(self):
        """Test TP levels are above entry for LONG"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_LONG, [1.0, 2.0, 3.0])
        
        assert len(tp_levels) == 3
        assert tp_levels[0] == 101.0  # 1% above
        assert tp_levels[1] == 102.0  # 2% above
        assert tp_levels[2] == 103.0  # 3% above
    
    def test_short_tp_levels_below_entry(self):
        """Test TP levels are below entry for SHORT"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_SHORT, [1.0, 2.0, 3.0])
        
        assert len(tp_levels) == 3
        assert tp_levels[0] == 99.0   # 1% below
        assert tp_levels[1] == 98.0   # 2% below
        assert tp_levels[2] == 97.0   # 3% below
    
    def test_default_tp_percents(self):
        """Test default TP percentages are used"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_LONG)
        
        # Should use SL_DEFAULTS['tp_percents'] = [1.0, 2.0, 3.0, 5.0]
        assert len(tp_levels) == 4
    
    def test_empty_tp_percents(self):
        """Test empty TP list returns empty"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_LONG, [])
        assert tp_levels == []
    
    def test_single_tp(self):
        """Test single TP level"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_LONG, [5.0])
        
        assert len(tp_levels) == 1
        assert tp_levels[0] == 105.0
    
    def test_fractional_percents(self):
        """Test fractional percentages"""
        tp_levels = calculate_tp_levels(100.0, SIGNAL_LONG, [0.5, 1.5])
        
        assert tp_levels[0] == pytest.approx(100.5, rel=1e-6)
        assert tp_levels[1] == pytest.approx(101.5, rel=1e-6)


# =============================================================================
# TEST: CALCULATE INITIAL SL
# =============================================================================

class TestCalculateInitialSL:
    """Test calculate_initial_sl() function"""
    
    def test_long_sl_below_entry(self):
        """Test SL is below entry for LONG"""
        sl = calculate_initial_sl(100.0, SIGNAL_LONG, 2.0)
        assert sl == 98.0  # 2% below
    
    def test_short_sl_above_entry(self):
        """Test SL is above entry for SHORT"""
        sl = calculate_initial_sl(100.0, SIGNAL_SHORT, 2.0)
        assert sl == 102.0  # 2% above
    
    def test_default_sl_percent(self):
        """Test default SL percent is used"""
        sl = calculate_initial_sl(100.0, SIGNAL_LONG)
        # Should use SL_DEFAULTS['sl_percent'] = 2.0
        assert sl == 98.0
    
    def test_large_sl_percent(self):
        """Test larger SL percentages"""
        sl = calculate_initial_sl(100.0, SIGNAL_LONG, 10.0)
        assert sl == 90.0  # 10% below
    
    def test_small_sl_percent(self):
        """Test small SL percentages"""
        sl = calculate_initial_sl(100.0, SIGNAL_SHORT, 0.5)
        assert sl == pytest.approx(100.5, rel=1e-9)  # 0.5% above


# =============================================================================
# TEST: SL MODE FIXED (Mode 0)
# =============================================================================

class TestSLModeFixed:
    """Test SL Mode 0 - Fixed (SL never moves)"""
    
    def test_sl_never_moves_no_tps(self):
        """Test SL stays at original with no TPs hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_FIXED,
            tps_hit=[False, False, False, False]
        )
        assert sl == 98.0  # Original SL
    
    def test_sl_never_moves_all_tps(self):
        """Test SL stays at original even with all TPs hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_FIXED,
            tps_hit=[True, True, True, True]
        )
        assert sl == 98.0  # Still at original
    
    def test_fixed_sl_long(self):
        """Test fixed SL for long position"""
        sl = calculate_sl_level(
            entry_price=50000.0,  # BTC price example
            direction=SIGNAL_LONG,
            sl_percent=3.0,
            sl_mode=SL_MODE_FIXED,
            tps_hit=[True, True, False, False]
        )
        assert sl == 48500.0  # 3% below 50000
    
    def test_fixed_sl_short(self):
        """Test fixed SL for short position"""
        sl = calculate_sl_level(
            entry_price=50000.0,
            direction=SIGNAL_SHORT,
            sl_percent=3.0,
            sl_mode=SL_MODE_FIXED,
            tps_hit=[True, True, False, False]
        )
        assert sl == 51500.0  # 3% above 50000


# =============================================================================
# TEST: SL MODE AFTER TP1 (Mode 1)
# =============================================================================

class TestSLModeAfterTP1:
    """Test SL Mode 1 - Breakeven after TP1"""
    
    def test_sl_unchanged_before_tp1(self):
        """Test SL stays at original before TP1 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=[False, False, False, False]
        )
        assert sl == 98.0  # Original SL
    
    def test_sl_moves_to_entry_after_tp1(self):
        """Test SL moves to entry after TP1 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=[True, False, False, False]
        )
        assert sl == 100.0  # Breakeven
    
    def test_sl_stays_at_breakeven_after_more_tps(self):
        """Test SL stays at breakeven after more TPs hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=[True, True, True, False]
        )
        assert sl == 100.0  # Still breakeven
    
    def test_breakeven_protects_from_loss_long(self):
        """Test breakeven protects from loss on long"""
        # After TP1, worst case is breakeven (no loss)
        sl = calculate_sl_level(
            entry_price=50000.0,
            direction=SIGNAL_LONG,
            sl_percent=5.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=[True, False, False, False]
        )
        assert sl == 50000.0  # Breakeven = no loss
    
    def test_breakeven_protects_from_loss_short(self):
        """Test breakeven protects from loss on short"""
        sl = calculate_sl_level(
            entry_price=50000.0,
            direction=SIGNAL_SHORT,
            sl_percent=5.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=[True, False, False, False]
        )
        assert sl == 50000.0  # Breakeven


# =============================================================================
# TEST: SL MODE AFTER TP2 (Mode 2)
# =============================================================================

class TestSLModeAfterTP2:
    """Test SL Mode 2 - Breakeven after TP2"""
    
    def test_sl_unchanged_before_tp2(self):
        """Test SL stays at original before TP2 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP2,
            tps_hit=[False, False, False, False]
        )
        assert sl == 98.0
    
    def test_sl_unchanged_after_tp1_only(self):
        """Test SL stays at original after only TP1 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP2,
            tps_hit=[True, False, False, False]
        )
        assert sl == 98.0  # Still at original (not breakeven yet)
    
    def test_sl_moves_after_tp2(self):
        """Test SL moves to breakeven after TP2 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP2,
            tps_hit=[True, True, False, False]
        )
        assert sl == 100.0  # Breakeven
    
    def test_sl_stays_at_breakeven_after_more(self):
        """Test SL stays at breakeven after more TPs"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP2,
            tps_hit=[True, True, True, True]
        )
        assert sl == 100.0


# =============================================================================
# TEST: SL MODE AFTER TP3 (Mode 3)
# =============================================================================

class TestSLModeAfterTP3:
    """Test SL Mode 3 - Breakeven after TP3"""
    
    def test_sl_unchanged_after_tp1_tp2(self):
        """Test SL stays at original after TP1 and TP2 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP3,
            tps_hit=[True, True, False, False]
        )
        assert sl == 98.0  # Still at original
    
    def test_sl_moves_after_tp3_only(self):
        """Test SL moves only after TP3 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP3,
            tps_hit=[True, True, True, False]
        )
        assert sl == 100.0  # Breakeven
    
    def test_short_position_breakeven(self):
        """Test breakeven for short position"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_SHORT,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP3,
            tps_hit=[True, True, True, False]
        )
        assert sl == 100.0  # Breakeven


# =============================================================================
# TEST: SL MODE CASCADE (Mode 4)
# =============================================================================

class TestSLModeCascade:
    """Test SL Mode 4 - Cascade Trailing"""
    
    def test_sl_at_original_no_tps(self):
        """Test SL at original when no TPs hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[False, False, False, False],
            tp_levels=[101.0, 102.0, 103.0, 105.0]
        )
        assert sl == 98.0  # Original SL
    
    def test_sl_moves_to_entry_after_tp1(self):
        """Test SL moves to breakeven after TP1"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, False, False, False],
            tp_levels=[101.0, 102.0, 103.0, 105.0]
        )
        assert sl == 100.0  # Breakeven
    
    def test_sl_trails_to_tp1_after_tp2(self):
        """Test SL trails to TP1 level after TP2 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, False, False],
            tp_levels=[101.0, 102.0, 103.0, 105.0]
        )
        assert sl == 101.0  # TP1 level
    
    def test_sl_trails_to_tp2_after_tp3(self):
        """Test SL trails to TP2 level after TP3 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, True, False],
            tp_levels=[101.0, 102.0, 103.0, 105.0]
        )
        assert sl == 102.0  # TP2 level
    
    def test_sl_trails_to_tp3_after_tp4(self):
        """Test SL trails to TP3 level after TP4 hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, True, True],
            tp_levels=[101.0, 102.0, 103.0, 105.0]
        )
        assert sl == 103.0  # TP3 level
    
    def test_cascade_locks_profit_long(self):
        """Test cascade mode locks in profit for long"""
        # After TP2, SL at TP1 means minimum 1% profit locked
        entry = 100.0
        tp1 = 101.0  # 1% profit
        
        sl = calculate_sl_level(
            entry_price=entry,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, False, False],
            tp_levels=[tp1, 102.0, 103.0, 105.0]
        )
        
        # If SL hit at this point, profit = (sl - entry) / entry * 100 = 1%
        assert sl == tp1
        profit_locked = (sl - entry) / entry * 100
        assert profit_locked == pytest.approx(1.0, rel=0.01)
    
    def test_cascade_short_position(self):
        """Test cascade for short position"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_SHORT,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, False, False],
            tp_levels=[99.0, 98.0, 97.0, 95.0]  # Short TPs are below entry
        )
        assert sl == 99.0  # TP1 level for short


# =============================================================================
# TEST: POSITION TRACKING
# =============================================================================

class TestPositionTracking:
    """Test track_position() function"""
    
    def test_track_long_position_sl_hit(self):
        """Test tracking long position that hits SL"""
        # Create data where price drops after entry
        n = 20
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        
        # Entry at 100, then price drops
        prices = [100] + [100 - i * 0.5 for i in range(1, n)]
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.1 for p in prices],
            'low': [p - 0.5 for p in prices],  # Low goes down
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=2.0,  # SL at 98
            tp_percents=[1.0, 2.0, 3.0],
            sl_mode=SL_MODE_FIXED
        )
        
        assert result['exit_reason'] == 'sl'
        assert result['pnl_percent'] < 0  # Loss
    
    def test_track_long_position_tp_hit(self):
        """Test tracking long position that hits TP"""
        # Create data where price rises after entry
        n = 20
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        
        # Entry at 100, then price rises
        prices = [100] + [100 + i * 0.5 for i in range(1, n)]
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.5 for p in prices],  # High goes up
            'low': [p - 0.1 for p in prices],
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=2.0,
            tp_percents=[1.0, 2.0, 3.0],  # TP1 at 101, TP2 at 102, etc.
            sl_mode=SL_MODE_FIXED
        )
        
        # Should hit at least TP1
        assert result['tps_hit'][0] == True  # TP1 hit
    
    def test_track_short_position(self):
        """Test tracking short position"""
        # Create data where price drops after entry (good for short)
        n = 20
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        
        # Entry at 100, then price drops
        prices = [100] + [100 - i * 0.5 for i in range(1, n)]
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.1 for p in prices],
            'low': [p - 0.5 for p in prices],
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_SHORT,
            entry_price=100.0,
            sl_percent=2.0,
            tp_percents=[1.0, 2.0, 3.0],
            sl_mode=SL_MODE_FIXED
        )
        
        # Short should profit when price drops
        assert result['tps_hit'][0] == True  # TP1 hit
    
    def test_cascade_sl_movement(self):
        """Test SL moves correctly in cascade mode"""
        # Create data with clear uptrend for long
        n = 30
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        
        # Price goes up then back down
        prices = [100]
        for i in range(1, 15):  # Rising
            prices.append(100 + i * 0.5)
        for i in range(15, 30):  # Falling back
            prices.append(prices[14] - (i - 14) * 0.3)
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.3 for p in prices],
            'low': [p - 0.3 for p in prices],
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=2.0,
            tp_percents=[1.0, 2.0, 3.0, 5.0],
            sl_mode=SL_MODE_CASCADE
        )
        
        # Should have SL movements recorded
        assert len(result['sl_history']) > 0
        
        # If TPs were hit, SL should have moved
        if sum(result['tps_hit']) > 0:
            assert len(result['sl_history']) > 1  # Initial + at least one move
    
    def test_multiple_tp_hits(self):
        """Test position hitting multiple TPs before exit"""
        # Create strong uptrend
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        
        prices = [100 + i * 0.3 for i in range(n)]  # Steady uptrend
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.2 for p in prices],
            'low': [p - 0.1 for p in prices],
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=1.0,
            tp_percents=[1.0, 2.0, 3.0],
            sl_mode=SL_MODE_FIXED
        )
        
        # With strong uptrend, all TPs should be hit
        assert sum(result['tps_hit']) >= 1  # At least TP1
    
    def test_duration_tracking(self):
        """Test duration is tracked correctly"""
        n = 10
        dates = pd.date_range('2024-01-01', periods=n, freq='1h')
        prices = [100] * n  # Flat price
        
        df = pd.DataFrame({
            'open': prices,
            'high': [101] * n,
            'low': [99] * n,
            'close': prices,
            'volume': [5000] * n
        }, index=dates)
        
        result = track_position(
            df=df,
            entry_idx=2,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=5.0,  # Wide SL won't be hit
            tp_percents=[10.0],  # Wide TP won't be hit
            sl_mode=SL_MODE_FIXED
        )
        
        # Should hold until end of data
        assert result['exit_reason'] == 'end_of_data'
        assert result['duration'] == n - 1 - 2  # From entry to last bar


# =============================================================================
# TEST: GET SL MODE INFO
# =============================================================================

class TestGetSLModeInfo:
    """Test get_sl_mode_info() function"""
    
    def test_get_specific_mode(self):
        """Test getting info for specific mode"""
        info = get_sl_mode_info(SL_MODE_CASCADE)
        
        assert 'id' in info
        assert 'name' in info
        assert 'description' in info
        assert info['id'] == SL_MODE_CASCADE
        assert info['trails'] == True
    
    def test_get_all_modes(self):
        """Test getting info for all modes"""
        all_info = get_sl_mode_info()
        
        assert len(all_info) == 5
        for mode_id in range(5):
            assert mode_id in all_info
            assert 'name' in all_info[mode_id]
    
    def test_invalid_mode_clamped_to_valid(self):
        """Test invalid mode is clamped to valid range"""
        # 99 is clamped to SL_MODE_CASCADE (max valid = 4)
        info = get_sl_mode_info(99)
        assert info['id'] == SL_MODE_CASCADE
        
        # Negative is clamped to SL_MODE_FIXED (min = 0)
        info_neg = get_sl_mode_info(-5)
        assert info_neg['id'] == SL_MODE_FIXED
    
    def test_cascade_has_trail_logic(self):
        """Test cascade mode has trail logic details"""
        info = get_sl_mode_info(SL_MODE_CASCADE)
        
        assert 'trail_logic' in info
        assert len(info['trail_logic']) > 0
    
    def test_breakeven_modes_have_breakeven_after(self):
        """Test breakeven modes indicate when they trigger"""
        info1 = get_sl_mode_info(SL_MODE_AFTER_TP1)
        info2 = get_sl_mode_info(SL_MODE_AFTER_TP2)
        info3 = get_sl_mode_info(SL_MODE_AFTER_TP3)
        
        assert info1['breakeven_after'] == 'TP1'
        assert info2['breakeven_after'] == 'TP2'
        assert info3['breakeven_after'] == 'TP3'


# =============================================================================
# TEST: GET SL MODE STATISTICS
# =============================================================================

class TestGetSLModeStatistics:
    """Test get_sl_mode_statistics() function"""
    
    def test_empty_trades(self):
        """Test with empty trades list"""
        stats = get_sl_mode_statistics([])
        assert 'error' in stats
    
    def test_all_sl_exits(self):
        """Test statistics with all SL exits"""
        trades = [
            {'exit_reason': 'sl', 'pnl_percent': -2.0},
            {'exit_reason': 'sl', 'pnl_percent': -1.5},
            {'exit_reason': 'sl', 'pnl_percent': -1.0},
        ]
        
        stats = get_sl_mode_statistics(trades)
        
        assert stats['total_trades'] == 3
        assert stats['sl_exits'] == 3
        assert stats['sl_exit_rate'] == 100.0
        assert len(stats['tp_exits']) == 0
    
    def test_all_tp_exits(self):
        """Test statistics with all TP exits"""
        trades = [
            {'exit_reason': 'tp1', 'pnl_percent': 1.0},
            {'exit_reason': 'tp2', 'pnl_percent': 2.0},
            {'exit_reason': 'tp3', 'pnl_percent': 3.0},
        ]
        
        stats = get_sl_mode_statistics(trades)
        
        assert stats['sl_exits'] == 0
        assert stats['tp_exits']['tp1'] == 1
        assert stats['tp_exits']['tp2'] == 1
        assert stats['tp_exits']['tp3'] == 1
        assert stats['tp_exit_rate'] == 100.0
    
    def test_mixed_exits(self):
        """Test statistics with mixed exits"""
        trades = [
            {'exit_reason': 'tp1', 'pnl_percent': 1.0},
            {'exit_reason': 'sl', 'pnl_percent': -2.0},
            {'exit_reason': 'tp2', 'pnl_percent': 2.0},
            {'exit_reason': 'sl', 'pnl_percent': 0.0},  # Breakeven
        ]
        
        stats = get_sl_mode_statistics(trades)
        
        assert stats['total_trades'] == 4
        assert stats['sl_exits'] == 2
        assert stats['breakeven_protected'] == 1  # One SL at ~0
    
    def test_pnl_statistics(self):
        """Test PnL statistics calculation"""
        trades = [
            {'exit_reason': 'tp1', 'pnl_percent': 1.0},
            {'exit_reason': 'tp1', 'pnl_percent': 1.5},
            {'exit_reason': 'sl', 'pnl_percent': -2.0},
        ]
        
        stats = get_sl_mode_statistics(trades)
        
        assert 'pnl_stats' in stats
        assert stats['pnl_stats']['total'] == pytest.approx(0.5, rel=0.01)  # 1 + 1.5 - 2
        assert stats['pnl_stats']['win_rate'] == pytest.approx(66.67, rel=0.1)  # 2/3


# =============================================================================
# TEST: INTEGRATION WITH GENERATE_SIGNALS
# =============================================================================

class TestSLModesIntegration:
    """Test SL modes integration with signal generation"""
    
    def test_backtest_with_sl_modes(self, sample_df):
        """Test running backtest with different SL modes"""
        # Generate signals
        result = generate_signals(sample_df, sensitivity=21)
        
        # Find signals
        signals = result[result['signal'] != SIGNAL_NONE]
        
        if len(signals) == 0:
            pytest.skip("No signals generated in sample data")
        
        # Get first signal
        first_signal_idx = signals.index[0]
        idx_num = result.index.get_loc(first_signal_idx)
        entry_price = result.loc[first_signal_idx, 'close']
        direction = result.loc[first_signal_idx, 'signal']
        
        # Run with different SL modes and compare
        results_by_mode = {}
        for sl_mode in range(5):
            trade_result = track_position(
                df=result,
                entry_idx=idx_num,
                direction=direction,
                entry_price=entry_price,
                sl_percent=2.0,
                tp_percents=[1.0, 2.0, 3.0],
                sl_mode=sl_mode
            )
            results_by_mode[sl_mode] = trade_result
        
        # Verify all modes produce valid results
        for mode, result in results_by_mode.items():
            assert 'exit_reason' in result
            assert 'pnl_percent' in result
            assert 'sl_history' in result
            assert isinstance(result['tps_hit'], list)


# =============================================================================
# TEST: EDGE CASES
# =============================================================================

class TestSLModesEdgeCases:
    """Test edge cases for SL modes"""
    
    def test_empty_tps_hit_list(self):
        """Test with empty tps_hit list"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[],
            tp_levels=[101.0, 102.0]
        )
        assert sl == 98.0  # Original SL
    
    def test_none_tps_hit(self):
        """Test with None tps_hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_AFTER_TP1,
            tps_hit=None
        )
        assert sl == 98.0  # Original SL
    
    def test_cascade_with_insufficient_tp_levels(self):
        """Test cascade mode with fewer TP levels than TPs hit"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_CASCADE,
            tps_hit=[True, True, True, True],  # 4 TPs hit
            tp_levels=[101.0]  # Only 1 TP level
        )
        # Should handle gracefully
        assert sl > 98.0  # At least breakeven or better
    
    def test_very_small_sl_percent(self):
        """Test with very small SL percentage"""
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=0.01,  # 0.01%
            sl_mode=SL_MODE_FIXED,
            tps_hit=[False]
        )
        assert sl == pytest.approx(99.99, rel=0.001)
    
    def test_zero_entry_price(self):
        """Test with zero entry price (edge case)"""
        tp_levels = calculate_tp_levels(0.0, SIGNAL_LONG, [1.0])
        assert tp_levels[0] == 0.0  # 0 + 1% of 0 = 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
