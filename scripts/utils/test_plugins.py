"""
Komas Plugins Module - Test Script
"""
import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

def test_registry():
    print('=' * 50)
    print('TEST 1: Registry')
    print('=' * 50)
    
    from app.indicators.registry import (
        PluginRegistry, 
        registry, 
        PluginType,
        register_indicator
    )
    
    # Test singleton
    r1 = PluginRegistry()
    r2 = PluginRegistry()
    assert r1 is r2, 'Singleton failed'
    print('✓ Singleton pattern works')
    
    # Test registration
    class DummyIndicator:
        pass
    
    info = registry.indicators.register(
        plugin_id='test_indicator',
        cls=DummyIndicator,
        name='Test Indicator',
        version='1.0.0'
    )
    print(f'✓ Registered: {info.id}')
    
    # Test get
    cls = registry.indicators.get('test_indicator')
    assert cls is DummyIndicator, 'Get failed'
    print('✓ Get works')
    
    # Test stats
    stats = registry.get_stats()
    print(f'✓ Stats: {stats}')
    
    # Cleanup
    registry.indicators.unregister('test_indicator')
    print('✓ Unregister works')


def test_loader():
    print()
    print('=' * 50)
    print('TEST 2: Loader')
    print('=' * 50)
    
    from app.indicators.loader import (
        PluginLoader,
        PluginManifest,
        ManifestEntryPoint
    )
    
    # Test entry point parsing
    ep = ManifestEntryPoint.from_string('indicator.core:TRGIndicator')
    assert ep.module_path == 'indicator.core', 'Module path failed'
    assert ep.class_name == 'TRGIndicator', 'Class name failed'
    print('✓ Entry point parsing works')
    
    # Test manifest parsing
    manifest_dict = {
        'id': 'test',
        'name': 'Test Plugin',
        'version': '1.0.0',
        'description': 'Test',
        'author': 'Test',
        'entry_points': {
            'indicator': 'indicator:TestIndicator'
        }
    }
    
    manifest = PluginManifest.from_dict(manifest_dict)
    assert manifest.id == 'test', 'Manifest ID failed'
    assert manifest.indicator is not None, 'Manifest indicator failed'
    print('✓ Manifest parsing works')
    
    # Test validation
    is_valid, errors = manifest.validate()
    assert is_valid, f'Validation failed: {errors}'
    print('✓ Manifest validation works')
    
    # Test loader init
    loader = PluginLoader()
    print(f'✓ Loader initialized, plugins_dir: {loader._plugins_dir}')


def test_api():
    print()
    print('=' * 50)
    print('TEST 3: API')
    print('=' * 50)
    
    try:
        from app.api.plugins import router
        print(f'✓ API router loaded, prefix: {router.prefix}')
        print(f'✓ Routes: {len(router.routes)} endpoints')
    except ImportError as e:
        print(f'⚠ API test skipped (missing dependency: {e})')
        print('  Run: pip install fastapi pydantic')


if __name__ == '__main__':
    try:
        test_registry()
        test_loader()
        test_api()
        
        print()
        print('=' * 50)
        print('ALL TESTS PASSED!')
        print('=' * 50)
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
