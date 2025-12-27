"""
Generate Dominant Presets Script
================================
Run this script to generate Dominant system presets if they don't exist.

Usage:
    python generate_dominant_presets.py [--replace]
    
Options:
    --replace   Replace existing presets (delete first, then create)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    replace = '--replace' in sys.argv
    
    print("=" * 50)
    print("Dominant Presets Generator")
    print("=" * 50)
    print()
    
    # Check if presets module is available
    try:
        from app.presets import DominantPreset
        print("[OK] Presets module loaded")
    except ImportError as e:
        print(f"[ERROR] Cannot import presets module: {e}")
        print("Please ensure the presets module is properly installed.")
        return 1
    
    # Check if database module is available
    try:
        from app.database.presets_db import (
            create_preset,
            list_presets,
            count_presets,
            delete_presets_by_indicator,
            ensure_presets_table
        )
        print("[OK] Database module loaded")
    except ImportError as e:
        print(f"[ERROR] Cannot import database module: {e}")
        return 1
    
    # Ensure table exists
    try:
        ensure_presets_table()
        print("[OK] Database table ready")
    except Exception as e:
        print(f"[ERROR] Cannot initialize table: {e}")
        return 1
    
    # Check current count
    current_count = count_presets(indicator_type="dominant")
    print(f"[INFO] Current Dominant presets: {current_count}")
    
    if current_count > 0 and not replace:
        print()
        print(f"Dominant presets already exist ({current_count}).")
        print("Use --replace flag to regenerate.")
        return 0
    
    # Delete existing if replace mode
    if replace and current_count > 0:
        print()
        print("[INFO] Deleting existing presets...")
        deleted = delete_presets_by_indicator("dominant", source="system")
        print(f"[OK] Deleted {deleted} presets")
    
    # Generate presets
    print()
    print("[INFO] Generating Dominant presets...")
    
    created = 0
    skipped = 0
    errors = 0
    
    try:
        preset_list = list(DominantPreset.generate_system_presets())
        total = len(preset_list)
        print(f"[INFO] Total presets to create: {total}")
        
        for i, preset in enumerate(preset_list):
            try:
                is_valid, validation_errors = preset.validate()
                if not is_valid:
                    errors += 1
                    continue
                
                try:
                    create_preset(
                        preset_id=preset.id,
                        name=preset.name,
                        indicator_type=preset.config.indicator_type,
                        params=preset.params,
                        category=preset.config.category,
                        source=preset.config.source,
                        description=preset.config.description,
                        tags=preset.config.tags,
                    )
                    created += 1
                except ValueError as e:
                    if "already exists" in str(e):
                        skipped += 1
                    else:
                        errors += 1
                        print(f"  [ERROR] {preset.id}: {e}")
                
                # Progress
                if (i + 1) % 25 == 0 or (i + 1) == total:
                    pct = round((i + 1) / total * 100)
                    print(f"  Progress: {i + 1}/{total} ({pct}%) - Created: {created}, Skipped: {skipped}, Errors: {errors}")
                
            except Exception as e:
                errors += 1
                print(f"  [ERROR] Preset {i}: {e}")
    
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}")
        return 1
    
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Created:  {created}")
    print(f"Skipped:  {skipped}")
    print(f"Errors:   {errors}")
    print(f"Total:    {created + skipped + errors}")
    print()
    
    # Verify final count
    final_count = count_presets(indicator_type="dominant")
    print(f"Final Dominant presets in DB: {final_count}")
    
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
