"""
KOMAS Trading Server - Optimization Modes
==========================================
Mode configurations for preset optimization.

Modes:
- Quick: Top 20 presets × 5 most liquid pairs (~100 combinations, < 1 min)
- Standard: All presets × 10 pairs (~1000+ combinations, < 5 min)
- Smart: Adaptive selection based on correlation and clustering
- Full: All presets × all pairs (comprehensive, 10+ min)

Chat #46: Preset Optimizer Modes
"""

import logging
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class OptimizationMode(str, Enum):
    """Optimization mode selection"""
    QUICK = "quick"        # ~100 combinations, < 1 min
    STANDARD = "standard"  # ~1000 combinations, < 5 min
    SMART = "smart"        # Adaptive, variable time
    FULL = "full"          # All combinations, 10+ min


# Pair liquidity ranking (based on typical Binance Futures volume)
# Higher score = more liquid
PAIR_LIQUIDITY_SCORES = {
    "BTCUSDT": 100,
    "ETHUSDT": 95,
    "BNBUSDT": 85,
    "SOLUSDT": 82,
    "XRPUSDT": 80,
    "DOGEUSDT": 78,
    "ADAUSDT": 75,
    "AVAXUSDT": 73,
    "DOTUSDT": 70,
    "LINKUSDT": 68,
    "MATICUSDT": 65,
    "LTCUSDT": 63,
    "ATOMUSDT": 60,
    "UNIUSDT": 58,
    "ETCUSDT": 55,
    "XLMUSDT": 53,
    "FILUSDT": 50,
    "APTUSDT": 48,
    "ARBUSDT": 47,
    "OPUSDT": 46,
    "NEARUSDT": 45,
    "TRXUSDT": 43,
    "AAVEUSDT": 40,
    "MKRUSDT": 38,
    "INJUSDT": 37,
    "FTMUSDT": 35,
    "SANDUSDT": 33,
    "MANAUSDT": 32,
    "GALAUSDT": 30,
    "AXSUSDT": 28,
    "RUNEUSDT": 27,
    "SUSHIUSDT": 25,
    "SNXUSDT": 24,
    "CRVUSDT": 23,
    "1INCHUSDT": 22,
    "COMPUSDT": 21,
    "YFIUSDT": 20,
    "BALUSDT": 19,
    "ZRXUSDT": 18,
    "ENSUSDT": 17,
    "LDOUSDT": 16,
    "GMXUSDT": 15,
    "DYDXUSDT": 14,
    "MASKUSDT": 13,
    "IMXUSDT": 12,
    "SUIUSDT": 45,  # Recently added, high volume
    "PEPEUSDT": 55,  # Meme coin, high volume
    "SHIBUSDT": 50,  # Meme coin
    "FLOKIUSDT": 35,  # Meme coin
    "WIFUSDT": 40,   # Meme coin
    "BONKUSDT": 38,  # Meme coin
}


# Correlation groups (pairs that tend to move together)
CORRELATION_GROUPS = {
    "btc_correlated": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
    "layer1": ["AVAXUSDT", "DOTUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT", "SUIUSDT"],
    "layer2": ["MATICUSDT", "ARBUSDT", "OPUSDT"],
    "defi_blue": ["AAVEUSDT", "UNIUSDT", "MKRUSDT", "LINKUSDT"],
    "defi_degen": ["SUSHIUSDT", "CRVUSDT", "COMPUSDT", "YFIUSDT", "1INCHUSDT"],
    "meme": ["DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "BONKUSDT"],
    "gaming": ["AXSUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT", "IMXUSDT"],
    "storage": ["FILUSDT"],
    "legacy": ["LTCUSDT", "ETCUSDT", "XLMUSDT", "TRXUSDT"],
}


# Preset clusters based on parameters (for smart mode)
PRESET_CLUSTERS = {
    "fast_scalp": {
        "i1_range": (10, 30),
        "i2_range": (1.5, 3.0),
        "description": "Fast scalping presets"
    },
    "medium_swing": {
        "i1_range": (30, 80),
        "i2_range": (3.0, 5.0),
        "description": "Medium-term swing presets"
    },
    "slow_trend": {
        "i1_range": (80, 200),
        "i2_range": (4.0, 8.0),
        "description": "Slow trend-following presets"
    },
    "tight_range": {
        "i1_range": (20, 60),
        "i2_range": (1.5, 3.0),
        "description": "Tight range presets"
    },
    "wide_range": {
        "i1_range": (40, 120),
        "i2_range": (5.0, 10.0),
        "description": "Wide range presets"
    }
}


# ============================================================================
# MODE CONFIGURATION
# ============================================================================

@dataclass
class ModeConfig:
    """Configuration for an optimization mode"""
    mode: OptimizationMode
    
    # Preset selection
    max_presets: Optional[int] = None  # None = all
    preset_selection: str = "all"  # all, top_performers, clustered, representative
    
    # Pair selection
    max_pairs: Optional[int] = None  # None = all
    pair_selection: str = "all"  # all, liquidity, diversity, representative
    
    # Smart mode options
    correlation_threshold: float = 0.7
    min_diversity: int = 5
    use_preset_clustering: bool = False
    
    # Timing
    estimated_time_per_backtest: float = 0.5  # seconds
    
    # Description
    description: str = ""
    
    @property
    def name(self) -> str:
        return self.mode.value.title()


# Predefined mode configurations
MODE_CONFIGS = {
    OptimizationMode.QUICK: ModeConfig(
        mode=OptimizationMode.QUICK,
        max_presets=20,
        max_pairs=5,
        preset_selection="top_performers",
        pair_selection="liquidity",
        description="Fast optimization with top presets and most liquid pairs. ~100 combinations, < 1 min."
    ),
    
    OptimizationMode.STANDARD: ModeConfig(
        mode=OptimizationMode.STANDARD,
        max_presets=100,
        max_pairs=10,
        preset_selection="all",
        pair_selection="diversity",
        description="Balanced optimization with diverse pair selection. ~1000 combinations, < 5 min."
    ),
    
    OptimizationMode.SMART: ModeConfig(
        mode=OptimizationMode.SMART,
        max_presets=50,
        max_pairs=15,
        preset_selection="representative",
        pair_selection="representative",
        correlation_threshold=0.7,
        min_diversity=5,
        use_preset_clustering=True,
        description="Adaptive optimization using correlation and clustering. Variable time."
    ),
    
    OptimizationMode.FULL: ModeConfig(
        mode=OptimizationMode.FULL,
        max_presets=None,
        max_pairs=None,
        preset_selection="all",
        pair_selection="all",
        description="Comprehensive optimization with all presets and pairs. 10+ min."
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_mode_config(mode: str) -> ModeConfig:
    """Get configuration for a specific mode"""
    try:
        opt_mode = OptimizationMode(mode.lower())
        return MODE_CONFIGS[opt_mode]
    except (ValueError, KeyError):
        logger.warning(f"Unknown mode '{mode}', defaulting to STANDARD")
        return MODE_CONFIGS[OptimizationMode.STANDARD]


def get_liquidity_ranking(pairs: List[str]) -> List[Tuple[str, int]]:
    """
    Rank pairs by liquidity.
    Returns list of (pair, score) tuples sorted by score descending.
    """
    rankings = []
    for pair in pairs:
        score = PAIR_LIQUIDITY_SCORES.get(pair.upper(), 10)  # Default score for unknown pairs
        rankings.append((pair, score))
    
    return sorted(rankings, key=lambda x: x[1], reverse=True)


def select_pairs_by_liquidity(pairs: List[str], max_pairs: int) -> List[str]:
    """Select top N pairs by liquidity"""
    ranked = get_liquidity_ranking(pairs)
    return [pair for pair, _ in ranked[:max_pairs]]


def select_pairs_by_diversity(pairs: List[str], max_pairs: int) -> List[str]:
    """
    Select pairs ensuring diversity across correlation groups.
    Picks at least one from each group if available.
    """
    selected = []
    used_groups = set()
    
    # First pass: one from each group
    for group_name, group_pairs in CORRELATION_GROUPS.items():
        available = [p for p in pairs if p.upper() in [gp.upper() for gp in group_pairs]]
        if available and len(selected) < max_pairs:
            # Pick the most liquid from this group
            ranked = get_liquidity_ranking(available)
            if ranked:
                selected.append(ranked[0][0])
                used_groups.add(group_name)
    
    # Second pass: fill remaining with most liquid
    if len(selected) < max_pairs:
        remaining = [p for p in pairs if p not in selected]
        ranked = get_liquidity_ranking(remaining)
        for pair, _ in ranked:
            if len(selected) >= max_pairs:
                break
            selected.append(pair)
    
    return selected


def select_pairs_by_representative(
    pairs: List[str], 
    max_pairs: int,
    correlation_threshold: float = 0.7
) -> List[str]:
    """
    Select representative pairs minimizing correlation overlap.
    """
    selected = []
    
    # Start with most liquid
    ranked = get_liquidity_ranking(pairs)
    if ranked:
        selected.append(ranked[0][0])
    
    # Build group membership for quick lookup
    pair_to_group = {}
    for group_name, group_pairs in CORRELATION_GROUPS.items():
        for gp in group_pairs:
            pair_to_group[gp.upper()] = group_name
    
    # Add pairs from different groups
    selected_groups = set()
    if selected:
        selected_groups.add(pair_to_group.get(selected[0].upper(), "unknown"))
    
    for pair, score in ranked[1:]:
        if len(selected) >= max_pairs:
            break
        
        pair_group = pair_to_group.get(pair.upper(), "unknown")
        
        # Prefer pairs from new groups
        if pair_group not in selected_groups or len(selected_groups) >= len(CORRELATION_GROUPS):
            selected.append(pair)
            selected_groups.add(pair_group)
    
    return selected


def classify_preset(preset: Dict) -> str:
    """Classify a preset into a cluster based on its parameters"""
    params = preset.get('params', preset)
    
    # Get i1 and i2 values
    i1 = params.get('i1', params.get('trg_atr_length', 45))
    i2 = params.get('i2', params.get('trg_multiplier', 4.0))
    
    # Check each cluster
    for cluster_name, cluster_def in PRESET_CLUSTERS.items():
        i1_min, i1_max = cluster_def['i1_range']
        i2_min, i2_max = cluster_def['i2_range']
        
        if i1_min <= i1 <= i1_max and i2_min <= i2 <= i2_max:
            return cluster_name
    
    return "other"


def select_presets_clustered(presets: List[Dict], max_presets: int) -> List[Dict]:
    """
    Select presets ensuring representation from each cluster.
    """
    # Group presets by cluster
    clusters = {}
    for preset in presets:
        cluster = classify_preset(preset)
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(preset)
    
    selected = []
    cluster_names = list(clusters.keys())
    
    # Round-robin selection from each cluster
    idx = 0
    while len(selected) < max_presets and any(clusters.values()):
        cluster_name = cluster_names[idx % len(cluster_names)]
        if clusters.get(cluster_name):
            preset = clusters[cluster_name].pop(0)
            selected.append(preset)
        idx += 1
        
        # Remove empty clusters
        cluster_names = [c for c in cluster_names if clusters.get(c)]
        if not cluster_names:
            break
    
    return selected


def select_presets_representative(
    presets: List[Dict], 
    max_presets: int,
    previous_results: Optional[Dict] = None
) -> List[Dict]:
    """
    Select representative presets based on parameter diversity.
    If previous_results provided, prioritize top performers.
    """
    if not presets:
        return []
    
    # If we have previous results, prioritize top performers
    if previous_results:
        # Sort by previous score if available
        def get_score(preset):
            preset_id = preset.get('id', '')
            if preset_id in previous_results:
                return previous_results[preset_id].get('overall_score', 0)
            return 0
        
        sorted_presets = sorted(presets, key=get_score, reverse=True)
        return sorted_presets[:max_presets]
    
    # Otherwise, use clustering for diversity
    return select_presets_clustered(presets, max_presets)


# ============================================================================
# TIME ESTIMATION
# ============================================================================

def estimate_optimization_time(
    mode: str,
    num_presets: int,
    num_pairs: int,
    num_workers: int = 4
) -> Dict:
    """
    Estimate optimization time based on mode and parameters.
    
    Returns:
        Dict with estimated times and breakdown
    """
    config = get_mode_config(mode)
    
    # Apply mode limits
    effective_presets = num_presets
    effective_pairs = num_pairs
    
    if config.max_presets:
        effective_presets = min(num_presets, config.max_presets)
    if config.max_pairs:
        effective_pairs = min(num_pairs, config.max_pairs)
    
    # Calculate combinations
    total_combinations = effective_presets * effective_pairs
    
    # Base time per backtest (adjusted by mode)
    base_time = config.estimated_time_per_backtest
    
    # Account for parallelization
    parallelization_factor = min(num_workers, 8)
    
    # Estimate total time
    estimated_seconds = (total_combinations * base_time) / parallelization_factor
    
    # Add overhead (10% for I/O, aggregation, etc.)
    estimated_seconds *= 1.1
    
    return {
        'mode': mode,
        'total_combinations': total_combinations,
        'effective_presets': effective_presets,
        'effective_pairs': effective_pairs,
        'num_workers': num_workers,
        'estimated_seconds': round(estimated_seconds, 1),
        'estimated_minutes': round(estimated_seconds / 60, 1),
        'human_readable': format_duration(estimated_seconds),
        'base_time_per_backtest': base_time,
        'description': config.description
    }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        if secs > 0:
            return f"{minutes} min {secs} sec"
        return f"{minutes} minutes"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


# ============================================================================
# MODE SELECTION HELPERS
# ============================================================================

def select_presets_for_mode(
    presets: List[Dict],
    mode: str,
    previous_results: Optional[Dict] = None
) -> List[Dict]:
    """
    Select presets based on optimization mode.
    
    Args:
        presets: All available presets
        mode: Optimization mode
        previous_results: Optional dict of previous results for top performer selection
    
    Returns:
        List of selected presets
    """
    config = get_mode_config(mode)
    
    if not presets:
        return []
    
    # Apply max limit
    max_presets = config.max_presets or len(presets)
    
    if config.preset_selection == "all":
        return presets[:max_presets]
    
    elif config.preset_selection == "top_performers":
        if previous_results:
            # Sort by previous overall_score
            def get_score(preset):
                preset_id = preset.get('id', '')
                if preset_id in previous_results:
                    return previous_results[preset_id].get('overall_score', 0)
                return 0
            
            sorted_presets = sorted(presets, key=get_score, reverse=True)
            return sorted_presets[:max_presets]
        else:
            # No previous results, use clustering
            return select_presets_clustered(presets, max_presets)
    
    elif config.preset_selection == "clustered":
        return select_presets_clustered(presets, max_presets)
    
    elif config.preset_selection == "representative":
        return select_presets_representative(presets, max_presets, previous_results)
    
    else:
        return presets[:max_presets]


def select_pairs_for_mode(
    pairs: List[str],
    mode: str
) -> List[str]:
    """
    Select pairs based on optimization mode.
    
    Args:
        pairs: All available pairs
        mode: Optimization mode
    
    Returns:
        List of selected pairs
    """
    config = get_mode_config(mode)
    
    if not pairs:
        return []
    
    # Apply max limit
    max_pairs = config.max_pairs or len(pairs)
    
    if len(pairs) <= max_pairs:
        return pairs
    
    if config.pair_selection == "all":
        return pairs[:max_pairs]
    
    elif config.pair_selection == "liquidity":
        return select_pairs_by_liquidity(pairs, max_pairs)
    
    elif config.pair_selection == "diversity":
        return select_pairs_by_diversity(pairs, max_pairs)
    
    elif config.pair_selection == "representative":
        return select_pairs_by_representative(
            pairs, 
            max_pairs, 
            config.correlation_threshold
        )
    
    else:
        return pairs[:max_pairs]


# ============================================================================
# MODE INFO
# ============================================================================

def get_all_modes_info() -> List[Dict]:
    """Get information about all available modes"""
    modes_info = []
    
    for mode in OptimizationMode:
        config = MODE_CONFIGS[mode]
        modes_info.append({
            'mode': mode.value,
            'name': config.name,
            'description': config.description,
            'max_presets': config.max_presets,
            'max_pairs': config.max_pairs,
            'preset_selection': config.preset_selection,
            'pair_selection': config.pair_selection,
            'use_clustering': config.use_preset_clustering
        })
    
    return modes_info


def get_mode_info(mode: str) -> Dict:
    """Get information about a specific mode"""
    config = get_mode_config(mode)
    
    return {
        'mode': config.mode.value,
        'name': config.name,
        'description': config.description,
        'max_presets': config.max_presets,
        'max_pairs': config.max_pairs,
        'preset_selection': config.preset_selection,
        'pair_selection': config.pair_selection,
        'correlation_threshold': config.correlation_threshold,
        'use_clustering': config.use_preset_clustering
    }
