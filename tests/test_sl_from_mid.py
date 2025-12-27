import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/claude')

from dominant import (
    track_position, SIGNAL_LONG, SIGNAL_SHORT,
    SL_MODE_FIXED, calculate_dominant
)

# Create test data with mid_channel
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=100, freq='1h')
base = 100
prices = base + np.cumsum(np.random.randn(100) * 0.5)

df = pd.DataFrame({
    'open': prices,
    'high': prices + np.abs(np.random.randn(100)),
    'low': prices - np.abs(np.random.randn(100)),
    'close': prices + np.random.randn(100) * 0.3,
    'volume': np.random.randint(1000, 10000, 100)
}, index=dates)

# Calculate mid_channel
df = calculate_dominant(df, sensitivity=21)

# Test entry
entry_idx = 20
entry_price = df.iloc[entry_idx]['close']
mid_channel = df.iloc[entry_idx]['mid_channel']

print(f"Entry price: {entry_price:.4f}")
print(f"Mid channel: {mid_channel:.4f}")
print()

# Test 1: fixed_stop=False (should use mid_channel)
result1 = track_position(
    df=df, entry_idx=entry_idx, direction=SIGNAL_LONG,
    entry_price=entry_price, sl_percent=2.0, sl_mode=SL_MODE_FIXED,
    fixed_stop=False
)
initial_sl_1 = result1['sl_history'][0][1]
expected_sl_1 = mid_channel * (1 - 2.0/100)
print(f"Test 1: fixed_stop=False (SL from mid_channel)")
print(f"  Initial SL: {initial_sl_1:.4f}")
print(f"  Expected:   {expected_sl_1:.4f}")
print(f"  Match: {abs(initial_sl_1 - expected_sl_1) < 0.0001}")
print()

# Test 2: fixed_stop=True (should use entry_price)
result2 = track_position(
    df=df, entry_idx=entry_idx, direction=SIGNAL_LONG,
    entry_price=entry_price, sl_percent=2.0, sl_mode=SL_MODE_FIXED,
    fixed_stop=True
)
initial_sl_2 = result2['sl_history'][0][1]
expected_sl_2 = entry_price * (1 - 2.0/100)
print(f"Test 2: fixed_stop=True (SL from entry_price)")
print(f"  Initial SL: {initial_sl_2:.4f}")
print(f"  Expected:   {expected_sl_2:.4f}")
print(f"  Match: {abs(initial_sl_2 - expected_sl_2) < 0.0001}")
print()

# Verify they're different
print(f"Difference between SL modes: {abs(initial_sl_1 - initial_sl_2):.4f}")
print(f"Are they different? {initial_sl_1 != initial_sl_2}")
