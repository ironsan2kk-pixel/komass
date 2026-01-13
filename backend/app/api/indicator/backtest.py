"""
Backtest Engine Module
=======================

Backtest simulation with proper TP/SL handling, leverage, and commission.

Functions:
- run_backtest: Main backtest engine with adaptive optimization support
- quick_backtest: Fast backtest for optimization (simplified)
- check_exit: Check exit conditions for a position
- calculate_statistics: Calculate comprehensive statistics
- _build_monthly_stats: Build monthly breakdown statistics
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime


def run_backtest(df: pd.DataFrame, settings: Any, adaptive_mode: str = None) -> Tuple:
    """
    Main backtest engine with proper Partial TP Close and trailing SL

    Features:
    - Leverage: multiplies PnL (e.g., 10x leverage = 10x profits AND losses)
    - Commission: deducted on entry and exit (e.g., 0.1% per side = 0.2% round trip)
    - Partial TP closes: Close portions of position at multiple TP levels
    - Trailing SL: Breakeven or moving SL after TP hits
    - Adaptive optimization: Re-optimize parameters during backtest

    Args:
        df: DataFrame with OHLC and indicators already calculated
        settings: IndicatorSettings object
        adaptive_mode: None, "indicator", "tp", or "all"

    Returns:
        Tuple of (trades, equity_curve, tp_stats, monthly_stats, param_changes)
    """
    # Import calculate functions (circular import workaround)
    from .calculate import calculate_trg, calculate_supertrend, generate_signals

    trades = []
    equity_curve = []
    monthly_stats = {}
    capital = settings.initial_capital

    # Leverage and commission settings
    leverage = max(1.0, settings.leverage)
    use_commission = settings.use_commission
    commission_pct = settings.commission_percent if use_commission else 0.0

    # Adaptive optimization settings
    REOPTIMIZE_EVERY = 20
    LOOKBACK_CANDLES = 500

    # Active parameters (can change during backtest)
    active_i1 = settings.trg_atr_length
    active_i2 = settings.trg_multiplier
    active_tp_levels = [
        settings.tp1_percent, settings.tp2_percent, settings.tp3_percent,
        settings.tp4_percent, settings.tp5_percent, settings.tp6_percent,
        settings.tp7_percent, settings.tp8_percent, settings.tp9_percent,
        settings.tp10_percent
    ][:settings.tp_count]
    active_sl = settings.sl_percent

    param_changes = []
    last_optimization_trade = 0

    # TP amounts (fixed)
    tp_amounts = [
        settings.tp1_amount, settings.tp2_amount, settings.tp3_amount,
        settings.tp4_amount, settings.tp5_amount, settings.tp6_amount,
        settings.tp7_amount, settings.tp8_amount, settings.tp9_amount,
        settings.tp10_amount
    ][:settings.tp_count]

    total_amount = sum(tp_amounts)
    if total_amount > 0:
        tp_amounts = [a / total_amount * 100 for a in tp_amounts]

    # TP hit tracking
    tp_stats = {f"tp{i+1}_hits": 0 for i in range(settings.tp_count)}
    tp_stats["total_trades"] = 0

    position = None
    last_exit_reason = None
    last_exit_trend = None

    # Check if indicators already calculated
    if 'trg_trend' not in df.columns:
        df = calculate_trg(df, active_i1, active_i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        df = generate_signals(df, settings)

    # Main backtest loop
    for i in range(len(df)):
        row = df.iloc[i]
        timestamp = df.index[i]
        current_trend = int(row.get('trg_trend', 0))
        month_key = timestamp.strftime("%Y-%m")

        # Initialize month stats
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "trades": 0, "wins": 0, "losses": 0,
                "pnl": 0, "pnl_amount": 0,
                "long_trades": 0, "short_trades": 0,
                "tp1_hits": 0, "tp2_hits": 0, "tp3_hits": 0, "tp4_hits": 0
            }

        # === POSITION MANAGEMENT ===
        if position:
            high = row['high']
            low = row['low']
            close = row['close']

            # Update trailing prices
            if position['type'] == 'long':
                position['highest_price'] = max(position['highest_price'], high)
            else:
                position['lowest_price'] = min(position['lowest_price'], low)

            # Check each TP level (partial close)
            for tp_idx in range(len(position['tp_levels_active'])):
                if tp_idx in position['tp_closed']:
                    continue

                tp_price = position['tp_prices'][tp_idx]
                tp_amount_pct = tp_amounts[tp_idx]

                tp_hit = False
                if position['type'] == 'long' and high >= tp_price:
                    tp_hit = True
                elif position['type'] == 'short' and low <= tp_price:
                    tp_hit = True

                if tp_hit:
                    portion_size = position['entry_capital'] * (tp_amount_pct / 100)
                    portion_pnl_pct = position['tp_levels_active'][tp_idx]
                    portion_pnl_pct_leveraged = portion_pnl_pct * leverage

                    # Exit commission for this portion
                    exit_commission = portion_size * (commission_pct / 100) if use_commission else 0
                    portion_pnl = portion_size * (portion_pnl_pct_leveraged / 100) - exit_commission

                    position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                    position['realized_pnl'] += portion_pnl
                    position['remaining_pct'] -= tp_amount_pct
                    position['tp_closed'].append(tp_idx)
                    position['tp_hit'].append(tp_idx + 1)

                    tp_stats[f"tp{tp_idx + 1}_hits"] += 1
                    monthly_stats[month_key][f"tp{tp_idx + 1}_hits"] = monthly_stats[month_key].get(f"tp{tp_idx + 1}_hits", 0) + 1

                    # Update trailing SL
                    if settings.sl_trailing_mode == 'breakeven' and len(position['tp_closed']) == 1:
                        position['sl_price'] = position['entry_price']
                    elif settings.sl_trailing_mode == 'moving':
                        if len(position['tp_closed']) > 1:
                            prev_tp_idx = position['tp_closed'][-2]
                            position['sl_price'] = position['tp_prices'][prev_tp_idx]
                        else:
                            position['sl_price'] = position['entry_price']

            all_tp_closed = position['remaining_pct'] <= 0.01

            # Check SL
            sl_hit = False
            if position['type'] == 'long' and low <= position['sl_price']:
                sl_hit = True
            elif position['type'] == 'short' and high >= position['sl_price']:
                sl_hit = True

            # Check reverse signal
            reverse_signal = False
            if row['signal'] != 0:
                if (position['type'] == 'long' and row['signal'] == -1) or \
                   (position['type'] == 'short' and row['signal'] == 1):
                    reverse_signal = True

            # Close position
            if all_tp_closed or sl_hit or reverse_signal:
                if position['remaining_pct'] > 0.01:
                    remaining_size = position['entry_capital'] * (position['remaining_pct'] / 100)

                    if sl_hit:
                        exit_price = position['sl_price']
                        exit_reason = "SL"
                    else:
                        exit_price = close
                        exit_reason = "Reverse" if reverse_signal else "Final TP"

                    if position['type'] == 'long':
                        remaining_pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        remaining_pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100

                    remaining_pnl_pct_leveraged = remaining_pnl_pct * leverage
                    exit_commission = remaining_size * (commission_pct / 100) if use_commission else 0

                    remaining_pnl = remaining_size * (remaining_pnl_pct_leveraged / 100) - exit_commission
                    position['commission_paid'] += exit_commission
                    position['realized_pnl'] += remaining_pnl
                else:
                    exit_price = position['tp_prices'][-1]
                    exit_reason = f"TP{len(position['tp_hit'])}"

                # Record trade
                total_pnl = position['realized_pnl']
                capital += total_pnl

                trade = {
                    "type": position['type'],
                    "entry_time": position['entry_time'].isoformat(),
                    "exit_time": timestamp.isoformat(),
                    "entry_price": round(position['entry_price'], 8),
                    "exit_price": round(exit_price, 8),
                    "pnl": round(total_pnl, 2),
                    "pnl_pct": round(total_pnl / position['entry_capital'] * 100, 2),
                    "tp_hit": position['tp_hit'],
                    "exit_reason": exit_reason if 'exit_reason' in locals() else "All TPs",
                    "is_reentry": position.get('is_reentry', False),
                    "commission_paid": round(position['commission_paid'], 2)
                }
                trades.append(trade)

                # Update monthly stats
                monthly_stats[month_key]['trades'] += 1
                monthly_stats[month_key]['pnl'] += total_pnl
                if total_pnl > 0:
                    monthly_stats[month_key]['wins'] += 1
                else:
                    monthly_stats[month_key]['losses'] += 1

                last_exit_reason = exit_reason if 'exit_reason' in locals() else "All TPs"
                last_exit_trend = current_trend
                position = None

        # === NEW ENTRY ===
        if position is None and row.get('signal', 0) != 0:
            entry_type = "long" if row['signal'] == 1 else "short"
            entry_price = row['close']
            entry_capital = capital

            entry_commission = entry_capital * (commission_pct / 100) if use_commission else 0

            position = {
                "type": entry_type,
                "entry_time": timestamp,
                "entry_price": entry_price,
                "entry_capital": entry_capital,
                "remaining_pct": 100.0,
                "realized_pnl": -entry_commission,
                "commission_paid": entry_commission,
                "tp_closed": [],
                "tp_hit": [],
                "highest_price": entry_price,
                "lowest_price": entry_price,
                "is_reentry": False,
                "tp_levels_active": active_tp_levels.copy()
            }

            # Calculate TP/SL prices
            if position['type'] == 'long':
                position['tp_prices'] = [entry_price * (1 + tp/100) for tp in active_tp_levels]
                position['sl_price'] = entry_price * (1 - active_sl/100)
            else:
                position['tp_prices'] = [entry_price * (1 - tp/100) for tp in active_tp_levels]
                position['sl_price'] = entry_price * (1 + active_sl/100)

        equity_curve.append({
            "time": timestamp.isoformat(),
            "value": round(capital, 2)
        })

    return trades, equity_curve, tp_stats, monthly_stats, param_changes


def quick_backtest(df: pd.DataFrame, settings: Any,
                   tp_levels: list = None, sl_pct: float = None) -> list:
    """
    Simplified fast backtest for optimization

    Used during parameter optimization for speed.
    Only checks first TP and SL, no partial closes.

    Args:
        df: DataFrame with signals already generated
        settings: IndicatorSettings object
        tp_levels: Override TP percentages
        sl_pct: Override SL percentage

    Returns:
        List of trades with pnl
    """
    if tp_levels is None:
        tp_levels = [settings.tp1_percent, settings.tp2_percent,
                     settings.tp3_percent, settings.tp4_percent][:settings.tp_count]
    if sl_pct is None:
        sl_pct = settings.sl_percent

    trades = []
    position = None

    for i in range(len(df)):
        row = df.iloc[i]

        if position:
            high, low = row['high'], row['low']

            # Check TP1 hit (simplified)
            tp1_price = position['tp_price']
            sl_price = position['sl_price']

            exit_price = None
            if position['type'] == 'long':
                if high >= tp1_price:
                    exit_price = tp1_price
                    pnl = tp_levels[0]
                elif low <= sl_price:
                    exit_price = sl_price
                    pnl = -sl_pct
            else:
                if low <= tp1_price:
                    exit_price = tp1_price
                    pnl = tp_levels[0]
                elif high >= sl_price:
                    exit_price = sl_price
                    pnl = -sl_pct

            if exit_price:
                trades.append({"pnl": pnl})
                position = None

        if position is None and row.get('signal', 0) != 0:
            entry_price = row['close']
            position = {
                "type": "long" if row['signal'] == 1 else "short",
                "entry_price": entry_price,
            }

            if position['type'] == 'long':
                position['tp_price'] = entry_price * (1 + tp_levels[0]/100)
                position['sl_price'] = entry_price * (1 - sl_pct/100)
            else:
                position['tp_price'] = entry_price * (1 - tp_levels[0]/100)
                position['sl_price'] = entry_price * (1 + sl_pct/100)

    return trades


def check_exit(position: Dict, row: pd.Series, settings: Any,
               tp_levels: List[float], tp_amounts: List[float]) -> Tuple:
    """
    Check for exit conditions on a position

    Args:
        position: Current position dict
        row: Current candle data
        settings: IndicatorSettings
        tp_levels: TP percentages
        tp_amounts: TP amount percentages

    Returns:
        Tuple of (exit_price, exit_reason, tp_hit)
    """
    high = row['high']
    low = row['low']
    close = row['close']

    exit_price = None
    exit_reason = None
    tp_hit = list(position.get('tp_hit', []))

    # Update highest/lowest
    if position['type'] == 'long':
        position['highest_price'] = max(position['highest_price'], high)
    else:
        position['lowest_price'] = min(position['lowest_price'], low)

    # Check TPs
    for i, (tp_price, tp_amount) in enumerate(zip(position['tp_prices'], tp_amounts)):
        if i + 1 in tp_hit:
            continue

        hit = False
        if position['type'] == 'long' and high >= tp_price:
            hit = True
        elif position['type'] == 'short' and low <= tp_price:
            hit = True

        if hit:
            tp_hit.append(i + 1)
            position['tp_hit'] = tp_hit
            position['remaining_amount'] -= tp_amount

            # Update trailing SL
            if settings.sl_trailing_mode == 'breakeven' and len(tp_hit) >= 1:
                position['sl_price'] = position['entry_price']
            elif settings.sl_trailing_mode == 'moving' and len(tp_hit) >= 1:
                prev_tp = position['tp_prices'][len(tp_hit) - 1] if len(tp_hit) > 0 else position['entry_price']
                position['sl_price'] = prev_tp

            # Full exit if all TPs hit
            if position['remaining_amount'] <= 0 or len(tp_hit) >= len(tp_levels):
                exit_price = tp_price
                exit_reason = f"TP{len(tp_hit)}"
                return exit_price, exit_reason, tp_hit

    # Check SL
    sl_price = position['sl_price']
    if position['type'] == 'long' and low <= sl_price:
        exit_price = sl_price
        exit_reason = "SL"
    elif position['type'] == 'short' and high >= sl_price:
        exit_price = sl_price
        exit_reason = "SL"

    # Check reverse signal
    if row['signal'] != 0:
        if (position['type'] == 'long' and row['signal'] == -1) or \
           (position['type'] == 'short' and row['signal'] == 1):
            exit_price = close
            exit_reason = "Reverse"

    return exit_price, exit_reason, tp_hit


def _build_monthly_stats(trades: List[Dict]) -> Dict:
    """
    Build monthly statistics from trades list

    Args:
        trades: List of trade dicts

    Returns:
        Dict of monthly stats keyed by "YYYY-MM"
    """
    if not trades:
        return {}

    monthly = {}
    for trade in trades:
        exit_time = trade.get('exit_time', '')
        if not exit_time:
            continue

        try:
            if isinstance(exit_time, str):
                month_key = exit_time[:7]  # "2024-01"
            else:
                month_key = exit_time.strftime("%Y-%m")
        except:
            continue

        if month_key not in monthly:
            monthly[month_key] = {
                'month': month_key,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'pnl': 0.0,
                'pnl_pct': 0.0
            }

        monthly[month_key]['trades'] += 1
        pnl = trade.get('pnl', 0) or 0
        monthly[month_key]['pnl'] += pnl
        monthly[month_key]['pnl_pct'] += pnl

        if pnl > 0:
            monthly[month_key]['wins'] += 1
        elif pnl < 0:
            monthly[month_key]['losses'] += 1

    return monthly


def calculate_statistics(trades: List[Dict], equity_curve: List[Dict],
                         settings: Any, monthly_stats: Dict) -> Dict:
    """
    Calculate comprehensive statistics

    Calculates:
    - Win rate, profit factor, Sharpe ratio
    - Max drawdown, recovery factor
    - Long/short performance breakdown
    - TP hit rates and accuracy by recency
    - Profit panel per TP level

    Args:
        trades: List of completed trades
        equity_curve: Equity curve points
        settings: IndicatorSettings
        monthly_stats: Monthly breakdown (can be empty)

    Returns:
        Dict of statistics
    """
    if not trades:
        return {}

    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    long_trades = [t for t in trades if t['type'] == 'long']
    short_trades = [t for t in trades if t['type'] == 'short']

    long_wins = len([t for t in long_trades if t['pnl'] > 0])
    short_wins = len([t for t in short_trades if t['pnl'] > 0])

    # Max drawdown
    peak = settings.initial_capital
    max_dd = 0
    for eq in equity_curve:
        if eq['value'] > peak:
            peak = eq['value']
        dd = (peak - eq['value']) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio
    sharpe = None
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            prev_val = equity_curve[i-1]['value']
            curr_val = equity_curve[i]['value']
            if prev_val > 0:
                returns.append((curr_val - prev_val) / prev_val)
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5
            if std_return > 0:
                sharpe = round((avg_return / std_return) * (252 ** 0.5), 2)

    # Recovery factor
    total_profit = equity_curve[-1]['value'] - settings.initial_capital if equity_curve else 0
    recovery_factor = round(total_profit / (settings.initial_capital * max_dd / 100), 2) if max_dd > 0 else None

    return {
        "total_trades": len(trades),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": round(len(wins) / len(trades) * 100, 2) if trades else 0,
        "total_pnl": round(sum(pnls), 2),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else 999,
        "max_drawdown": round(max_dd, 2),
        "initial_capital": settings.initial_capital,
        "final_capital": round(equity_curve[-1]['value'], 2) if equity_curve else settings.initial_capital,
        "profit_pct": round((equity_curve[-1]['value'] / settings.initial_capital - 1) * 100, 2) if equity_curve else 0,
        "sharpe": sharpe,
        "recovery_factor": recovery_factor,
        "long_trades": len(long_trades),
        "long_wins": long_wins,
        "long_win_rate": round(long_wins / len(long_trades) * 100, 2) if long_trades else 0,
        "short_trades": len(short_trades),
        "short_wins": short_wins,
        "short_win_rate": round(short_wins / len(short_trades) * 100, 2) if short_trades else 0
    }
