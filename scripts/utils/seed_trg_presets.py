"""
Komas Trading Server - TRG Preset Seeder
========================================
Command-line script to seed all 200 TRG system presets.

Usage:
    python seed_trg_presets.py [options]

Options:
    --replace    Delete existing TRG system presets before seeding
    --verify     Only verify existing presets, don't seed
    --stats      Show preset statistics only
    --quiet      Minimal output

Chat: #30 — Presets TRG Generator
"""

import sys
import argparse
import time


def print_header():
    """Print script header"""
    print()
    print("=" * 60)
    print("  KOMAS TRG Preset Seeder")
    print("  200 System Presets (8 x 5 x 5)")
    print("=" * 60)
    print()


def seed_presets(replace: bool = False, quiet: bool = False):
    """Seed all 200 TRG system presets"""
    from app.presets import TRGPreset, FilterProfile
    from app.database.trg_presets_db import (
        ensure_trg_presets_table,
        create_trg_preset,
        delete_trg_system_presets,
        count_trg_presets
    )
    
    ensure_trg_presets_table()
    
    # Check existing
    existing = count_trg_presets(source="system")
    if not quiet:
        print(f"Existing TRG system presets: {existing}")
    
    # Delete if replacing
    if replace and existing > 0:
        if not quiet:
            print(f"\nDeleting {existing} existing TRG system presets...")
        deleted = delete_trg_system_presets()
        if not quiet:
            print(f"Deleted {deleted} presets")
    
    # Generate presets
    total = len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES)
    if not quiet:
        print(f"\nGenerating {total} TRG system presets...")
        print()
    
    created = 0
    skipped = 0
    errors = 0
    error_list = []
    
    start_time = time.time()
    current = 0
    
    for i1 in TRGPreset.I1_VALUES:
        for i2 in TRGPreset.I2_VALUES:
            for profile in TRGPreset.FILTER_PROFILES:
                current += 1
                
                try:
                    # Create preset instance
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    
                    # Validate
                    is_valid, validation_errors = preset.validate()
                    if not is_valid:
                        errors += 1
                        error_list.append(f"{preset.id}: {validation_errors}")
                        continue
                    
                    # Save to database
                    try:
                        create_trg_preset(
                            preset_id=preset.id,
                            name=preset.name,
                            params=preset.params,
                            category=preset.config.category,
                            description=preset.config.description,
                            source=preset.config.source,
                            tags=preset.config.tags,
                        )
                        created += 1
                    except ValueError as e:
                        if "already exists" in str(e):
                            skipped += 1
                        else:
                            errors += 1
                            error_list.append(f"{preset.id}: {e}")
                    except Exception as e:
                        errors += 1
                        error_list.append(f"{preset.id}: {e}")
                
                except Exception as e:
                    errors += 1
                    error_list.append(f"i1={i1}, i2={i2}, filter={profile.value}: {e}")
                
                # Progress
                if not quiet:
                    percent = round(current / total * 100)
                    bar_len = 40
                    filled = int(bar_len * current / total)
                    bar = "#" * filled + "-" * (bar_len - filled)
                    print(f"\r  [{bar}] {percent}% ({current}/{total})", end="", flush=True)
    
    elapsed = time.time() - start_time
    
    if not quiet:
        print()
        print()
        print("-" * 40)
        print(f"  Created:  {created}")
        print(f"  Skipped:  {skipped}")
        print(f"  Errors:   {errors}")
        print(f"  Time:     {elapsed:.2f}s")
        print("-" * 40)
    
    if errors > 0 and not quiet:
        print("\nFirst 5 errors:")
        for err in error_list[:5]:
            print(f"  - {err}")
    
    return created, skipped, errors


def verify_presets(quiet: bool = False):
    """Verify all TRG system presets"""
    from app.database.trg_presets_db import verify_trg_system_presets, ensure_trg_presets_table
    
    ensure_trg_presets_table()
    
    if not quiet:
        print("Verifying TRG system presets...")
        print()
    
    result = verify_trg_system_presets()
    
    if not quiet:
        print(f"Expected: {result['expected']}")
        print(f"Found:    {result['found']}")
        print(f"Missing:  {result['missing_count']}")
        print(f"Invalid:  {result['invalid_count']}")
        print()
        
        if result['missing']:
            print(f"Missing presets ({result['missing_count']}):")
            for name in result['missing'][:10]:
                print(f"  - {name}")
            if result['missing_count'] > 10:
                print(f"  ... and {result['missing_count'] - 10} more")
        
        if result['invalid']:
            print(f"\nInvalid presets ({result['invalid_count']}):")
            for preset_id in result['invalid'][:10]:
                print(f"  - {preset_id}")
        
        print()
        if result['is_valid']:
            print("[OK] All TRG system presets verified!")
        else:
            print("[FAIL] Verification failed - run with --replace to fix")
    
    return result['is_valid']


def show_stats():
    """Show preset statistics"""
    from app.database.trg_presets_db import get_trg_preset_stats, ensure_trg_presets_table
    
    ensure_trg_presets_table()
    stats = get_trg_preset_stats()
    
    print("TRG Preset Statistics")
    print("-" * 40)
    print(f"Total presets:     {stats['total_presets']}")
    print(f"Expected system:   {stats['expected_system']}")
    print(f"System complete:   {'Yes' if stats['system_complete'] else 'No'}")
    print()
    
    print("By source:")
    for src, count in stats.get('by_source', {}).items():
        print(f"  {src}: {count}")
    
    print()
    print("By category:")
    for cat, count in stats.get('by_category', {}).items():
        print(f"  {cat}: {count}")
    
    print()
    print(f"Active:     {stats.get('active_count', 0)}")
    print(f"Favorites:  {stats.get('favorites_count', 0)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="KOMAS TRG Preset Seeder - Generate 200 system presets"
    )
    parser.add_argument(
        "--replace", 
        action="store_true",
        help="Delete existing TRG system presets before seeding"
    )
    parser.add_argument(
        "--verify",
        action="store_true", 
        help="Only verify existing presets, don't seed"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show preset statistics only"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_header()
    
    try:
        if args.stats:
            show_stats()
        elif args.verify:
            success = verify_presets(quiet=args.quiet)
            sys.exit(0 if success else 1)
        else:
            created, skipped, errors = seed_presets(
                replace=args.replace,
                quiet=args.quiet
            )
            
            if not args.quiet:
                print()
                if errors == 0 and created > 0:
                    print("[OK] Seeding completed successfully!")
                elif errors == 0 and skipped > 0 and created == 0:
                    print("[OK] All presets already exist (use --replace to regenerate)")
                else:
                    print("[FAIL] Seeding completed with errors")
            
            sys.exit(0 if errors == 0 else 1)
    
    except ImportError as e:
        print(f"\nError: Failed to import required modules: {e}")
        print("Make sure you're running from the backend directory")
        print("and the virtual environment is activated.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
