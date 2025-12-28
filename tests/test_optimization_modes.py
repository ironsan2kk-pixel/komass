"""
Unit Tests for Optimization Modes
==================================
Tests for optimization mode configurations and selection functions.

Chat #46: Preset Optimizer Modes
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from services.optimization_modes import (
    OptimizationMode,
    ModeConfig,
    MODE_CONFIGS,
    get_mode_config,
    get_liquidity_ranking,
    select_pairs_by_liquidity,
    select_pairs_by_diversity,
    select_pairs_by_representative,
    classify_preset,
    select_presets_clustered,
    select_presets_for_mode,
    select_pairs_for_mode,
    estimate_optimization_time,
    format_duration,
    get_all_modes_info,
    get_mode_info,
    PAIR_LIQUIDITY_SCORES,
    CORRELATION_GROUPS,
    PRESET_CLUSTERS,
)


# ============================================================================
# TEST DATA
# ============================================================================

SAMPLE_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT"
]

SAMPLE_PRESETS = [
    {"id": "N_14_20", "name": "N_14_20", "indicator_type": "trg", "params": {"i1": 14, "i2": 2.0}},
    {"id": "T_40_40", "name": "T_40_40", "indicator_type": "trg", "params": {"i1": 40, "i2": 4.0}},
    {"id": "M_60_55", "name": "M_60_55", "indicator_type": "trg", "params": {"i1": 60, "i2": 5.5}},
    {"id": "S_80_30", "name": "S_80_30", "indicator_type": "trg", "params": {"i1": 80, "i2": 3.0}},
    {"id": "F_110_45", "name": "F_110_45", "indicator_type": "trg", "params": {"i1": 110, "i2": 4.5}},
    {"id": "N_150_75", "name": "N_150_75", "indicator_type": "trg", "params": {"i1": 150, "i2": 7.5}},
    {"id": "T_25_25", "name": "T_25_25", "indicator_type": "trg", "params": {"i1": 25, "i2": 2.5}},
    {"id": "M_200_80", "name": "M_200_80", "indicator_type": "trg", "params": {"i1": 200, "i2": 8.0}},
]


# ============================================================================
# MODE CONFIG TESTS
# ============================================================================

class TestModeConfigs:
    """Test optimization mode configurations"""
    
    def test_all_modes_have_configs(self):
        """All OptimizationMode values should have configs"""
        for mode in OptimizationMode:
            assert mode in MODE_CONFIGS, f"Missing config for {mode}"
    
    def test_quick_mode_config(self):
        """Quick mode should have strict limits"""
        config = MODE_CONFIGS[OptimizationMode.QUICK]
        assert config.max_presets == 20
        assert config.max_pairs == 5
        assert config.preset_selection == "top_performers"
        assert config.pair_selection == "liquidity"
    
    def test_standard_mode_config(self):
        """Standard mode should have balanced limits"""
        config = MODE_CONFIGS[OptimizationMode.STANDARD]
        assert config.max_presets == 100
        assert config.max_pairs == 10
        assert config.preset_selection == "all"
        assert config.pair_selection == "diversity"
    
    def test_smart_mode_config(self):
        """Smart mode should use clustering"""
        config = MODE_CONFIGS[OptimizationMode.SMART]
        assert config.use_preset_clustering == True
        assert config.correlation_threshold == 0.7
        assert config.preset_selection == "representative"
    
    def test_full_mode_config(self):
        """Full mode should have no limits"""
        config = MODE_CONFIGS[OptimizationMode.FULL]
        assert config.max_presets is None
        assert config.max_pairs is None
        assert config.preset_selection == "all"
        assert config.pair_selection == "all"
    
    def test_get_mode_config_valid(self):
        """get_mode_config should return correct config for valid modes"""
        config = get_mode_config("quick")
        assert config.mode == OptimizationMode.QUICK
        
        config = get_mode_config("STANDARD")
        assert config.mode == OptimizationMode.STANDARD
    
    def test_get_mode_config_invalid(self):
        """get_mode_config should return STANDARD for invalid modes"""
        config = get_mode_config("invalid_mode")
        assert config.mode == OptimizationMode.STANDARD


# ============================================================================
# LIQUIDITY RANKING TESTS
# ============================================================================

class TestLiquidityRanking:
    """Test pair liquidity ranking functions"""
    
    def test_liquidity_scores_exist(self):
        """PAIR_LIQUIDITY_SCORES should have common pairs"""
        assert "BTCUSDT" in PAIR_LIQUIDITY_SCORES
        assert "ETHUSDT" in PAIR_LIQUIDITY_SCORES
        assert PAIR_LIQUIDITY_SCORES["BTCUSDT"] > PAIR_LIQUIDITY_SCORES["ETHUSDT"]
    
    def test_get_liquidity_ranking(self):
        """get_liquidity_ranking should return sorted pairs"""
        pairs = ["ETHUSDT", "BTCUSDT", "DOGEUSDT"]
        ranking = get_liquidity_ranking(pairs)
        
        assert len(ranking) == 3
        assert ranking[0][0] == "BTCUSDT"  # Most liquid first
        assert ranking[0][1] == 100
    
    def test_get_liquidity_ranking_unknown_pair(self):
        """Unknown pairs should get default score"""
        pairs = ["BTCUSDT", "UNKNOWNUSDT"]
        ranking = get_liquidity_ranking(pairs)
        
        assert len(ranking) == 2
        assert ranking[0][0] == "BTCUSDT"
        assert ranking[1][1] == 10  # Default score
    
    def test_select_pairs_by_liquidity(self):
        """select_pairs_by_liquidity should return top N by liquidity"""
        selected = select_pairs_by_liquidity(SAMPLE_PAIRS, 5)
        
        assert len(selected) == 5
        assert "BTCUSDT" in selected
        assert "ETHUSDT" in selected
    
    def test_select_pairs_by_liquidity_more_than_available(self):
        """Should return all if max_pairs > available"""
        selected = select_pairs_by_liquidity(SAMPLE_PAIRS[:3], 10)
        assert len(selected) == 3


# ============================================================================
# DIVERSITY SELECTION TESTS
# ============================================================================

class TestDiversitySelection:
    """Test pair diversity selection functions"""
    
    def test_correlation_groups_exist(self):
        """CORRELATION_GROUPS should have multiple groups"""
        assert len(CORRELATION_GROUPS) >= 5
        assert "btc_correlated" in CORRELATION_GROUPS
        assert "meme" in CORRELATION_GROUPS
    
    def test_select_pairs_by_diversity(self):
        """select_pairs_by_diversity should select from different groups"""
        pairs = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "AAVEUSDT", "SANDUSDT", 
                 "MATICUSDT", "SOLUSDT", "LTCUSDT", "AVAXUSDT", "ARBUSDT"]
        
        selected = select_pairs_by_diversity(pairs, 5)
        
        assert len(selected) == 5
        # Should have pairs from different groups
        groups_represented = set()
        for pair in selected:
            for group_name, group_pairs in CORRELATION_GROUPS.items():
                if pair.upper() in [p.upper() for p in group_pairs]:
                    groups_represented.add(group_name)
                    break
        
        assert len(groups_represented) >= 3  # At least 3 different groups
    
    def test_select_pairs_by_representative(self):
        """select_pairs_by_representative should minimize correlation"""
        selected = select_pairs_by_representative(SAMPLE_PAIRS, 5, 0.7)
        
        assert len(selected) == 5
        assert "BTCUSDT" in selected  # Most liquid first


# ============================================================================
# PRESET CLUSTERING TESTS
# ============================================================================

class TestPresetClustering:
    """Test preset clustering functions"""
    
    def test_preset_clusters_exist(self):
        """PRESET_CLUSTERS should have multiple clusters"""
        assert len(PRESET_CLUSTERS) >= 3
        assert "fast_scalp" in PRESET_CLUSTERS
        assert "slow_trend" in PRESET_CLUSTERS
    
    def test_classify_preset_fast_scalp(self):
        """Fast scalp preset should be classified correctly"""
        preset = {"params": {"i1": 14, "i2": 2.0}}
        cluster = classify_preset(preset)
        assert cluster == "fast_scalp"
    
    def test_classify_preset_slow_trend(self):
        """Slow trend preset should be classified correctly"""
        preset = {"params": {"i1": 150, "i2": 6.0}}
        cluster = classify_preset(preset)
        assert cluster == "slow_trend"
    
    def test_classify_preset_medium_swing(self):
        """Medium swing preset should be classified correctly"""
        preset = {"params": {"i1": 50, "i2": 4.0}}
        cluster = classify_preset(preset)
        assert cluster == "medium_swing"
    
    def test_select_presets_clustered(self):
        """select_presets_clustered should select from different clusters"""
        selected = select_presets_clustered(SAMPLE_PRESETS, 4)
        
        assert len(selected) == 4
        
        # Should have presets from different clusters
        clusters = set(classify_preset(p) for p in selected)
        assert len(clusters) >= 2


# ============================================================================
# MODE SELECTION TESTS
# ============================================================================

class TestModeSelection:
    """Test preset and pair selection for different modes"""
    
    def test_select_presets_for_quick_mode(self):
        """Quick mode should limit presets"""
        selected = select_presets_for_mode(SAMPLE_PRESETS * 5, "quick")
        assert len(selected) <= 20
    
    def test_select_presets_for_full_mode(self):
        """Full mode should return all presets"""
        selected = select_presets_for_mode(SAMPLE_PRESETS, "full")
        assert len(selected) == len(SAMPLE_PRESETS)
    
    def test_select_pairs_for_quick_mode(self):
        """Quick mode should select by liquidity"""
        selected = select_pairs_for_mode(SAMPLE_PAIRS, "quick")
        
        assert len(selected) <= 5
        assert "BTCUSDT" in selected  # Most liquid
    
    def test_select_pairs_for_standard_mode(self):
        """Standard mode should select by diversity"""
        selected = select_pairs_for_mode(SAMPLE_PAIRS, "standard")
        
        assert len(selected) <= 10
    
    def test_select_pairs_for_full_mode(self):
        """Full mode should return all pairs"""
        selected = select_pairs_for_mode(SAMPLE_PAIRS, "full")
        assert len(selected) == len(SAMPLE_PAIRS)


# ============================================================================
# TIME ESTIMATION TESTS
# ============================================================================

class TestTimeEstimation:
    """Test optimization time estimation"""
    
    def test_estimate_quick_mode(self):
        """Quick mode should estimate fast times"""
        estimate = estimate_optimization_time("quick", 200, 20, 8)
        
        assert estimate['mode'] == "quick"
        assert estimate['effective_presets'] <= 20
        assert estimate['effective_pairs'] <= 5
        assert estimate['estimated_seconds'] < 60  # Less than 1 minute
    
    def test_estimate_full_mode(self):
        """Full mode should estimate longer times"""
        estimate = estimate_optimization_time("full", 200, 20, 8)
        
        assert estimate['mode'] == "full"
        assert estimate['effective_presets'] == 200
        assert estimate['effective_pairs'] == 20
        assert estimate['total_combinations'] == 4000
    
    def test_estimate_with_parallelization(self):
        """More workers should reduce time"""
        estimate_4 = estimate_optimization_time("full", 100, 10, 4)
        estimate_8 = estimate_optimization_time("full", 100, 10, 8)
        
        assert estimate_8['estimated_seconds'] < estimate_4['estimated_seconds']
    
    def test_format_duration_seconds(self):
        """format_duration should format seconds correctly"""
        assert "seconds" in format_duration(30)
    
    def test_format_duration_minutes(self):
        """format_duration should format minutes correctly"""
        assert "min" in format_duration(120)
    
    def test_format_duration_hours(self):
        """format_duration should format hours correctly"""
        result = format_duration(3700)
        assert "h" in result


# ============================================================================
# MODE INFO TESTS
# ============================================================================

class TestModeInfo:
    """Test mode information functions"""
    
    def test_get_all_modes_info(self):
        """get_all_modes_info should return info for all modes"""
        modes_info = get_all_modes_info()
        
        assert len(modes_info) == 4
        mode_names = [m['mode'] for m in modes_info]
        assert 'quick' in mode_names
        assert 'standard' in mode_names
        assert 'smart' in mode_names
        assert 'full' in mode_names
    
    def test_get_mode_info(self):
        """get_mode_info should return detailed info"""
        info = get_mode_info("quick")
        
        assert info['mode'] == "quick"
        assert info['name'] == "Quick"
        assert 'description' in info
        assert 'max_presets' in info
        assert 'max_pairs' in info


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_presets_list(self):
        """Should handle empty presets list"""
        selected = select_presets_for_mode([], "quick")
        assert selected == []
    
    def test_empty_pairs_list(self):
        """Should handle empty pairs list"""
        selected = select_pairs_for_mode([], "quick")
        assert selected == []
    
    def test_single_preset(self):
        """Should handle single preset"""
        presets = [SAMPLE_PRESETS[0]]
        selected = select_presets_for_mode(presets, "full")
        assert len(selected) == 1
    
    def test_single_pair(self):
        """Should handle single pair"""
        pairs = ["BTCUSDT"]
        selected = select_pairs_for_mode(pairs, "full")
        assert len(selected) == 1
    
    def test_unknown_mode_fallback(self):
        """Unknown mode should fallback to standard"""
        selected = select_pairs_for_mode(SAMPLE_PAIRS, "unknown_mode")
        assert len(selected) <= 10  # Standard limit


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
