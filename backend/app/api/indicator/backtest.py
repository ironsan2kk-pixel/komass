"""
Backtest Engine
===============
Backtesting functions for indicator strategies.
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import IndicatorSettings

from .calculate import calculate_trg, calculate_supertrend, generate_signals


def run_backtest(
    df: pd.DataFrame,
    settings: "IndicatorSettings",
    adaptive_mode: str = None
) -> Tuple[List[Dict], List[Dict], Dict, Dict, List[Dict]]:
    """
    Run backtest with proper Partial TP Close and trailing SL

    Supports:
    - Leverage: multiplies PnL
    - Commission: deducted on entry and exit
    - Adaptive mode: re-optimize parameters during backtest

    Returns:
        trades, equity_curve, tp_stats, monthly_stats, param_changes
    """

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

    # Current active parameters
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

    # TP amounts
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

    total_commission_paid = 0.0
    position = None
    last_exit_reason = None
    last_exit_trend = None

    # Ensure indicators are calculated
    if 'trg_trend' not in df.columns:
        df = calculate_trg(df, active_i1, active_i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        df = generate_signals(df, settings)

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

        # Adaptive optimization
        if adaptive_mode and len(trades) > 0 and len(trades) - last_optimization_trade >= REOPTIMIZE_EVERY:
            if i > LOOKBACK_CANDLES:
                lookback_df = df.iloc[i - LOOKBACK_CANDLES:i].copy()
                new_params = optimize_on_lookback(
                    lookback_df, settings, adaptive_mode,
                    active_i1, active_i2, active_tp_levels, active_sl
                )

                if new_params:
                    params_changed = False

                    if adaptive_mode in ["indicator", "all"]:
                        if new_params.get('i1') != active_i1 or new_params.get('i2') != active_i2:
                            active_i1 = new_params.get('i1', active_i1)
                            active_i2 = new_params.get('i2', active_i2)
                            params_changed = True

                            remaining_df = df.iloc[i:].copy()
                            remaining_df = calculate_trg(remaining_df, active_i1, active_i2)
                            if settings.use_supertrend:
                                remaining_df = calculate_supertrend(
                                    remaining_df, settings.supertrend_period, settings.supertrend_multiplier
                                )
                            remaining_df = generate_signals(remaining_df, settings)

                            for col in remaining_df.columns:
                                df.loc[remaining_df.index, col] = remaining_df[col]

                    if adaptive_mode in ["tp", "all"]:
                        if new_params.get('tp_levels'):
                            active_tp_levels = new_params['tp_levels']
                            params_changed = True

                    if adaptive_mode == "all":
                        if new_params.get('sl') and new_params['sl'] != active_sl:
                            active_sl = new_params['sl']
                            params_changed = True

                    if params_changed:
                        param_changes.append({
                            "trade_num": len(trades),
                            "timestamp": timestamp.isoformat(),
                            "i1": active_i1,
                            "i2": active_i2,
                            "tp1": active_tp_levels[0] if active_tp_levels else None,
                            "sl": active_sl
                        })

                last_optimization_trade = len(trades)

        row = df.iloc[i]

        # Check position updates
        if position:
            high = row['high']
            low = row['low']
            close = row['close']

            if position['type'] == 'long':
                position['highest_price'] = max(position['highest_price'], high)
            else:
                position['lowest_price'] = min(position['lowest_price'], low)

            # Check TP levels
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

                    exit_commission = portion_size * (commission_pct / 100) if use_commission else 0
                    portion_pnl = portion_size * (portion_pnl_pct_leveraged / 100) - exit_commission
                    position['commission_paid'] = position.get('commission_paid', 0) + exit_commission

                    position['realized_pnl'] += portion_pnl
                    position['remaining_pct'] -= tp_amount_pct
                    position['tp_closed'].append(tp_idx)
                    position['tp_hit'].append(tp_idx + 1)

                    tp_stats[f"tp{tp_idx + 1}_hits"] += 1
                    monthly_stats[month_key][f"tp{tp_idx + 1}_hits"] = \
                        monthly_stats[month_key].get(f"tp{tp_idx + 1}_hits", 0) + 1

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
                    else:
                        exit_price = close

                    if position['type'] == 'long':
                        remaining_pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        remaining_pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100

                    remaining_pnl_pct_leveraged = remaining_pnl_pct * leverage
                    exit_commission = remaining_size * (commission_pct / 100) if use_commission else 0
                    remaining_pnl = remaining_size * (remaining_pnl_pct_leveraged / 100) - exit_commission
                    position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                    position['realized_pnl'] += remaining_pnl

                total_pnl = position['realized_pnl']
                total_pnl_pct = (total_pnl / position['entry_capital']) * 100
                total_commission = position.get('commission_paid', 0)
                total_commission_paid += total_commission

                capital += total_pnl

                if all_tp_closed:
                    exit_reason = f"TP{len(position['tp_closed'])}"
                elif sl_hit:
                    exit_reason = "SL"
                else:
                    exit_reason = "Reverse"

                tp_stats["total_trades"] += 1
                monthly_stats[month_key]["trades"] += 1
                monthly_stats[month_key]["pnl"] += total_pnl_pct
                monthly_stats[month_key]["pnl_amount"] += total_pnl

                if total_pnl > 0:
                    monthly_stats[month_key]["wins"] += 1
                else:
                    monthly_stats[month_key]["losses"] += 1

                if position['type'] == 'long':
                    monthly_stats[month_key]["long_trades"] += 1
                else:
                    monthly_stats[month_key]["short_trades"] += 1

                trade = {
                    "id": len(trades) + 1,
                    "type": position['type'],
                    "entry_time": position['entry_time'].isoformat(),
                    "entry_price": position['entry_price'],
                    "exit_time": timestamp.isoformat(),
                    "exit_price": exit_price if not all_tp_closed else position['tp_prices'][position['tp_closed'][-1]],
                    "pnl": round(total_pnl_pct, 2),
                    "pnl_amount": round(total_pnl, 2),
                    "exit_reason": exit_reason,
                    "tp_hit": position['tp_hit'],
                    "tp_levels": position['tp_prices'],
                    "sl_level": position['sl_price'],
                    "is_reentry": position.get('is_reentry', False),
                    "partial_closes": len(position['tp_closed']),
                    "params_used": {"i1": position.get('i1_used'), "i2": position.get('i2_used')},
                    "leverage": leverage,
                    "commission": round(total_commission, 4) if use_commission else 0
                }
                trades.append(trade)

                last_exit_reason = exit_reason
                last_exit_trend = current_trend
                position = None

        # Check entry
        if position is None:
            should_enter = False
            entry_type = None
            is_reentry = False

            if row['signal'] != 0:
                should_enter = True
                entry_type = "long" if row['signal'] == 1 else "short"

            elif settings.allow_reentry and last_exit_reason and last_exit_trend:
                can_reentry = False

                if last_exit_reason == "SL" and settings.reentry_after_sl:
                    if last_exit_trend == current_trend and current_trend != 0:
                        can_reentry = True

                if last_exit_reason and last_exit_reason.startswith("TP") and settings.reentry_after_tp:
                    if last_exit_trend == current_trend and current_trend != 0:
                        can_reentry = True

                if can_reentry:
                    should_enter = True
                    entry_type = "long" if current_trend == 1 else "short"
                    is_reentry = True
                    last_exit_reason = None

            if should_enter and entry_type:
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
                    "is_reentry": is_reentry,
                    "tp_levels_active": active_tp_levels.copy(),
                    "i1_used": active_i1,
                    "i2_used": active_i2
                }

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


def quick_backtest(
    df: pd.DataFrame,
    settings: "IndicatorSettings",
    tp_levels: list = None,
    sl_pct: float = None
) -> List[Dict]:
    """Simplified fast backtest for optimization"""

    if tp_levels is None:
        tp_levels = [
            settings.tp1_percent, settings.tp2_percent,
            settings.tp3_percent, settings.tp4_percent
        ][:settings.tp_count]
    if sl_pct is None:
        sl_pct = settings.sl_percent

    trades = []
    position = None

    for i in range(len(df)):
        row = df.iloc[i]

        if position:
            high, low, close = row['high'], row['low'], row['close']
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


def optimize_on_lookback(
    df: pd.DataFrame,
    settings: "IndicatorSettings",
    mode: str,
    current_i1: int,
    current_i2: float,
    current_tp: list,
    current_sl: float
) -> Dict:
    """Quick optimization on lookback period to find better parameters"""

    best_score = float('-inf')
    best_params = {}

    if mode in ["indicator", "all"]:
        i1_range = [30, 40, 45, 50, 60, 80]
        i2_range = [2, 3, 4, 5, 6]

        for i1 in i1_range:
            for i2 in i2_range:
                try:
                    test_df = df.copy()
                    test_df = calculate_trg(test_df, i1, i2)
                    if settings.use_supertrend:
                        test_df = calculate_supertrend(
                            test_df, settings.supertrend_period, settings.supertrend_multiplier
                        )
                    test_df = generate_signals(test_df, settings)

                    trades = quick_backtest(test_df, settings)
                    if trades:
                        total_pnl = sum(t['pnl'] for t in trades)
                        win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades)
                        score = total_pnl * (1 + win_rate)

                        if score > best_score:
                            best_score = score
                            best_params['i1'] = i1
                            best_params['i2'] = i2
                except Exception:
                    continue

    if mode in ["tp", "all"]:
        tp1_range = [0.5, 1.0, 1.5, 2.0]

        for tp1 in tp1_range:
            try:
                test_tp = [tp1, tp1 * 2, tp1 * 3, tp1 * 4][:settings.tp_count]

                test_df = df.copy()
                if 'signal' not in test_df.columns:
                    test_df = calculate_trg(test_df, current_i1, current_i2)
                    test_df = generate_signals(test_df, settings)

                trades = quick_backtest(test_df, settings, tp_levels=test_tp)
                if trades:
                    total_pnl = sum(t['pnl'] for t in trades)
                    if total_pnl > best_score:
                        best_score = total_pnl
                        best_params['tp_levels'] = test_tp
            except Exception:
                continue

    return best_params


def calculate_statistics(
    trades: List[Dict],
    equity_curve: List[Dict],
    settings: "IndicatorSettings",
    monthly_stats: Dict
) -> Dict:
    """Calculate comprehensive statistics"""

    if not trades:
        return {}

    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    long_trades = [t for t in trades if t['type'] == 'long']
    short_trades = [t for t in trades if t['type'] == 'short']
    reentry_trades = [t for t in trades if t.get('is_reentry', False)]

    long_wins = len([t for t in long_trades if t['pnl'] > 0])
    short_wins = len([t for t in short_trades if t['pnl'] > 0])
    reentry_wins = len([t for t in reentry_trades if t['pnl'] > 0])

    # TP accuracy
    accuracy = {"total": {}}
    for tp_num in range(1, settings.tp_count + 1):
        hits = len([t for t in trades if tp_num in t.get('tp_hit', [])])
        accuracy["total"][f"tp{tp_num}"] = round(hits / len(trades) * 100, 2) if trades else 0

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
        "short_win_rate": round(short_wins / len(short_trades) * 100, 2) if short_trades else 0,
        "reentry_trades": len(reentry_trades),
        "reentry_wins": reentry_wins,
        "reentry_win_rate": round(reentry_wins / len(reentry_trades) * 100, 2) if reentry_trades else 0,
        "accuracy": accuracy
    }


def build_monthly_stats(trades: List[Dict]) -> Dict:
    """Build monthly statistics from trades list"""
    if not trades:
        return {}

    monthly = {}
    for trade in trades:
        exit_time = trade.get('exit_time', '')
        if not exit_time:
            continue

        try:
            if isinstance(exit_time, str):
                month_key = exit_time[:7]
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
