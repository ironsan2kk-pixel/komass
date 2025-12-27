"""
Test Signal Score UI Integration
================================

Tests for Signal Score UI components and backend integration.

Chat #36: Score UI

Run with:
    cd backend
    python -m pytest tests/test_score_ui.py -v
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGradeCalculation:
    """Test grade calculation from scores"""
    
    def test_grade_a(self):
        """Scores 85-100 should be grade A"""
        from app.services.signal_score import get_grade_from_score
        
        assert get_grade_from_score(100) == 'A'
        assert get_grade_from_score(95) == 'A'
        assert get_grade_from_score(90) == 'A'
        assert get_grade_from_score(85) == 'A'
    
    def test_grade_b(self):
        """Scores 70-84 should be grade B"""
        from app.services.signal_score import get_grade_from_score
        
        assert get_grade_from_score(84) == 'B'
        assert get_grade_from_score(77) == 'B'
        assert get_grade_from_score(70) == 'B'
    
    def test_grade_c(self):
        """Scores 55-69 should be grade C"""
        from app.services.signal_score import get_grade_from_score
        
        assert get_grade_from_score(69) == 'C'
        assert get_grade_from_score(60) == 'C'
        assert get_grade_from_score(55) == 'C'
    
    def test_grade_d(self):
        """Scores 40-54 should be grade D"""
        from app.services.signal_score import get_grade_from_score
        
        assert get_grade_from_score(54) == 'D'
        assert get_grade_from_score(47) == 'D'
        assert get_grade_from_score(40) == 'D'
    
    def test_grade_f(self):
        """Scores 0-39 should be grade F"""
        from app.services.signal_score import get_grade_from_score
        
        assert get_grade_from_score(39) == 'F'
        assert get_grade_from_score(20) == 'F'
        assert get_grade_from_score(0) == 'F'


class TestGradeColors:
    """Test grade color mapping"""
    
    def test_grade_colors_exist(self):
        """All grades should have colors"""
        from app.services.signal_score import get_grade_color
        
        grades = ['A', 'B', 'C', 'D', 'F']
        for grade in grades:
            color = get_grade_color(grade)
            assert color is not None
            assert color.startswith('#')
    
    def test_grade_a_is_green(self):
        """Grade A should be green"""
        from app.services.signal_score import get_grade_color
        
        assert get_grade_color('A') == '#22c55e'
    
    def test_grade_f_is_red(self):
        """Grade F should be red"""
        from app.services.signal_score import get_grade_color
        
        assert get_grade_color('F') == '#ef4444'


class TestScoreIntegration:
    """Test score integration utilities"""
    
    def test_import_integration_module(self):
        """Should be able to import score integration module"""
        from app.utils.score_integration import (
            add_signal_scores_to_trades,
            get_grade_statistics,
        )
        
        assert callable(add_signal_scores_to_trades)
        assert callable(get_grade_statistics)
    
    def test_empty_trades(self):
        """Empty trades should return empty"""
        from app.utils.score_integration import add_signal_scores_to_trades
        import pandas as pd
        
        result = add_signal_scores_to_trades([], pd.DataFrame())
        assert result == []
    
    def test_get_grade_statistics_empty(self):
        """Empty trades should return empty stats"""
        from app.utils.score_integration import get_grade_statistics
        
        result = get_grade_statistics([])
        assert result == {}
    
    def test_get_grade_statistics_with_scores(self):
        """Should calculate statistics from scored trades"""
        from app.utils.score_integration import get_grade_statistics
        
        trades = [
            {'signal_grade': 'A', 'pnl': 5.0},
            {'signal_grade': 'A', 'pnl': 3.0},
            {'signal_grade': 'B', 'pnl': 2.0},
            {'signal_grade': 'B', 'pnl': -1.0},
            {'signal_grade': 'C', 'pnl': -2.0},
            {'signal_score': 35, 'pnl': -3.0},  # Should be grade F
        ]
        
        stats = get_grade_statistics(trades)
        
        assert stats['A']['count'] == 2
        assert stats['A']['win_rate'] == 100.0
        assert stats['B']['count'] == 2
        assert stats['B']['win_rate'] == 50.0
        assert stats['C']['count'] == 1
        assert stats['F']['count'] == 1


class TestSignalScorer:
    """Test SignalScorer class"""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame"""
        import pandas as pd
        import numpy as np
        
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        close = 45000 + np.cumsum(np.random.randn(100) * 100)
        high = close + np.abs(np.random.randn(100) * 50)
        low = close - np.abs(np.random.randn(100) * 50)
        open_ = close + np.random.randn(100) * 20
        volume = np.abs(np.random.randn(100) * 500000) + 100000
        
        return pd.DataFrame({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        }, index=dates)
    
    def test_scorer_initialization(self):
        """SignalScorer should initialize correctly"""
        from app.services.signal_score import SignalScorer
        
        scorer = SignalScorer()
        assert scorer is not None
        assert hasattr(scorer, 'calculate_score')
    
    def test_scorer_with_custom_params(self):
        """SignalScorer should accept custom parameters"""
        from app.services.signal_score import SignalScorer
        
        params = {
            'atr_period': 20,
            'rsi_period': 21,
            'adx_threshold': 30,
        }
        
        scorer = SignalScorer(params=params)
        assert scorer.params['atr_period'] == 20
        assert scorer.params['rsi_period'] == 21
        assert scorer.params['adx_threshold'] == 30
    
    def test_calculate_score_long(self, sample_df):
        """Should calculate score for long signal"""
        from app.services.signal_score import SignalScorer
        
        scorer = SignalScorer()
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=sample_df['close'].iloc[-1],
        )
        
        assert result is not None
        assert 0 <= result.total_score <= 100
        assert result.grade in ['A', 'B', 'C', 'D', 'F']
        assert 'confluence' in result.components
        assert 'multi_tf' in result.components
        assert 'market_context' in result.components
        assert 'technical_levels' in result.components
    
    def test_calculate_score_short(self, sample_df):
        """Should calculate score for short signal"""
        from app.services.signal_score import SignalScorer
        
        scorer = SignalScorer()
        result = scorer.calculate_score(
            df=sample_df,
            direction='short',
            entry_price=sample_df['close'].iloc[-1],
        )
        
        assert result is not None
        assert 0 <= result.total_score <= 100
        assert result.grade in ['A', 'B', 'C', 'D', 'F']
    
    def test_score_with_insufficient_data(self):
        """Should handle insufficient data gracefully"""
        from app.services.signal_score import SignalScorer
        import pandas as pd
        
        # Create tiny DataFrame
        df = pd.DataFrame({
            'open': [100],
            'high': [101],
            'low': [99],
            'close': [100],
            'volume': [1000],
        })
        
        scorer = SignalScorer()
        result = scorer.calculate_score(
            df=df,
            direction='long',
            entry_price=100,
        )
        
        assert result.total_score == 0
        assert result.grade == 'F'
        assert 'Insufficient data' in result.details.get('error', '')


class TestBatchScoring:
    """Test batch trade scoring"""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame"""
        import pandas as pd
        import numpy as np
        
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
        
        close = 45000 + np.cumsum(np.random.randn(200) * 100)
        high = close + np.abs(np.random.randn(200) * 50)
        low = close - np.abs(np.random.randn(200) * 50)
        open_ = close + np.random.randn(200) * 20
        volume = np.abs(np.random.randn(200) * 500000) + 100000
        
        return pd.DataFrame({
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
        }, index=dates)
    
    def test_score_trades_batch(self, sample_df):
        """Should score multiple trades"""
        from app.services.signal_score import score_trades
        
        trades = [
            {'direction': 'long', 'entry_price': 45100, 'entry_idx': 50},
            {'direction': 'short', 'entry_price': 45200, 'entry_idx': 100},
            {'direction': 'long', 'entry_price': 45050, 'entry_idx': 150},
        ]
        
        scored = score_trades(trades, sample_df)
        
        assert len(scored) == 3
        for trade in scored:
            assert 'signal_score' in trade
            assert 'signal_grade' in trade
            assert 'score_components' in trade
    
    def test_score_trades_preserves_original_data(self, sample_df):
        """Should preserve original trade data"""
        from app.services.signal_score import score_trades
        
        trades = [
            {
                'direction': 'long',
                'entry_price': 45100,
                'entry_idx': 50,
                'pnl': 2.5,
                'custom_field': 'test',
            },
        ]
        
        scored = score_trades(trades, sample_df)
        
        assert scored[0]['pnl'] == 2.5
        assert scored[0]['custom_field'] == 'test'
        assert scored[0]['entry_price'] == 45100


class TestAPIEndpoints:
    """Test Signal Score API endpoints"""
    
    def test_grades_endpoint(self):
        """Test /api/signal-score/grades endpoint structure"""
        # This would be an integration test with FastAPI TestClient
        # For now, just test the expected structure
        expected_grades = ['A', 'B', 'C', 'D', 'F']
        expected_components = ['confluence', 'multi_tf', 'market_context', 'technical_levels']
        
        from app.services.signal_score import (
            GRADE_THRESHOLDS,
            MAX_CONFLUENCE,
            MAX_MULTI_TF,
            MAX_MARKET_CONTEXT,
            MAX_TECHNICAL_LEVELS,
        )
        
        # Verify grade thresholds exist
        for grade_str in expected_grades:
            from app.services.signal_score import Grade
            grade = Grade(grade_str)
            assert grade in GRADE_THRESHOLDS
        
        # Verify component max values
        assert MAX_CONFLUENCE == 25
        assert MAX_MULTI_TF == 25
        assert MAX_MARKET_CONTEXT == 25
        assert MAX_TECHNICAL_LEVELS == 25


class TestFrontendIntegration:
    """Test expected data format for frontend"""
    
    def test_score_result_format(self):
        """Score result should match frontend expectations"""
        from app.services.signal_score import SignalScorer
        import pandas as pd
        import numpy as np
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        df = pd.DataFrame({
            'open': 45000 + np.cumsum(np.random.randn(100) * 100),
            'high': 45100 + np.random.rand(100) * 100,
            'low': 44900 - np.random.rand(100) * 100,
            'close': 45000 + np.cumsum(np.random.randn(100) * 100),
            'volume': np.random.rand(100) * 1000000,
        }, index=dates)
        
        scorer = SignalScorer()
        result = scorer.calculate_score(
            df=df,
            direction='long',
            entry_price=df['close'].iloc[-1],
        )
        
        # Verify structure matches frontend expectations
        result_dict = result.to_dict()
        
        assert 'total_score' in result_dict
        assert isinstance(result_dict['total_score'], int)
        
        assert 'grade' in result_dict
        assert result_dict['grade'] in ['A', 'B', 'C', 'D', 'F']
        
        assert 'components' in result_dict
        components = result_dict['components']
        assert 'confluence' in components
        assert 'multi_tf' in components
        assert 'market_context' in components
        assert 'technical_levels' in components
        
        # All component values should be integers 0-25
        for comp, value in components.items():
            assert 0 <= value <= 25, f"{comp} value {value} out of range"
        
        assert 'details' in result_dict
        assert 'recommendations' in result_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
