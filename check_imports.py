#!/usr/bin/env python3
"""
Check all React component imports for issues
"""
import os
import re
from pathlib import Path
from collections import defaultdict

frontend_src = Path("/home/user/komass/frontend/src")

print("=" * 70)
print("FRONTEND IMPORT ANALYSIS")
print("=" * 70)
print()

# Track all imports
all_imports = defaultdict(list)
component_files = []

# Find all JSX files
for jsx_file in frontend_src.rglob("*.jsx"):
    if "node_modules" in str(jsx_file):
        continue
    component_files.append(jsx_file)

    with open(jsx_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all imports
    import_pattern = r"^import\s+.*?\s+from\s+['\"](.+?)['\"]"
    for match in re.finditer(import_pattern, content, re.MULTILINE):
        import_path = match.group(1)
        all_imports[import_path].append(str(jsx_file.relative_to(frontend_src)))

print(f"Total JSX files found: {len(component_files)}")
print(f"Total unique imports: {len(all_imports)}")
print()

# Categorize imports
internal_imports = {}
external_imports = {}
relative_imports = {}

for imp, files in all_imports.items():
    if imp.startswith('.'):
        relative_imports[imp] = files
    elif imp.startswith('@') or '/' in imp:
        external_imports[imp] = files
    else:
        external_imports[imp] = files

print("IMPORT CATEGORIES:")
print("-" * 70)
print(f"  External packages: {len(external_imports)}")
print(f"  Relative imports:  {len(relative_imports)}")
print()

# Check for potentially broken relative imports
print("RELATIVE IMPORTS ANALYSIS:")
print("-" * 70)

broken_imports = []
for imp_path, source_files in relative_imports.items():
    for source_file in source_files:
        source_path = frontend_src / source_file
        source_dir = source_path.parent

        # Resolve the import path
        if imp_path.startswith('./'):
            target = source_dir / imp_path[2:]
        elif imp_path.startswith('../'):
            parts = imp_path.split('/')
            target = source_dir
            for part in parts:
                if part == '..':
                    target = target.parent
                elif part and part != '.':
                    target = target / part
        else:
            continue

        # Check if file exists (try .jsx, .js, /index.jsx)
        found = False
        for ext in ['', '.jsx', '.js', '/index.jsx', '/index.js']:
            check_path = Path(str(target) + ext)
            if check_path.exists():
                found = True
                break

        if not found:
            broken_imports.append({
                'source': source_file,
                'import': imp_path,
                'expected': str(target)
            })

if broken_imports:
    print(f"⚠️  Found {len(broken_imports)} potentially broken imports:")
    print()
    for bi in broken_imports[:20]:  # Show first 20
        print(f"  ❌ {bi['source']}")
        print(f"     imports: {bi['import']}")
        print(f"     expected: {bi['expected']}")
        print()
else:
    print("✅ All relative imports appear to be valid")
    print()

# Most common external packages
print("TOP EXTERNAL DEPENDENCIES:")
print("-" * 70)
ext_counts = {k: len(v) for k, v in external_imports.items()}
for pkg, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {count:3d}x  {pkg}")

print()
print("=" * 70)
