"""
Fix imports in signal_score.py
Replaces absolute import with try/except relative import
"""
import os
import sys

def fix_signal_score():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    signal_score_path = os.path.join(script_dir, 'backend', 'app', 'services', 'signal_score.py')
    
    if not os.path.exists(signal_score_path):
        print(f"ERROR: signal_score.py not found at {signal_score_path}")
        return False
    
    print(f"Reading {signal_score_path}...")
    
    with open(signal_score_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'try:\n    from .multi_tf_loader import' in content:
        print("Already fixed!")
        return True
    
    old_import = """from app.services.multi_tf_loader import (
    MultiTFLoader,
    TrendDetectionMethod,
    DEFAULT_TF_WEIGHTS,
)"""
    
    new_import = """# Import MultiTFLoader with fallback for different contexts
try:
    from .multi_tf_loader import (
        MultiTFLoader,
        TrendDetectionMethod,
        DEFAULT_TF_WEIGHTS,
    )
except ImportError:
    from multi_tf_loader import (
        MultiTFLoader,
        TrendDetectionMethod,
        DEFAULT_TF_WEIGHTS,
    )"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        with open(signal_score_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("SUCCESS: Fixed signal_score.py imports!")
        return True
    else:
        print("WARNING: Expected import pattern not found")
        if 'from app.services.multi_tf_loader' in content:
            content = content.replace('from app.services.multi_tf_loader', 'from multi_tf_loader')
            with open(signal_score_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Applied fallback fix")
            return True
        return False

if __name__ == '__main__':
    success = fix_signal_score()
    sys.exit(0 if success else 1)
