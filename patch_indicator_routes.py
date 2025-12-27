#!/usr/bin/env python3
"""
Patch indicator_routes.py to add data_range support
Chat #18: Data Period Selection
"""
import re
import sys

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patch 1: After loading and sorting df, save full range BEFORE filtering
    # Find the pattern where we sort and then filter
    old_pattern1 = '''    df = pd.read_parquet(filepath)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Filter by date
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]'''
    
    new_pattern1 = '''    df = pd.read_parquet(filepath)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Save full data range BEFORE filtering
    data_range = {
        "available_start": df.index.min().strftime("%Y-%m-%d") if len(df) > 0 else None,
        "available_end": df.index.max().strftime("%Y-%m-%d") if len(df) > 0 else None,
        "total_candles": len(df)
    }
    
    # Filter by date
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]
    
    # Add used range info
    data_range["used_start"] = df.index.min().strftime("%Y-%m-%d") if len(df) > 0 else None
    data_range["used_end"] = df.index.max().strftime("%Y-%m-%d") if len(df) > 0 else None
    data_range["used_candles"] = len(df)'''
    
    if old_pattern1 in content:
        content = content.replace(old_pattern1, new_pattern1)
        print("[OK] Patched: Added data_range collection before/after filtering")
    else:
        print("[SKIP] Pattern 1 not found - may already be patched")
    
    # Patch 2: Add data_range to the return statement
    old_pattern2 = '''    return {
        "success": True,
        "candles": candles,
        "indicators": indicators,
        "trades": trades,
        "trade_markers": trade_markers,
        "equity_curve": equity_curve,
        "stats": stats,
        "tp_stats": tp_stats,
        "monthly": monthly_stats,
        "param_changes": param_changes,
        "settings": settings.dict()
    }'''
    
    new_pattern2 = '''    return {
        "success": True,
        "candles": candles,
        "indicators": indicators,
        "trades": trades,
        "trade_markers": trade_markers,
        "equity_curve": equity_curve,
        "stats": stats,
        "tp_stats": tp_stats,
        "monthly": monthly_stats,
        "param_changes": param_changes,
        "settings": settings.dict(),
        "data_range": data_range
    }'''
    
    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern2)
        print("[OK] Patched: Added data_range to return statement")
    else:
        print("[SKIP] Pattern 2 not found - may already be patched")
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[DONE] Patched {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python patch_indicator_routes.py <path_to_indicator_routes.py>")
        sys.exit(1)
    patch_file(sys.argv[1])
