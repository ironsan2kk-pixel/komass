"""
Tests for TRG Trading System
============================
Comprehensive tests for trading.py module.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np

# Import trading module
from indicators.plugins.trg.trading import (
    PositionType, TrailingMode, ExitReason,
    TakeProfitLevel, TRGTradingConfig, Position, Trade,
    TRGTradingSystem, create_trading_system, run_trading_simulation
)


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    detail_str = f" - {details}" if details else ""
    print(f"  {status}: {name}{detail_str}")
    return passed


def create_test_data(n_bars: int = 100) -> pd.DataFrame:
    """Create test OHLCV data with signals"""
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=n_bars, freq='1h')
    
    # Generate price data
    base_price = 100.0
    returns = np.random.randn(n_bars) * 0.01
    closes = base_price * np.exp(np.cumsum(returns))
    
    highs = closes * (1 + np.abs(np.random.randn(n_bars)) * 0.005)
    lows = closes * (1 - np.abs(np.random.randn(n_bars)) * 0.005)
    opens = closes * (1 + np.random.randn(n_bars) * 0.002)
    
    # Generate trend and signals
    trend = np.zeros(n_bars, dtype=int)
    signal = np.zeros(n_bars, dtype=int)
    
    # Simple trend pattern
    for i in range(n_bars):
        if i < 20:
            trend[i] = 1
        elif i < 40:
            trend[i] = -1
        elif i < 60:
            trend[i] = 1
        elif i < 80:
            trend[i] = -1
        else:
            trend[i] = 1
    
    # Generate signals at trend changes
    for i in range(1, n_bars):
        if trend[i] != trend[i-1]:
            signal[i] = trend[i]
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': np.random.rand(n_bars) * 1000000,
        'trg_trend': trend,
        'signal': signal
    }, index=dates)
    
    return df


class TestEnums:
    """Test enum classes"""
    
    @staticmethod
    def run():
        print("\n=== Testing Enums ===")
        passed = 0
        total = 0
        
        # TrailingMode
        total += 1
        if print_test(
            "TrailingMode.from_string('breakeven')",
            TrailingMode.from_string('breakeven') == TrailingMode.BREAKEVEN
        ):
            passed += 1
        
        total += 1
        if print_test(
            "TrailingMode.from_string('no')",
            TrailingMode.from_string('no') == TrailingMode.FIXED
        ):
            passed += 1
        
        total += 1
        if print_test(
            "TrailingMode.from_string('moving')",
            TrailingMode.from_string('moving') == TrailingMode.CASCADE
        ):
            passed += 1
        
        # ExitReason
        total += 1
        if print_test(
            "ExitReason.from_tp_index(1)",
            ExitReason.from_tp_index(1) == ExitReason.TP1
        ):
            passed += 1
        
        total += 1
        if print_test(
            "ExitReason.from_tp_index(5)",
            ExitReason.from_tp_index(5) == ExitReason.TP5
        ):
            passed += 1
        
        return passed, total


class TestTakeProfitLevel:
    """Test TakeProfitLevel class"""
    
    @staticmethod
    def run():
        print("\n=== Testing TakeProfitLevel ===")
        passed = 0
        total = 0
        
        # Long position
        total += 1
        tp = TakeProfitLevel(index=1, percent=2.0, amount=50.0)
        price = tp.calculate_price(100.0, is_long=True)
        if print_test(
            "Long TP price calculation",
            abs(price - 102.0) < 0.01,
            f"Expected 102.0, got {price}"
        ):
            passed += 1
        
        # Short position
        total += 1
        tp = TakeProfitLevel(index=1, percent=2.0, amount=50.0)
        price = tp.calculate_price(100.0, is_long=False)
        if print_test(
            "Short TP price calculation",
            abs(price - 98.0) < 0.01,
            f"Expected 98.0, got {price}"
        ):
            passed += 1
        
        return passed, total


class TestTRGTradingConfig:
    """Test TRGTradingConfig class"""
    
    @staticmethod
    def run():
        print("\n=== Testing TRGTradingConfig ===")
        passed = 0
        total = 0
        
        # Default config
        total += 1
        config = TRGTradingConfig()
        if print_test(
            "Default config creation",
            config.tp_count == 4 and config.sl_percent == 6.0
        ):
            passed += 1
        
        # From dict
        total += 1
        data = {
            'tp_count': 3,
            'tp1_percent': 1.0,
            'tp2_percent': 2.0,
            'tp3_percent': 3.0,
            'tp1_amount': 40.0,
            'tp2_amount': 40.0,
            'tp3_amount': 20.0,
            'sl_percent': 5.0,
            'sl_trailing_mode': 'breakeven',
            'leverage': 10.0,
            'use_commission': True,
            'commission_percent': 0.05
        }
        config = TRGTradingConfig.from_dict(data)
        if print_test(
            "Config from dict",
            config.tp_count == 3 and config.leverage == 10.0 and config.use_commission
        ):
            passed += 1
        
        # Get TP levels
        total += 1
        levels = config.get_tp_levels()
        if print_test(
            "Get TP levels",
            len(levels) == 3 and levels[0].percent == 1.0
        ):
            passed += 1
        
        # Normalize amounts
        total += 1
        amounts = config.normalize_tp_amounts()
        if print_test(
            "Normalize TP amounts",
            abs(sum(amounts) - 100.0) < 0.01,
            f"Sum = {sum(amounts)}"
        ):
            passed += 1
        
        return passed, total


class TestPosition:
    """Test Position class"""
    
    @staticmethod
    def run():
        print("\n=== Testing Position ===")
        passed = 0
        total = 0
        
        # Create position
        total += 1
        pos = Position(
            type=PositionType.LONG,
            entry_time=datetime.now(),
            entry_price=100.0,
            entry_capital=10000.0
        )
        if print_test(
            "Position creation",
            pos.is_long and not pos.is_short and pos.remaining_pct == 100.0
        ):
            passed += 1
        
        # Update trailing prices
        total += 1
        pos.update_trailing_prices(105.0, 99.0)
        if print_test(
            "Update trailing prices",
            pos.highest_price == 105.0 and pos.lowest_price == 99.0
        ):
            passed += 1
        
        return passed, total


class TestTRGTradingSystem:
    """Test TRGTradingSystem class"""
    
    @staticmethod
    def run():
        print("\n=== Testing TRGTradingSystem ===")
        passed = 0
        total = 0
        
        # Create system
        total += 1
        config = TRGTradingConfig()
        system = TRGTradingSystem(config)
        if print_test(
            "System creation",
            system.capital == 10000.0 and system.position is None
        ):
            passed += 1
        
        # Open position via check_entry
        total += 1
        timestamp = datetime(2024, 1, 1, 12, 0)
        opened = system.check_entry(
            signal=1,
            current_trend=1,
            timestamp=timestamp,
            close_price=100.0,
            i1=45,
            i2=4.0
        )
        if print_test(
            "Open position on signal",
            opened and system.position is not None
        ):
            passed += 1
        
        # Verify position details
        total += 1
        if system.position:
            pos = system.position
            sl_expected = 100.0 * (1 - 6.0 / 100)  # 94.0
            if print_test(
                "Position details",
                pos.is_long and abs(pos.sl_price - sl_expected) < 0.01,
                f"SL={pos.sl_price}, expected {sl_expected}"
            ):
                passed += 1
        else:
            print_test("Position details", False, "Position is None")
        
        # TP prices
        total += 1
        if system.position:
            tp_prices = system.position.tp_prices
            expected_tp1 = 100.0 * (1 + 1.05 / 100)  # 101.05
            if print_test(
                "TP prices calculated",
                abs(tp_prices[0] - expected_tp1) < 0.01,
                f"TP1={tp_prices[0]}, expected {expected_tp1}"
            ):
                passed += 1
        else:
            print_test("TP prices calculated", False, "Position is None")
        
        # Simulate TP1 hit (only TP1, not TP2+)
        total += 1
        if system.position:
            # Move price above TP1 (101.05) but below TP2 (101.95)
            trade = system.check_exit(
                high=101.5,  # Above TP1 (101.05) but below TP2 (101.95)
                low=100.5,
                close=101.2,
                signal=0,
                timestamp=datetime(2024, 1, 1, 14, 0),
                current_trend=1
            )
            # Position should still be open (partial close) - TP1 only takes 50%
            if print_test(
                "TP1 partial close",
                system.position is not None and 1 in system.position.tp_hit,
                f"TP hit: {system.position.tp_hit if system.position else 'None'}"
            ):
                passed += 1
        else:
            print_test("TP1 partial close", False, "Position was None")
        
        # Check SL updated to breakeven
        total += 1
        if system.position:
            if print_test(
                "SL moved to breakeven",
                abs(system.position.sl_price - 100.0) < 0.01,
                f"SL={system.position.sl_price}, expected 100.0"
            ):
                passed += 1
        else:
            print_test("SL moved to breakeven", False, "Position was None")
        
        # Reset and test full close on SL
        total += 1
        system.reset()
        system.check_entry(1, 1, timestamp, 100.0)
        if system.position:
            trade = system.check_exit(
                high=100.5,
                low=93.0,  # Below SL (94.0)
                close=93.5,
                signal=0,
                timestamp=datetime(2024, 1, 1, 15, 0),
                current_trend=1
            )
            if print_test(
                "Close on SL hit",
                trade is not None and trade.exit_reason == "SL",
                f"Exit reason: {trade.exit_reason if trade else 'None'}"
            ):
                passed += 1
        else:
            print_test("Close on SL hit", False, "Failed to open position")
        
        # Test re-entry
        total += 1
        if system.last_exit_reason == "SL":
            opened = system.check_entry(
                signal=0,  # No new signal
                current_trend=1,  # Same trend as before
                timestamp=datetime(2024, 1, 1, 16, 0),
                close_price=95.0
            )
            if print_test(
                "Re-entry after SL",
                opened and system.position is not None and system.position.is_reentry,
                f"Re-entry: {system.position.is_reentry if system.position else 'N/A'}"
            ):
                passed += 1
        else:
            print_test("Re-entry after SL", False, "Last exit was not SL")
        
        return passed, total


class TestIntegration:
    """Integration tests with DataFrame simulation"""
    
    @staticmethod
    def run():
        print("\n=== Testing Integration ===")
        passed = 0
        total = 0
        
        # Run full simulation
        total += 1
        df = create_test_data(100)
        settings = {
            'tp_count': 4,
            'tp1_percent': 1.0,
            'tp2_percent': 2.0,
            'tp3_percent': 3.0,
            'tp4_percent': 5.0,
            'tp1_amount': 50.0,
            'tp2_amount': 30.0,
            'tp3_amount': 15.0,
            'tp4_amount': 5.0,
            'sl_percent': 5.0,
            'sl_trailing_mode': 'breakeven',
            'leverage': 1.0,
            'initial_capital': 10000.0
        }
        
        trades, equity, summary = run_trading_simulation(df, settings)
        
        if print_test(
            "Full simulation run",
            isinstance(trades, list) and isinstance(equity, list) and isinstance(summary, dict),
            f"Trades: {len(trades)}, Equity points: {len(equity)}"
        ):
            passed += 1
        
        # Check summary structure
        total += 1
        required_keys = ['total_trades', 'capital', 'pnl', 'pnl_pct']
        has_keys = all(k in summary for k in required_keys)
        if print_test(
            "Summary has required keys",
            has_keys,
            f"Keys: {list(summary.keys())}"
        ):
            passed += 1
        
        # Check trade structure
        total += 1
        if trades:
            trade = trades[0]
            trade_keys = ['id', 'type', 'entry_price', 'exit_price', 'pnl', 'exit_reason']
            has_trade_keys = all(k in trade for k in trade_keys)
            if print_test(
                "Trade has required keys",
                has_trade_keys,
                f"Trade keys: {list(trade.keys())}"
            ):
                passed += 1
        else:
            print_test("Trade has required keys", False, "No trades generated")
        
        # Check equity curve
        total += 1
        if equity:
            eq_point = equity[0]
            has_eq_keys = 'time' in eq_point and 'value' in eq_point
            if print_test(
                "Equity point structure",
                has_eq_keys,
                f"Equity keys: {list(eq_point.keys())}"
            ):
                passed += 1
        else:
            print_test("Equity point structure", False, "No equity points")
        
        # Test with leverage
        total += 1
        settings['leverage'] = 10.0
        trades2, equity2, summary2 = run_trading_simulation(df, settings)
        
        if print_test(
            "Simulation with leverage",
            isinstance(trades2, list),
            f"Trades with 10x: {len(trades2)}"
        ):
            passed += 1
        
        # Test with commission
        total += 1
        settings['use_commission'] = True
        settings['commission_percent'] = 0.1
        trades3, equity3, summary3 = run_trading_simulation(df, settings)
        
        if print_test(
            "Simulation with commission",
            'commission_paid' in summary3,
            f"Commission paid: {summary3.get('commission_paid', 'N/A')}"
        ):
            passed += 1
        
        return passed, total


class TestHelperFunctions:
    """Test helper functions"""
    
    @staticmethod
    def run():
        print("\n=== Testing Helper Functions ===")
        passed = 0
        total = 0
        
        # create_trading_system
        total += 1
        settings = {
            'tp_count': 3,
            'sl_percent': 4.0,
            'leverage': 5.0
        }
        system = create_trading_system(settings)
        if print_test(
            "create_trading_system",
            system.config.tp_count == 3 and system.config.leverage == 5.0
        ):
            passed += 1
        
        return passed, total


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("TRG TRADING SYSTEM TESTS")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Run each test class
    test_classes = [
        TestEnums,
        TestTakeProfitLevel,
        TestTRGTradingConfig,
        TestPosition,
        TestTRGTradingSystem,
        TestIntegration,
        TestHelperFunctions,
    ]
    
    for test_class in test_classes:
        passed, total = test_class.run()
        total_passed += passed
        total_tests += total
    
    # Summary
    print("\n" + "=" * 60)
    print(f"TOTAL: {total_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {total_tests - total_passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
