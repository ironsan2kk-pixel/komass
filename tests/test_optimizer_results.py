"""
KOMAS Trading Server - Optimization Results Tests
==================================================
Unit tests for optimization results persistence and aggregation.

Tests:
- OptimizationResultsManager CRUD operations
- Result aggregation by preset
- Result aggregation by pair
- Export functions (CSV/JSON)
- Grade calculation

Chat #47: Preset Optimizer Results
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path


# ============================================================================
# GRADE CALCULATION TESTS
# ============================================================================

class TestGradeCalculation:
    """Tests for grade calculation from score"""
    
    def test_grade_A(self):
        """Score >= 85 should be grade A"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(100) == 'A'
        assert calculate_grade(90) == 'A'
        assert calculate_grade(85) == 'A'
    
    def test_grade_B(self):
        """Score 70-84 should be grade B"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(84) == 'B'
        assert calculate_grade(75) == 'B'
        assert calculate_grade(70) == 'B'
    
    def test_grade_C(self):
        """Score 55-69 should be grade C"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(69) == 'C'
        assert calculate_grade(60) == 'C'
        assert calculate_grade(55) == 'C'
    
    def test_grade_D(self):
        """Score 40-54 should be grade D"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(54) == 'D'
        assert calculate_grade(45) == 'D'
        assert calculate_grade(40) == 'D'
    
    def test_grade_F(self):
        """Score < 40 should be grade F"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(39) == 'F'
        assert calculate_grade(20) == 'F'
        assert calculate_grade(0) == 'F'
    
    def test_grade_edge_cases(self):
        """Edge cases for grade calculation"""
        from app.db.optimizer_db import calculate_grade
        assert calculate_grade(84.9) == 'B'
        assert calculate_grade(85.0) == 'A'
        assert calculate_grade(-10) == 'F'


# ============================================================================
# GRADE COLOR TESTS
# ============================================================================

class TestGradeColor:
    """Tests for grade color mapping"""
    
    def test_grade_colors(self):
        """Test color mapping for each grade (returns Tailwind classes)"""
        from app.db.optimizer_db import get_grade_color
        assert get_grade_color('A') == 'text-green-400'
        assert get_grade_color('B') == 'text-blue-400'
        assert get_grade_color('C') == 'text-yellow-400'
        assert get_grade_color('D') == 'text-orange-400'
        assert get_grade_color('F') == 'text-red-400'
    
    def test_unknown_grade(self):
        """Unknown grade should return gray"""
        from app.db.optimizer_db import get_grade_color
        assert get_grade_color('X') == 'text-gray-400'
        assert get_grade_color('') == 'text-gray-400'


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestOptimizationDataclasses:
    """Tests for optimization dataclasses"""
    
    def test_run_summary_creation(self):
        """Test creating OptimizationRunSummary"""
        from app.db.optimizer_db import OptimizationRunSummary
        
        summary = OptimizationRunSummary(
            run_id="test_001",
            name="Test Run",
            mode="smart",
            status="completed",
            timeframe="1h",
            preset_count=10,
            pair_count=5,
            total_combinations=50,
            duration_seconds=30.5,
            best_preset_name="T_60_40",
            best_overall_score=85.0,
            best_avg_pnl=35.5,
            created_at="2025-12-28T12:00:00",
            completed_at="2025-12-28T12:00:30"
        )
        
        assert summary.run_id == "test_001"
        assert summary.mode == "smart"
        assert summary.best_overall_score == 85.0
    
    def test_run_detail_creation(self):
        """Test creating OptimizationRunDetail"""
        from app.db.optimizer_db import OptimizationRunDetail
        
        detail = OptimizationRunDetail(
            run_id="test_001",
            name="Test Run",
            mode="smart",
            status="completed",
            timeframe="1h",
            start_date="2025-01-01",
            end_date="2025-12-01",
            original_preset_count=10,
            original_pair_count=5,
            effective_preset_count=8,
            effective_pair_count=5,
            preset_ids=["T_60_40", "M_45_30"],
            pairs=["BTCUSDT", "ETHUSDT"],
            total_combinations=10,
            completed_combinations=10,
            num_workers=4,
            started_at="2025-12-28T12:00:00",
            completed_at="2025-12-28T12:00:30",
            duration_seconds=30.5,
            best_preset_id="T_60_40",
            best_preset_name="Trend Medium",
            best_overall_score=85.0,
            best_avg_pnl=35.5,
            top_10_presets=[{"id": "T_60_40", "score": 85.0}],
            preset_scores=[{"preset_id": "T_60_40", "score": 85.0}],
            result_matrix={"T_60_40": {"BTCUSDT": {"pnl": 40.0}}},
            errors=[],
            created_at="2025-12-28T12:00:00"
        )
        
        assert detail.run_id == "test_001"
        assert len(detail.preset_ids) == 2
        assert len(detail.pairs) == 2


# ============================================================================
# RESULTS MANAGER TESTS
# ============================================================================

class TestOptimizationResultsManager:
    """Tests for OptimizationResultsManager"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path, monkeypatch):
        """Setup test database path before each test"""
        # Monkey-patch the DB path to use temp directory
        test_db_path = tmp_path / "test_optimizer.db"
        
        from app.db import optimizer_db
        monkeypatch.setattr(optimizer_db, 'DB_PATH', test_db_path)
        monkeypatch.setattr(optimizer_db, 'SQLITE_URL', f"sqlite:///{test_db_path}")
        
        # Reset singleton
        optimizer_db.OptimizationResultsManager._engine = None
        optimizer_db.OptimizationResultsManager._session_factory = None
        
        # Initialize DB
        optimizer_db.init_optimizer_db()
    
    @pytest.fixture
    def sample_result(self):
        """Create sample optimization result data"""
        return {
            "run_id": "test_run_001",
            "mode": "smart",
            "timeframe": "1h",
            "preset_ids": ["T_60_40", "M_45_30"],
            "pairs": ["BTCUSDT", "ETHUSDT"],
            "status": "completed",
            "total_combinations": 4,
            "completed_combinations": 4,
            "num_workers": 4,
            "duration_seconds": 45.5,
            "original_preset_count": 2,
            "original_pair_count": 2,
            "effective_preset_count": 2,
            "effective_pair_count": 2,
            "best_preset_id": "T_60_40",
            "best_preset_name": "Trend Medium",
            "best_overall_score": 85.0,
            "best_avg_pnl": 35.5,
            "preset_scores": [
                {
                    "preset_id": "T_60_40",
                    "preset_name": "Trend Medium",
                    "indicator_type": "trg",
                    "rank": 1,
                    "overall_score": 85.0,
                    "grade": "A",
                    "avg_pnl": 35.5,
                    "avg_win_rate": 65.0,
                    "avg_max_dd": 15.0
                },
                {
                    "preset_id": "M_45_30",
                    "preset_name": "Momentum Fast",
                    "indicator_type": "trg",
                    "rank": 2,
                    "overall_score": 72.0,
                    "grade": "B",
                    "avg_pnl": 28.0,
                    "avg_win_rate": 60.0,
                    "avg_max_dd": 18.0
                }
            ],
            "top_10_presets": [
                {"preset_id": "T_60_40", "score": 85.0}
            ],
            "result_matrix": {
                "T_60_40": {
                    "BTCUSDT": {"pnl_percent": 40.0, "win_rate": 70.0},
                    "ETHUSDT": {"pnl_percent": 31.0, "win_rate": 60.0}
                },
                "M_45_30": {
                    "BTCUSDT": {"pnl_percent": 32.0, "win_rate": 62.0},
                    "ETHUSDT": {"pnl_percent": 24.0, "win_rate": 58.0}
                }
            },
            "errors": []
        }
    
    def test_save_run(self, sample_result):
        """Test saving optimization result"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        run_id = OptimizationResultsManager.save_run(sample_result)
        assert run_id == "test_run_001"
    
    def test_get_run(self, sample_result):
        """Test retrieving optimization result"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        OptimizationResultsManager.save_run(sample_result)
        result = OptimizationResultsManager.get_run("test_run_001")
        
        assert result is not None
        assert result.run_id == "test_run_001"
        assert result.mode == "smart"
        assert result.status == "completed"
    
    def test_get_nonexistent_run(self):
        """Test getting result that doesn't exist"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        result = OptimizationResultsManager.get_run("nonexistent")
        assert result is None
    
    def test_list_runs(self, sample_result):
        """Test getting optimization history"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        # Save multiple results
        OptimizationResultsManager.save_run(sample_result)
        
        sample_result["run_id"] = "test_run_002"
        sample_result["mode"] = "full"
        OptimizationResultsManager.save_run(sample_result)
        
        # List runs
        runs = OptimizationResultsManager.list_runs(limit=10)
        assert len(runs) == 2
    
    def test_list_runs_with_filter(self, sample_result):
        """Test filtering history by mode"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        OptimizationResultsManager.save_run(sample_result)
        
        sample_result["run_id"] = "test_run_002"
        sample_result["mode"] = "full"
        OptimizationResultsManager.save_run(sample_result)
        
        # Filter by mode
        runs = OptimizationResultsManager.list_runs(mode="smart")
        assert len(runs) == 1
        assert runs[0].mode == "smart"
    
    def test_delete_run(self, sample_result):
        """Test deleting optimization result"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        OptimizationResultsManager.save_run(sample_result)
        
        success = OptimizationResultsManager.delete_run("test_run_001")
        assert success is True
        
        result = OptimizationResultsManager.get_run("test_run_001")
        assert result is None
    
    def test_delete_nonexistent(self):
        """Test deleting result that doesn't exist"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        success = OptimizationResultsManager.delete_run("nonexistent")
        assert success is False
    
    def test_clear_all(self, sample_result):
        """Test clearing all history"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        for i in range(5):
            sample_result["run_id"] = f"test_run_{i:03d}"
            OptimizationResultsManager.save_run(sample_result)
        
        deleted = OptimizationResultsManager.clear_all()
        assert deleted == 5
        
        runs = OptimizationResultsManager.list_runs()
        assert len(runs) == 0
    
    def test_count_runs(self, sample_result):
        """Test counting runs"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        for i in range(3):
            sample_result["run_id"] = f"test_run_{i:03d}"
            OptimizationResultsManager.save_run(sample_result)
        
        count = OptimizationResultsManager.count_runs()
        assert count == 3
    
    def test_count_runs_with_filter(self, sample_result):
        """Test counting runs with mode filter"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        OptimizationResultsManager.save_run(sample_result)
        
        sample_result["run_id"] = "test_run_002"
        sample_result["mode"] = "full"
        OptimizationResultsManager.save_run(sample_result)
        
        count = OptimizationResultsManager.count_runs(mode="smart")
        assert count == 1


# ============================================================================
# EXPORT TESTS
# ============================================================================

class TestExportFunctions:
    """Tests for CSV/JSON export functions"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path, monkeypatch):
        """Setup test database path before each test"""
        test_db_path = tmp_path / "test_optimizer.db"
        
        from app.db import optimizer_db
        monkeypatch.setattr(optimizer_db, 'DB_PATH', test_db_path)
        monkeypatch.setattr(optimizer_db, 'SQLITE_URL', f"sqlite:///{test_db_path}")
        
        optimizer_db.OptimizationResultsManager._engine = None
        optimizer_db.OptimizationResultsManager._session_factory = None
        optimizer_db.init_optimizer_db()
    
    @pytest.fixture
    def manager_with_result(self):
        """Create manager and add sample result"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        result = {
            "run_id": "export_test",
            "mode": "smart",
            "timeframe": "1h",
            "status": "completed",
            "preset_ids": ["T_60_40", "M_45_30"],
            "pairs": ["BTCUSDT", "ETHUSDT"],
            "total_combinations": 4,
            "completed_combinations": 4,
            "num_workers": 4,
            "duration_seconds": 45.5,
            "original_preset_count": 2,
            "original_pair_count": 2,
            "effective_preset_count": 2,
            "effective_pair_count": 2,
            "preset_scores": [
                {
                    "preset_id": "T_60_40",
                    "preset_name": "Trend Medium",
                    "indicator_type": "trg",
                    "rank": 1,
                    "overall_score": 85.0,
                    "grade": "A",
                    "avg_pnl": 35.5,
                    "avg_win_rate": 65.0,
                    "avg_max_dd": 15.0,
                    "avg_sharpe": 2.1,
                    "avg_profit_factor": 2.5,
                    "consistency": 0.85,
                    "best_pair": "BTCUSDT",
                    "worst_pair": "ETHUSDT"
                }
            ],
            "result_matrix": {},
            "errors": []
        }
        OptimizationResultsManager.save_run(result)
        return OptimizationResultsManager
    
    def test_export_csv(self, manager_with_result):
        """Test exporting to CSV"""
        csv_data = manager_with_result.export_to_csv("export_test")
        
        assert csv_data is not None
        assert "Preset ID" in csv_data
        assert "T_60_40" in csv_data
        assert "Trend Medium" in csv_data
    
    def test_export_csv_columns(self, manager_with_result):
        """Test CSV has all required columns"""
        csv_data = manager_with_result.export_to_csv("export_test")
        lines = csv_data.strip().split('\n')
        headers = lines[0].split(',')
        
        # Headers use Title Case
        required_columns = ['Rank', 'Preset ID', 'Preset Name', 'Indicator', 
                          'Overall Score', 'Avg PnL %']
        for col in required_columns:
            assert col in headers, f"Missing column: {col}"
    
    def test_export_csv_not_found(self, manager_with_result):
        """Test exporting nonexistent run"""
        csv_data = manager_with_result.export_to_csv("nonexistent")
        assert csv_data is None
    
    def test_export_json(self, manager_with_result):
        """Test exporting to JSON"""
        json_data = manager_with_result.export_to_json("export_test")
        
        assert json_data is not None
        assert json_data["run_id"] == "export_test"
        assert "preset_scores" in json_data
    
    def test_export_json_structure(self, manager_with_result):
        """Test JSON export structure"""
        json_data = manager_with_result.export_to_json("export_test")
        
        # JSON has data directly at root level
        assert "run_id" in json_data
        assert "preset_scores" in json_data
        assert json_data["mode"] == "smart"
        assert json_data["timeframe"] == "1h"


# ============================================================================
# PAGINATION TESTS
# ============================================================================

class TestPagination:
    """Tests for pagination functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path, monkeypatch):
        """Setup test database with many results"""
        test_db_path = tmp_path / "test_optimizer.db"
        
        from app.db import optimizer_db
        monkeypatch.setattr(optimizer_db, 'DB_PATH', test_db_path)
        monkeypatch.setattr(optimizer_db, 'SQLITE_URL', f"sqlite:///{test_db_path}")
        
        optimizer_db.OptimizationResultsManager._engine = None
        optimizer_db.OptimizationResultsManager._session_factory = None
        optimizer_db.init_optimizer_db()
        
        # Create 25 runs
        for i in range(25):
            result = {
                "run_id": f"run_{i:03d}",
                "mode": ["quick", "standard", "smart", "full"][i % 4],
                "timeframe": "1h",
                "status": "completed",
                "total_combinations": 100,
                "completed_combinations": 100,
                "duration_seconds": 30.0,
                "preset_ids": [],
                "pairs": [],
                "preset_scores": [],
                "result_matrix": {},
                "errors": []
            }
            optimizer_db.OptimizationResultsManager.save_run(result)
    
    def test_pagination_first_page(self):
        """Test getting first page"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        runs = OptimizationResultsManager.list_runs(limit=10, offset=0)
        total = OptimizationResultsManager.count_runs()
        
        assert total == 25
        assert len(runs) == 10
    
    def test_pagination_second_page(self):
        """Test getting second page"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        runs = OptimizationResultsManager.list_runs(limit=10, offset=10)
        
        assert len(runs) == 10
    
    def test_pagination_last_page(self):
        """Test getting last page"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        runs = OptimizationResultsManager.list_runs(limit=10, offset=20)
        
        assert len(runs) == 5
    
    def test_pagination_with_filter(self):
        """Test pagination with mode filter"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        runs = OptimizationResultsManager.list_runs(mode="smart", limit=10)
        total = OptimizationResultsManager.count_runs(mode="smart")
        
        # 25 total, every 4th is "smart" starting at index 2
        # So indices 2, 6, 10, 14, 18, 22 = 6 smart runs
        assert total == 6
        for run in runs:
            assert run.mode == "smart"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for full optimization result flow"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path, monkeypatch):
        """Setup test database"""
        test_db_path = tmp_path / "test_optimizer.db"
        
        from app.db import optimizer_db
        monkeypatch.setattr(optimizer_db, 'DB_PATH', test_db_path)
        monkeypatch.setattr(optimizer_db, 'SQLITE_URL', f"sqlite:///{test_db_path}")
        
        optimizer_db.OptimizationResultsManager._engine = None
        optimizer_db.OptimizationResultsManager._session_factory = None
        optimizer_db.init_optimizer_db()
    
    def test_full_workflow(self):
        """Test complete workflow: save -> query -> export -> delete"""
        from app.db.optimizer_db import OptimizationResultsManager
        
        # 1. Save result
        result = {
            "run_id": "workflow_test",
            "mode": "smart",
            "timeframe": "4h",
            "status": "completed",
            "preset_ids": ["T_60_40"],
            "pairs": ["BTCUSDT"],
            "total_combinations": 1,
            "completed_combinations": 1,
            "num_workers": 1,
            "duration_seconds": 10.0,
            "original_preset_count": 1,
            "original_pair_count": 1,
            "effective_preset_count": 1,
            "effective_pair_count": 1,
            "preset_scores": [{
                "preset_id": "T_60_40",
                "preset_name": "Trend",
                "indicator_type": "trg",
                "rank": 1,
                "overall_score": 80.0,
                "grade": "B",
                "avg_pnl": 30.0,
                "avg_win_rate": 60.0,
                "avg_max_dd": 12.0
            }],
            "result_matrix": {},
            "errors": []
        }
        
        run_id = OptimizationResultsManager.save_run(result)
        assert run_id == "workflow_test"
        
        # 2. Query result
        saved = OptimizationResultsManager.get_run(run_id)
        assert saved is not None
        assert saved.status == "completed"
        
        # 3. Get in list
        runs = OptimizationResultsManager.list_runs()
        assert len(runs) == 1
        
        # 4. Export CSV
        csv = OptimizationResultsManager.export_to_csv(run_id)
        assert csv is not None
        assert "T_60_40" in csv
        
        # 5. Export JSON
        json_data = OptimizationResultsManager.export_to_json(run_id)
        assert json_data is not None
        assert json_data["run_id"] == run_id
        
        # 6. Delete
        deleted = OptimizationResultsManager.delete_run(run_id)
        assert deleted is True
        
        # 7. Verify deleted
        runs = OptimizationResultsManager.list_runs()
        assert len(runs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
