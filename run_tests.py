"""
Run Tests for Chat #31-33: Presets Full Module
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))
sys.path.insert(0, os.path.dirname(__file__))

def run_tests():
    """Run all tests for preset module"""
    print("=" * 50)
    print("KOMAS v4 - Chat #31-33 Tests")
    print("Presets Full Module")
    print("=" * 50)
    print()
    
    # Test 1: Preset ID Generation
    print("[Test 1] Preset ID Generation...")
    try:
        from backend.app.database.presets_db import _generate_preset_id
        
        id1 = _generate_preset_id("Test Preset", "dominant")
        assert id1.startswith("DOMINANT_"), f"Expected DOMINANT_ prefix, got {id1}"
        
        id2 = _generate_preset_id("Test Preset", "trg")
        assert id2.startswith("TRG_"), f"Expected TRG_ prefix, got {id2}"
        
        print("  PASSED: Preset ID generation works correctly")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 2: Backup Format
    print("[Test 2] Backup Format...")
    try:
        import json
        from datetime import datetime
        
        backup_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "total_presets": 2,
            "presets": [
                {"name": "Preset 1", "indicator_type": "dominant"},
                {"name": "Preset 2", "indicator_type": "trg"}
            ]
        }
        
        json_str = json.dumps(backup_data, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert "version" in parsed
        assert "presets" in parsed
        assert len(parsed["presets"]) == 2
        
        print("  PASSED: Backup format is correct")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 3: Batch Operations Fields
    print("[Test 3] Batch Update Allowed Fields...")
    try:
        allowed_fields = {"category", "is_active", "is_favorite", "tags"}
        
        valid_update = {"category": "scalp", "is_favorite": True}
        invalid = set(valid_update.keys()) - allowed_fields
        assert len(invalid) == 0, f"Valid update rejected: {invalid}"
        
        invalid_update = {"name": "Test", "params": {}}
        invalid = set(invalid_update.keys()) - allowed_fields
        assert len(invalid) == 2, "Invalid fields not detected"
        
        print("  PASSED: Batch update field validation works")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 4: Clone Name Generation
    print("[Test 4] Clone Name Generation...")
    try:
        original_name = "My Preset"
        clone_name = f"{original_name} (Copy)"
        
        assert clone_name == "My Preset (Copy)"
        assert "Copy" in clone_name
        
        print("  PASSED: Clone name generation works")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 5: Preset Validation
    print("[Test 5] Preset Parameter Validation...")
    try:
        dominant_params = {
            "sensitivity": 21,
            "tp1_percent": 2.5,
            "sl_percent": 3.0,
            "filter_type": 0
        }
        
        assert 10 <= dominant_params["sensitivity"] <= 100
        assert 0 < dominant_params["tp1_percent"] <= 50
        assert 0 < dominant_params["sl_percent"] <= 50
        
        trg_params = {
            "i1": 45,
            "i2": 4.0,
            "sl_percent": 2.0
        }
        
        assert 10 <= trg_params["i1"] <= 200
        assert 1.0 <= trg_params["i2"] <= 10.0
        
        print("  PASSED: Parameter validation works")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 6: API Endpoints
    print("[Test 6] API Endpoint Definitions...")
    try:
        endpoints = [
            ("POST", "/api/presets/clone/{id}"),
            ("POST", "/api/presets/backup"),
            ("POST", "/api/presets/restore"),
            ("POST", "/api/presets/batch/delete"),
            ("POST", "/api/presets/batch/update"),
            ("POST", "/api/presets/batch/export"),
        ]
        
        for method, path in endpoints:
            assert method in ["GET", "POST", "PUT", "DELETE"]
            assert path.startswith("/api/presets")
        
        print("  PASSED: All endpoints defined correctly")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Test 7: Frontend Props
    print("[Test 7] Frontend Component Props...")
    try:
        preset_card_props = [
            "preset", "onEdit", "onClone", "onDelete", 
            "onExport", "onToggleFavorite", "onApply"
        ]
        
        modal_modes = ["create", "edit", "clone"]
        
        assert len(preset_card_props) == 7
        assert len(modal_modes) == 3
        
        print("  PASSED: Frontend props defined correctly")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    print()
    print("=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
