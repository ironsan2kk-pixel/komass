"""
KOMAS Trading Server - Optimizer Heatmap Tests
===============================================
Unit tests for heatmap visualization endpoints.

Chat #48: Preset Optimizer Heatmap
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import functions to test
import sys
sys.path.insert(0, 'backend/app')


class TestHeatmapColorGeneration:
    """Test color generation for heatmap cells"""
    
    def test_value_to_color_positive(self):
        """Test color for positive values"""
        from app.api.heatmap_routes import value_to_color
        
        # Max value should be green
        normalized, color = value_to_color(50, -20, 50, False)
        assert normalized == 1.0
        assert color.startswith('#')
        # Should be greenish (high green component)
        assert color[3:5] == 'ff'  # Green = 255
    
    def test_value_to_color_negative(self):
        """Test color for negative values"""
        from app.api.heatmap_routes import value_to_color
        
        # Min value should be red
        normalized, color = value_to_color(-20, -20, 50, False)
        assert normalized == 0.0
        assert color.startswith('#')
        # Should be reddish (high red component)
        assert color[1:3] == 'ff'  # Red = 255
    
    def test_value_to_color_neutral(self):
        """Test color for middle values"""
        from app.api.heatmap_routes import value_to_color
        
        # Middle value should be yellowish
        normalized, color = value_to_color(15, -20, 50, False)
        assert 0.4 <= normalized <= 0.6
        assert color.startswith('#')
    
    def test_value_to_color_inverted(self):
        """Test inverted color scale (for max_dd)"""
        from app.api.heatmap_routes import value_to_color
        
        # With inverted, high value should be red (bad)
        normalized, color = value_to_color(50, -20, 50, True)
        assert normalized == 0.0  # Inverted from 1.0
        assert color[1:3] == 'ff'  # Red = 255
    
    def test_value_to_color_same_range(self):
        """Test when min == max"""
        from app.api.heatmap_routes import value_to_color
        
        normalized, color = value_to_color(10, 10, 10, False)
        assert normalized == 0.5
        assert color.startswith('#')
    
    def test_value_to_color_clamp(self):
        """Test values outside range are clamped"""
        from app.api.heatmap_routes import value_to_color
        
        # Below range
        normalized, color = value_to_color(-100, -20, 50, False)
        assert normalized == 0.0
        
        # Above range
        normalized, color = value_to_color(100, -20, 50, False)
        assert normalized == 1.0


class TestHeatmapDataExtraction:
    """Test heatmap data extraction from result matrix"""
    
    @pytest.fixture
    def sample_result_matrix(self):
        """Sample optimization result matrix"""
        return {
            'preset_1': {
                'BTCUSDT': {
                    'total_pnl_percent': 25.5,
                    'win_rate': 65.0,
                    'max_drawdown': 12.5,
                    'sharpe_ratio': 1.8,
                    'total_trades': 45,
                    'profit_factor': 1.65
                },
                'ETHUSDT': {
                    'total_pnl_percent': 18.3,
                    'win_rate': 58.0,
                    'max_drawdown': 15.2,
                    'sharpe_ratio': 1.4,
                    'total_trades': 38,
                    'profit_factor': 1.45
                }
            },
            'preset_2': {
                'BTCUSDT': {
                    'total_pnl_percent': -5.2,
                    'win_rate': 42.0,
                    'max_drawdown': 22.1,
                    'sharpe_ratio': 0.5,
                    'total_trades': 52,
                    'profit_factor': 0.85
                },
                'ETHUSDT': {
                    'total_pnl_percent': 8.7,
                    'win_rate': 55.0,
                    'max_drawdown': 18.5,
                    'sharpe_ratio': 1.1,
                    'total_trades': 41,
                    'profit_factor': 1.25
                }
            }
        }
    
    @pytest.fixture
    def sample_preset_scores(self):
        """Sample preset aggregate scores"""
        return [
            {
                'preset_id': 'preset_1',
                'preset_name': 'T_60_40',
                'indicator_type': 'trg',
                'overall_score': 75.0
            },
            {
                'preset_id': 'preset_2',
                'preset_name': 'S_80_55',
                'indicator_type': 'trg',
                'overall_score': 55.0
            }
        ]
    
    def test_extract_heatmap_data_pnl(self, sample_result_matrix, sample_preset_scores):
        """Test extraction for PnL metric"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'pnl')
        
        assert data['metric'] == 'pnl'
        assert data['metric_label'] == 'PnL %'
        assert len(data['rows']) == 2
        assert len(data['pairs']) == 2
        assert 'BTCUSDT' in data['pairs']
        assert 'ETHUSDT' in data['pairs']
        
        # Check first row (should be preset_1 due to higher score)
        first_row = data['rows'][0]
        assert first_row['preset_id'] == 'preset_1'
        assert first_row['preset_name'] == 'T_60_40'
        assert len(first_row['cells']) == 2
    
    def test_extract_heatmap_data_win_rate(self, sample_result_matrix, sample_preset_scores):
        """Test extraction for Win Rate metric"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'win_rate')
        
        assert data['metric'] == 'win_rate'
        assert data['metric_label'] == 'Win Rate %'
        
        # Check value extraction
        first_row = data['rows'][0]
        btc_cell = next(c for c in first_row['cells'] if c['pair'] == 'BTCUSDT')
        assert btc_cell['value'] == 65.0
    
    def test_extract_heatmap_data_max_dd(self, sample_result_matrix, sample_preset_scores):
        """Test extraction for Max DD metric (inverted)"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'max_dd')
        
        assert data['metric'] == 'max_dd'
        # Lower DD should have higher normalized value (inverted)
        first_row = data['rows'][0]
        btc_cell = next(c for c in first_row['cells'] if c['pair'] == 'BTCUSDT')
        # 12.5 is the lowest DD, so it should have high normalized value
        assert btc_cell['value'] == 12.5
    
    def test_extract_heatmap_data_normalization(self, sample_result_matrix, sample_preset_scores):
        """Test that values are properly normalized"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'pnl')
        
        # All normalized values should be between 0 and 1
        for row in data['rows']:
            for cell in row['cells']:
                assert 0 <= cell['normalized'] <= 1
    
    def test_extract_heatmap_data_colors(self, sample_result_matrix, sample_preset_scores):
        """Test that colors are properly generated"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'pnl')
        
        # All cells should have valid hex colors
        for row in data['rows']:
            for cell in row['cells']:
                assert cell['color'].startswith('#')
                assert len(cell['color']) == 7  # #RRGGBB
    
    def test_extract_heatmap_data_min_max(self, sample_result_matrix, sample_preset_scores):
        """Test min/max/avg calculations"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data(sample_result_matrix, sample_preset_scores, 'pnl')
        
        assert data['min_value'] == -5.2  # lowest PnL
        assert data['max_value'] == 25.5  # highest PnL
        # Average of all 4 values: (25.5 + 18.3 + (-5.2) + 8.7) / 4 = 11.825
        assert abs(data['avg_value'] - 11.825) < 0.01
    
    def test_extract_heatmap_data_empty(self):
        """Test with empty result matrix"""
        from app.api.heatmap_routes import extract_heatmap_data
        
        data = extract_heatmap_data({}, [], 'pnl')
        
        assert 'error' in data
        assert data['presets'] == []
        assert data['pairs'] == []


class TestHeatmapCSVExport:
    """Test CSV export functionality"""
    
    def test_generate_csv(self):
        """Test CSV generation"""
        from app.api.heatmap_routes import generate_csv
        
        heatmap_data = {
            'pairs': ['BTCUSDT', 'ETHUSDT'],
            'rows': [
                {
                    'preset_name': 'T_60_40',
                    'indicator_type': 'trg',
                    'avg_value': 21.9,
                    'cells': [
                        {'pair': 'BTCUSDT', 'value': 25.5},
                        {'pair': 'ETHUSDT', 'value': 18.3}
                    ]
                }
            ],
            'min_value': -5.2,
            'max_value': 25.5,
            'avg_value': 11.825
        }
        
        csv_content = generate_csv(heatmap_data, 'pnl')
        
        assert 'Preset' in csv_content
        assert 'Indicator' in csv_content
        assert 'BTCUSDT' in csv_content
        assert 'ETHUSDT' in csv_content
        assert 'T_60_40' in csv_content
        assert 'trg' in csv_content


class TestHeatmapMetricConfig:
    """Test metric configuration"""
    
    def test_metric_config_exists(self):
        """Test that all required metrics are configured"""
        from app.api.heatmap_routes import METRIC_CONFIG
        
        required = ['pnl', 'win_rate', 'max_dd', 'sharpe', 'trades', 'profit_factor']
        for metric in required:
            assert metric in METRIC_CONFIG
    
    def test_metric_config_structure(self):
        """Test metric config structure"""
        from app.api.heatmap_routes import METRIC_CONFIG
        
        for key, config in METRIC_CONFIG.items():
            assert 'label' in config
            assert 'field' in config
            assert 'format' in config
            assert 'inverted' in config
            assert 'thresholds' in config
    
    def test_metric_format_functions(self):
        """Test metric format functions"""
        from app.api.heatmap_routes import METRIC_CONFIG
        
        # Test PnL format
        pnl_format = METRIC_CONFIG['pnl']['format']
        assert '+' in pnl_format(10.5)
        assert '-' in pnl_format(-5.2)
        
        # Test win rate format
        wr_format = METRIC_CONFIG['win_rate']['format']
        assert '%' in wr_format(65.0)


class TestColorScaleLegend:
    """Test color scale legend generation"""
    
    def test_get_color_scale_legend(self):
        """Test legend generation"""
        from app.api.heatmap_routes import get_color_scale_legend
        
        legend = get_color_scale_legend()
        
        assert isinstance(legend, dict)
        assert len(legend) > 0
        
        # All values should be hex colors
        for key, color in legend.items():
            assert color.startswith('#')
            assert len(color) == 7


class TestHeatmapIntegration:
    """Integration tests for heatmap endpoints"""
    
    @pytest.fixture
    def mock_result(self):
        """Create a mock optimization result"""
        return {
            'run_id': 'test_run_123',
            'mode': 'standard',
            'timeframe': '1h',
            'result_matrix': {
                'preset_1': {
                    'BTCUSDT': {
                        'total_pnl_percent': 25.5,
                        'win_rate': 65.0,
                        'max_drawdown': 12.5,
                        'sharpe_ratio': 1.8,
                        'total_trades': 45,
                        'profit_factor': 1.65
                    }
                }
            },
            'preset_scores': [
                {
                    'preset_id': 'preset_1',
                    'preset_name': 'T_60_40',
                    'indicator_type': 'trg',
                    'overall_score': 75.0
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_get_heatmap_endpoint(self, mock_result):
        """Test GET /api/optimizer/results/{run_id}/heatmap endpoint"""
        from app.api.heatmap_routes import get_heatmap_data
        
        # Patch at the source module where get_stored_result is defined
        with patch('app.api.optimizer_routes.get_stored_result', return_value=mock_result):
            # Pass explicit values instead of Query objects
            result = await get_heatmap_data('test_run_123', 'pnl', None, None)
            
            assert result['run_id'] == 'test_run_123'
            assert result['metric'] == 'pnl'
            assert len(result['rows']) > 0
    
    @pytest.mark.asyncio
    async def test_get_heatmap_invalid_metric(self, mock_result):
        """Test with invalid metric"""
        from app.api.heatmap_routes import get_heatmap_data
        from fastapi import HTTPException
        
        # Need to patch get_stored_result to return a result first
        # Then the invalid metric check will trigger
        with patch('app.api.optimizer_routes.get_stored_result', return_value=mock_result):
            with pytest.raises(HTTPException) as exc_info:
                await get_heatmap_data('test_run_123', 'invalid_metric', None, None)
            
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio  
    async def test_get_heatmap_not_found(self):
        """Test when run_id not found"""
        from app.api.heatmap_routes import get_heatmap_data
        from fastapi import HTTPException
        
        # Patch at the source module
        with patch('app.api.optimizer_routes.get_stored_result', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_heatmap_data('nonexistent_run', 'pnl', None, None)
            
            assert exc_info.value.status_code == 404


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
