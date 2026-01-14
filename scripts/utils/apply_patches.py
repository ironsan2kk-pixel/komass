"""
KOMAS Chat #16: Backend Bug Fixes
=================================
Patches for:
1. Duplicate timestamp handling
2. UTF-8 encoding fixes (mojibake)
3. Additional data validation in /replay endpoint
"""
import re
import os
from pathlib import Path

def patch_indicator_routes():
    """Patch indicator_routes.py with fixes"""
    filepath = Path("backend/app/api/indicator_routes.py")
    if not filepath.exists():
        # Try relative path
        filepath = Path("app/api/indicator_routes.py")
        if not filepath.exists():
            print(f"[SKIP] indicator_routes.py not found")
            return False
    
    content = filepath.read_text(encoding='utf-8', errors='replace')
    original_content = content
    changes_made = 0
    
    # Fix 1: Replace mojibake text patterns
    mojibake_fixes = [
        # Russian error messages -> English
        (r'Ð"Ð°Ð½Ð½Ñ‹Ðµ Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½Ñ‹ Ð´Ð»Ñ', 'Data not found for'),
        (r'ÐŸÐµÑ€ÐµÐ¹Ð´Ð¸Ñ‚Ðµ Ð² Ñ€Ð°Ð·Ð´ÐµÐ» \'Ð"Ð°Ð½Ð½Ñ‹Ðµ\' Ð¸ ÑÐºÐ°Ñ‡Ð°Ð¹Ñ‚Ðµ Ð¸ÑÑ‚Ð¾Ñ€Ð¸ÑŽ', 
         'Go to Data section and download history'),
        (r'ÐžÑˆÐ¸Ð±ÐºÐ°:', 'Error:'),
        
        # Comments
        (r'Ð²Ð°Ð¶Ð½Ð¾ Ð´Ð»Ñ BE ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸', 'important for BE strategy'),
        (r'ÐºÑ€Ð¸Ñ‚Ð¸Ñ‡Ð½Ð¾ Ð´Ð»Ñ BE ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¸', 'critical for BE strategy'),
        
        # SSE messages
        (r'Ð—Ð°Ð³Ñ€ÑƒÐ¶ÐµÐ½Ð¾', 'Loaded'),
        (r'ÑÐ²ÐµÑ‡ÐµÐ¹', 'candles'),
        (r'Ð Ð°ÑÑ‡Ñ'Ñ‚ Ñ‚ÐµÐºÑƒÑ‰Ð¸Ñ… Ð¿Ð°Ñ€Ð°Ð¼ÐµÑ‚Ñ€Ð¾Ð²', 'Calculating current params'),
        (r'ÐŸÐ¾Ð»Ð½Ð°Ñ Ð¾Ð¿Ñ‚Ð¸Ð¼Ð¸Ð·Ð°Ñ†Ð¸Ñ:', 'Full optimization:'),
        (r'ÐºÐ¾Ð¼Ð±Ð¸Ð½Ð°Ñ†Ð¸Ð¹', 'combinations'),
        (r'Ñ€ÐµÐ¶Ð¸Ð¼:', 'mode:'),
        (r"'ÐÐµÑ‚'", "'None'"),
        
        # Mojibake emoji and symbols
        (r'âœ"', '✓'),
        (r'âœ—', '✗'),
        (r'Â±', '±'),
    ]
    
    for pattern, replacement in mojibake_fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made += 1
    
    # Fix 2: Add duplicate removal to /replay endpoint if missing
    # Look for the replay_indicator function and check if it has dedup
    if 'async def replay_indicator' in content:
        # Find the section between replay_indicator and the next @router
        replay_match = re.search(
            r'(async def replay_indicator.*?df = pd\.read_parquet\(filepath\)\s*\n)(\s*if settings\.start_date:)',
            content, 
            re.DOTALL
        )
        if replay_match:
            # Check if dedup already exists between parquet read and date filter
            section = replay_match.group(0)
            if 'df.index.duplicated' not in section:
                # Add dedup lines
                new_section = replay_match.group(1) + \
                    '\n    # Remove duplicates and sort\n' + \
                    '    df = df[~df.index.duplicated(keep="first")]\n' + \
                    '    df = df.sort_index()\n\n' + \
                    replay_match.group(2)
                content = content.replace(section, new_section)
                changes_made += 1
                print("    Added duplicate removal to /replay endpoint")
    
    if changes_made > 0:
        filepath.write_text(content, encoding='utf-8')
        print(f"[OK] Patched {filepath} ({changes_made} fixes)")
        return True
    else:
        print(f"[SKIP] {filepath} - no changes needed")
        return False


def patch_data_routes():
    """Patch data_routes.py with fixes"""
    filepath = Path("backend/app/api/data_routes.py")
    if not filepath.exists():
        # Try relative path
        filepath = Path("app/api/data_routes.py")
        if not filepath.exists():
            print(f"[SKIP] data_routes.py not found")
            return False
    
    content = filepath.read_text(encoding='utf-8', errors='replace')
    changes_made = 0
    
    # Fix mojibake
    mojibake_fixes = [
        (r'âœ"', '✓'),
        (r'âœ—', '✗'),
    ]
    
    for pattern, replacement in mojibake_fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made += 1
    
    if changes_made > 0:
        filepath.write_text(content, encoding='utf-8')
        print(f"[OK] Patched {filepath} ({changes_made} fixes)")
        return True
    else:
        print(f"[SKIP] {filepath} - no changes needed")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("KOMAS Chat #16: Backend Bug Fixes")
    print("=" * 50)
    
    patches = [
        patch_indicator_routes,
        patch_data_routes,
    ]
    
    results = []
    for patch_fn in patches:
        try:
            result = patch_fn()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] {patch_fn.__name__}: {e}")
            results.append(False)
    
    print("=" * 50)
    print(f"Done: {sum(results)}/{len(results)} patches applied")
