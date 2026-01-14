#!/usr/bin/env python
"""
Seed Dominant Presets Script
============================
Seeds the database with 125+ Dominant presets from GG Pine Script.

Run:
    python seed_presets.py
    
Or via API after server is running:
    POST http://localhost:8000/api/presets/dominant/seed
"""
import sys
import os

# Add app directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, 'backend')
app_dir = os.path.join(backend_dir, 'app')

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def main():
    print("=" * 50)
    print("KOMAS - Seeding Dominant Presets")
    print("=" * 50)
    print()
    
    try:
        # Ensure database table exists
        from app.database.presets_db import ensure_presets_table
        ensure_presets_table()
        print("[OK] Presets table ready")
        
        # Seed presets
        from app.migrations.seed_dominant_presets import seed_all_dominant_presets
        result = seed_all_dominant_presets()
        
        print()
        print("-" * 30)
        print(f"Created: {result.get('created', 0)}")
        print(f"Skipped: {result.get('skipped', 0)}")
        print(f"Errors:  {result.get('errors', 0)}")
        print("-" * 30)
        print()
        
        # Verify count
        from app.database.presets_db import count_presets
        total = count_presets(indicator_type="dominant")
        print(f"Total Dominant presets in DB: {total}")
        print()
        print("=" * 50)
        print("SUCCESS! Presets seeded.")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
