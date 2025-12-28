"""
KOMAS v4.0 — Portfolio Filters
================================

Portfolio-based filters for controlling position diversity and risk distribution.

Filters:
- CorrelationFilter: Limit positions in correlated assets
- DirectionFilter: Control long/short position balance
- SectorFilter: Enforce diversification across sectors

Chat #41: Filters Portfolio
Author: KOMAS Team
Version: 4.0
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
import logging

from .base import (
    BaseFilter,
    Signal,
    SignalContext,
    FilterDecision,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
    create_skip_decision
)
from .registry import register_filter

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Default correlation settings
DEFAULT_MAX_CORRELATED_POSITIONS = 2
DEFAULT_CORRELATION_THRESHOLD = 0.7

# Default direction settings
DEFAULT_MAX_LONG_POSITIONS = 5
DEFAULT_MAX_SHORT_POSITIONS = 5
DEFAULT_NET_EXPOSURE_LIMIT = 3

# Default sector settings
DEFAULT_MAX_PER_SECTOR = 2


# =============================================================================
# SECTOR CLASSIFICATIONS
# =============================================================================

# Crypto sector mapping for major trading pairs
SECTOR_MAPPING: Dict[str, str] = {
    # Layer 1 - Base layer blockchains
    "BTCUSDT": "layer1",
    "ETHUSDT": "layer1",
    "SOLUSDT": "layer1",
    "AVAXUSDT": "layer1",
    "ADAUSDT": "layer1",
    "DOTUSDT": "layer1",
    "ATOMUSDT": "layer1",
    "NEARUSDT": "layer1",
    "APTUSDT": "layer1",
    "SUIUSDT": "layer1",
    "SEIUSDT": "layer1",
    "TONUSDT": "layer1",
    "INJUSDT": "layer1",
    "TIAUSDT": "layer1",
    
    # Layer 2 - Scaling solutions
    "MATICUSDT": "layer2",
    "ARBUSDT": "layer2",
    "OPUSDT": "layer2",
    "STXUSDT": "layer2",
    "IMXUSDT": "layer2",
    "METISUSDT": "layer2",
    "MANTAUSDT": "layer2",
    "STRKUSDT": "layer2",
    
    # DeFi - Decentralized Finance
    "UNIUSDT": "defi",
    "AAVEUSDT": "defi",
    "LINKUSDT": "defi",
    "SNXUSDT": "defi",
    "MKRUSDT": "defi",
    "COMPUSDT": "defi",
    "CRVUSDT": "defi",
    "SUSHIUSDT": "defi",
    "1INCHUSDT": "defi",
    "LDOUSDT": "defi",
    "RPLETH": "defi",
    "PENDLEUSDT": "defi",
    "GMXUSDT": "defi",
    "DYDXUSDT": "defi",
    "JUPUSDT": "defi",
    
    # Meme - Meme coins
    "DOGEUSDT": "meme",
    "SHIBUSDT": "meme",
    "PEPEUSDT": "meme",
    "FLOKIUSDT": "meme",
    "BONKUSDT": "meme",
    "WIFUSDT": "meme",
    "MEMEUSDT": "meme",
    "BOMEUSDT": "meme",
    "NEIROUSDT": "meme",
    
    # AI - Artificial Intelligence tokens
    "FETUSDT": "ai",
    "RENDERUSDT": "ai",
    "THETAUSDT": "ai",
    "AKUSDT": "ai",
    "OCEANUSDT": "ai",
    "AIUSDT": "ai",
    "NMRUSDT": "ai",
    "TAOUSDT": "ai",
    
    # Gaming - Gaming and Metaverse
    "AXSUSDT": "gaming",
    "SANDUSDT": "gaming",
    "MANAUSDT": "gaming",
    "GALAUSDT": "gaming",
    "ENJUSDT": "gaming",
    "ILUVDT": "gaming",
    "YGGUSDT": "gaming",
    "PIXELUSDT": "gaming",
    "RONINUSDT": "gaming",
    "PORTALUSDT": "gaming",
    
    # Infrastructure - Blockchain infrastructure
    "FILUSDT": "infrastructure",
    "GRTUSDT": "infrastructure",
    "STORJUSDT": "infrastructure",
    "ARUSDT": "infrastructure",
    "RNDR": "infrastructure",
    "ANKRUSDT": "infrastructure",
    "BANDUSDT": "infrastructure",
    "APIUSDT": "infrastructure",
    
    # Exchange Tokens
    "BNBUSDT": "exchange",
    "FTMUSDT": "exchange",  # Note: FTM is actually L1, but often grouped
    "OKBUSDT": "exchange",
    "CAKUSDT": "exchange",
    "JOEUSDT": "exchange",
    
    # Privacy - Privacy coins
    "XMRUSDT": "privacy",
    "ZECUSDT": "privacy",
    "DASHUSDT": "privacy",
    
    # Oracles
    "LINKUSDT": "oracle",  # Also DeFi
    "BANDUSDT": "oracle",
    "API3USDT": "oracle",
    "DIAUSDT": "oracle",
    "PYTHUSDT": "oracle",
    
    # RWA - Real World Assets
    "ONDOUSDT": "rwa",
    "PROUSDT": "rwa",
    "PLUMAUSDT": "rwa",
}

# All available sectors
AVAILABLE_SECTORS = [
    "layer1",
    "layer2", 
    "defi",
    "meme",
    "ai",
    "gaming",
    "infrastructure",
    "exchange",
    "privacy",
    "oracle",
    "rwa",
    "unknown"  # For unclassified symbols
]


# =============================================================================
# CORRELATION GROUPS
# =============================================================================

# Known high correlation groups (symbols that move together)
CORRELATION_GROUPS: Dict[str, List[str]] = {
    # BTC and related
    "btc_correlated": [
        "BTCUSDT", "ETHUSDT"  # High correlation
    ],
    
    # ETH ecosystem
    "eth_ecosystem": [
        "ETHUSDT", "MATICUSDT", "ARBUSDT", "OPUSDT", "LDOUSDT"
    ],
    
    # Solana ecosystem
    "sol_ecosystem": [
        "SOLUSDT", "BONKUSDT", "JUPUSDT", "WIFUSDT", "RAYUSDT"
    ],
    
    # DeFi blue chips
    "defi_major": [
        "UNIUSDT", "AAVEUSDT", "MKRUSDT", "COMPUSDT"
    ],
    
    # Meme coins
    "meme_coins": [
        "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT", "BONKUSDT", "WIFUSDT"
    ],
    
    # AI tokens
    "ai_tokens": [
        "FETUSDT", "RENDERUSDT", "THETAUSDT", "AKUSDT", "OCEANUSDT", "TAOUSDT"
    ],
    
    # Gaming tokens
    "gaming_tokens": [
        "AXSUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT", "ENJUSDT"
    ],
    
    # L1 alternatives
    "l1_alts": [
        "AVAXUSDT", "DOTUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT", "SUIUSDT"
    ],
    
    # L2 scaling
    "l2_scaling": [
        "MATICUSDT", "ARBUSDT", "OPUSDT", "IMXUSDT"
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_sector(symbol: str, sector_mapping: Optional[Dict[str, str]] = None) -> str:
    """
    Get sector classification for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        sector_mapping: Custom sector mapping (uses default if None)
        
    Returns:
        Sector name (e.g., 'layer1', 'defi', 'unknown')
    """
    mapping = sector_mapping or SECTOR_MAPPING
    return mapping.get(symbol.upper(), "unknown")


def get_correlation_groups_for_symbol(
    symbol: str,
    correlation_groups: Optional[Dict[str, List[str]]] = None
) -> List[str]:
    """
    Get correlation groups that contain a symbol.
    
    Args:
        symbol: Trading symbol
        correlation_groups: Custom correlation groups (uses default if None)
        
    Returns:
        List of group names containing this symbol
    """
    groups = correlation_groups or CORRELATION_GROUPS
    result = []
    symbol_upper = symbol.upper()
    
    for group_name, symbols in groups.items():
        if symbol_upper in [s.upper() for s in symbols]:
            result.append(group_name)
    
    return result


def are_correlated(
    symbol1: str,
    symbol2: str,
    correlation_groups: Optional[Dict[str, List[str]]] = None
) -> bool:
    """
    Check if two symbols are in the same correlation group.
    
    Args:
        symbol1: First symbol
        symbol2: Second symbol
        correlation_groups: Custom correlation groups
        
    Returns:
        True if symbols share at least one correlation group
    """
    groups1 = set(get_correlation_groups_for_symbol(symbol1, correlation_groups))
    groups2 = set(get_correlation_groups_for_symbol(symbol2, correlation_groups))
    return bool(groups1 & groups2)


def count_correlated_positions(
    symbol: str,
    open_positions: List[Dict],
    correlation_groups: Optional[Dict[str, List[str]]] = None
) -> Tuple[int, List[str]]:
    """
    Count how many open positions are correlated with a symbol.
    
    Args:
        symbol: Symbol to check
        open_positions: List of open positions (each has 'symbol' key)
        correlation_groups: Custom correlation groups
        
    Returns:
        Tuple of (count, list of correlated symbols)
    """
    correlated = []
    
    for pos in open_positions:
        pos_symbol = pos.get("symbol", "")
        if pos_symbol and pos_symbol.upper() != symbol.upper():
            if are_correlated(symbol, pos_symbol, correlation_groups):
                correlated.append(pos_symbol)
    
    return len(correlated), correlated


def count_positions_by_direction(
    open_positions: List[Dict]
) -> Tuple[int, int]:
    """
    Count open positions by direction.
    
    Args:
        open_positions: List of open positions
        
    Returns:
        Tuple of (long_count, short_count)
    """
    long_count = 0
    short_count = 0
    
    for pos in open_positions:
        direction = pos.get("direction", "").lower()
        if direction == "long":
            long_count += 1
        elif direction == "short":
            short_count += 1
    
    return long_count, short_count


def count_positions_by_sector(
    open_positions: List[Dict],
    sector_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """
    Count open positions by sector.
    
    Args:
        open_positions: List of open positions
        sector_mapping: Custom sector mapping
        
    Returns:
        Dict of sector -> count
    """
    counts: Dict[str, int] = {}
    
    for pos in open_positions:
        symbol = pos.get("symbol", "")
        if symbol:
            sector = get_sector(symbol, sector_mapping)
            counts[sector] = counts.get(sector, 0) + 1
    
    return counts


def get_positions_in_sector(
    open_positions: List[Dict],
    sector: str,
    sector_mapping: Optional[Dict[str, str]] = None
) -> List[Dict]:
    """
    Get all positions in a specific sector.
    
    Args:
        open_positions: List of open positions
        sector: Sector name
        sector_mapping: Custom sector mapping
        
    Returns:
        List of positions in the sector
    """
    result = []
    
    for pos in open_positions:
        symbol = pos.get("symbol", "")
        if symbol:
            pos_sector = get_sector(symbol, sector_mapping)
            if pos_sector == sector:
                result.append(pos)
    
    return result


def calculate_net_exposure(long_count: int, short_count: int) -> int:
    """
    Calculate net directional exposure.
    
    Args:
        long_count: Number of long positions
        short_count: Number of short positions
        
    Returns:
        Net exposure (positive = long bias, negative = short bias)
    """
    return long_count - short_count


def get_portfolio_summary(
    open_positions: List[Dict],
    sector_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Get comprehensive portfolio summary.
    
    Args:
        open_positions: List of open positions
        sector_mapping: Custom sector mapping
        
    Returns:
        Portfolio summary dict
    """
    long_count, short_count = count_positions_by_direction(open_positions)
    sector_counts = count_positions_by_sector(open_positions, sector_mapping)
    
    return {
        "total_positions": len(open_positions),
        "long_count": long_count,
        "short_count": short_count,
        "net_exposure": calculate_net_exposure(long_count, short_count),
        "sector_distribution": sector_counts,
        "unique_sectors": len([s for s, c in sector_counts.items() if c > 0])
    }


def get_portfolio_filter_summary(filters: List['BaseFilter']) -> Dict[str, Any]:
    """
    Get summary of all portfolio filters.
    
    Args:
        filters: List of portfolio filter instances
        
    Returns:
        Summary dict
    """
    enabled = []
    disabled = []
    
    for f in filters:
        if f.category == FilterCategory.PORTFOLIO:
            if f.enabled:
                enabled.append(f.name)
            else:
                disabled.append(f.name)
    
    return {
        "enabled_filters": enabled,
        "disabled_filters": disabled,
        "total": len(enabled) + len(disabled)
    }


def create_portfolio_filter_chain(
    correlation_config: Optional[Dict] = None,
    direction_config: Optional[Dict] = None,
    sector_config: Optional[Dict] = None
) -> List['BaseFilter']:
    """
    Create a chain of portfolio filters with given configs.
    
    Args:
        correlation_config: Config for CorrelationFilter
        direction_config: Config for DirectionFilter
        sector_config: Config for SectorFilter
        
    Returns:
        List of configured filter instances
    """
    filters = []
    
    if correlation_config is not None:
        filters.append(CorrelationFilter(correlation_config))
    
    if direction_config is not None:
        filters.append(DirectionFilter(direction_config))
    
    if sector_config is not None:
        filters.append(SectorFilter(sector_config))
    
    return filters


def validate_portfolio_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate portfolio filter configuration.
    
    Args:
        config: Portfolio filter config
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Correlation filter validation
    if "correlation" in config:
        corr_config = config["correlation"]
        if corr_config.get("max_correlated_positions", 0) < 0:
            errors.append("max_correlated_positions cannot be negative")
        threshold = corr_config.get("correlation_threshold", 0.7)
        if not 0 <= threshold <= 1:
            errors.append("correlation_threshold must be between 0 and 1")
    
    # Direction filter validation
    if "direction" in config:
        dir_config = config["direction"]
        if dir_config.get("max_long_positions", 0) < 0:
            errors.append("max_long_positions cannot be negative")
        if dir_config.get("max_short_positions", 0) < 0:
            errors.append("max_short_positions cannot be negative")
    
    # Sector filter validation
    if "sector" in config:
        sec_config = config["sector"]
        if sec_config.get("max_per_sector", 0) < 0:
            errors.append("max_per_sector cannot be negative")
    
    return len(errors) == 0, errors


def create_portfolio_profile(profile_name: str) -> Dict[str, Any]:
    """
    Create predefined portfolio filter profile.
    
    Args:
        profile_name: 'conservative', 'balanced', or 'aggressive'
        
    Returns:
        Portfolio filter configuration
    """
    profiles = {
        "conservative": {
            "correlation": {
                "enabled": True,
                "max_correlated_positions": 1,
                "correlation_threshold": 0.6
            },
            "direction": {
                "enabled": True,
                "max_long_positions": 3,
                "max_short_positions": 3,
                "net_exposure_limit": 2
            },
            "sector": {
                "enabled": True,
                "max_per_sector": 1
            }
        },
        "balanced": {
            "correlation": {
                "enabled": True,
                "max_correlated_positions": 2,
                "correlation_threshold": 0.7
            },
            "direction": {
                "enabled": True,
                "max_long_positions": 5,
                "max_short_positions": 5,
                "net_exposure_limit": 3
            },
            "sector": {
                "enabled": True,
                "max_per_sector": 2
            }
        },
        "aggressive": {
            "correlation": {
                "enabled": True,
                "max_correlated_positions": 3,
                "correlation_threshold": 0.8
            },
            "direction": {
                "enabled": True,
                "max_long_positions": 8,
                "max_short_positions": 8,
                "net_exposure_limit": 5
            },
            "sector": {
                "enabled": True,
                "max_per_sector": 3
            }
        }
    }
    
    return profiles.get(profile_name, profiles["balanced"])


# =============================================================================
# CORRELATION FILTER
# =============================================================================

@register_filter
class CorrelationFilter(BaseFilter):
    """
    Filter to limit positions in correlated assets.
    
    Prevents taking positions in assets that move together,
    reducing the risk of concentrated exposure.
    
    Config:
        max_correlated_positions: Maximum number of positions with high correlation
        correlation_threshold: Threshold above which assets are considered correlated
        correlation_groups: Dict of group_name -> list of correlated symbols
        use_predefined_groups: Whether to use predefined correlation groups
    """
    
    name = "correlation_filter"
    description = "Limits positions in correlated assets to reduce concentrated risk"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract configuration with defaults
        self.max_correlated_positions = self.config.get(
            "max_correlated_positions", 
            DEFAULT_MAX_CORRELATED_POSITIONS
        )
        self.correlation_threshold = self.config.get(
            "correlation_threshold",
            DEFAULT_CORRELATION_THRESHOLD
        )
        self.use_predefined_groups = self.config.get("use_predefined_groups", True)
        
        # Custom correlation groups (merged with predefined if enabled)
        custom_groups = self.config.get("correlation_groups", {})
        if self.use_predefined_groups:
            self.correlation_groups = {**CORRELATION_GROUPS, **custom_groups}
        else:
            self.correlation_groups = custom_groups
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if signal should be allowed based on correlation limits.
        
        Args:
            signal: Trading signal to evaluate
            context: Current market and portfolio context
            
        Returns:
            FilterDecision with pass/block result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Count correlated positions
        correlated_count, correlated_symbols = count_correlated_positions(
            signal.symbol,
            context.open_positions,
            self.correlation_groups
        )
        
        # Check against limit
        if correlated_count >= self.max_correlated_positions:
            return create_block_decision(
                self.name,
                f"Too many correlated positions ({correlated_count}/{self.max_correlated_positions})",
                correlated_count=correlated_count,
                correlated_symbols=correlated_symbols,
                limit=self.max_correlated_positions,
                signal_symbol=signal.symbol
            )
        
        return create_pass_decision(
            self.name,
            f"Correlation check passed ({correlated_count}/{self.max_correlated_positions})",
            correlated_count=correlated_count,
            correlated_symbols=correlated_symbols
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for UI."""
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable correlation filter"
            },
            "max_correlated_positions": {
                "type": "int",
                "default": DEFAULT_MAX_CORRELATED_POSITIONS,
                "min": 0,
                "max": 10,
                "description": "Maximum positions with high correlation"
            },
            "correlation_threshold": {
                "type": "float",
                "default": DEFAULT_CORRELATION_THRESHOLD,
                "min": 0.0,
                "max": 1.0,
                "description": "Correlation threshold (0-1)"
            },
            "use_predefined_groups": {
                "type": "bool",
                "default": True,
                "description": "Use predefined correlation groups"
            },
            "correlation_groups": {
                "type": "dict",
                "default": {},
                "description": "Custom correlation groups (group_name -> symbol list)"
            }
        }


# =============================================================================
# DIRECTION FILTER
# =============================================================================

@register_filter
class DirectionFilter(BaseFilter):
    """
    Filter to control long/short position balance.
    
    Limits the number of positions in each direction and
    controls net directional exposure.
    
    Config:
        max_long_positions: Maximum number of long positions
        max_short_positions: Maximum number of short positions
        allow_both_directions: Whether to allow both longs and shorts simultaneously
        net_exposure_limit: Maximum difference between longs and shorts
    """
    
    name = "direction_filter"
    description = "Controls long/short position balance and net exposure"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract configuration with defaults
        self.max_long_positions = self.config.get(
            "max_long_positions",
            DEFAULT_MAX_LONG_POSITIONS
        )
        self.max_short_positions = self.config.get(
            "max_short_positions",
            DEFAULT_MAX_SHORT_POSITIONS
        )
        self.allow_both_directions = self.config.get("allow_both_directions", True)
        self.net_exposure_limit = self.config.get(
            "net_exposure_limit",
            DEFAULT_NET_EXPOSURE_LIMIT
        )
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if signal should be allowed based on direction limits.
        
        Args:
            signal: Trading signal to evaluate
            context: Current market and portfolio context
            
        Returns:
            FilterDecision with pass/block result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Count current positions by direction
        long_count, short_count = count_positions_by_direction(context.open_positions)
        current_net = calculate_net_exposure(long_count, short_count)
        
        is_long = signal.direction.lower() == "long"
        is_short = signal.direction.lower() == "short"
        
        # Check direction limits
        if is_long and long_count >= self.max_long_positions:
            return create_block_decision(
                self.name,
                f"Max long positions reached ({long_count}/{self.max_long_positions})",
                long_count=long_count,
                short_count=short_count,
                limit=self.max_long_positions,
                direction="long"
            )
        
        if is_short and short_count >= self.max_short_positions:
            return create_block_decision(
                self.name,
                f"Max short positions reached ({short_count}/{self.max_short_positions})",
                long_count=long_count,
                short_count=short_count,
                limit=self.max_short_positions,
                direction="short"
            )
        
        # Check if both directions are allowed
        if not self.allow_both_directions:
            if is_long and short_count > 0:
                return create_block_decision(
                    self.name,
                    f"Cannot open long while {short_count} shorts are open",
                    long_count=long_count,
                    short_count=short_count,
                    requested_direction="long"
                )
            if is_short and long_count > 0:
                return create_block_decision(
                    self.name,
                    f"Cannot open short while {long_count} longs are open",
                    long_count=long_count,
                    short_count=short_count,
                    requested_direction="short"
                )
        
        # Check net exposure limit
        new_net = current_net + (1 if is_long else -1)
        if abs(new_net) > self.net_exposure_limit:
            return create_block_decision(
                self.name,
                f"Net exposure would exceed limit ({new_net}/{self.net_exposure_limit})",
                current_net_exposure=current_net,
                projected_net_exposure=new_net,
                limit=self.net_exposure_limit,
                long_count=long_count,
                short_count=short_count
            )
        
        return create_pass_decision(
            self.name,
            f"Direction check passed (L:{long_count} S:{short_count} Net:{current_net})",
            long_count=long_count,
            short_count=short_count,
            net_exposure=current_net
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for UI."""
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable direction filter"
            },
            "max_long_positions": {
                "type": "int",
                "default": DEFAULT_MAX_LONG_POSITIONS,
                "min": 0,
                "max": 20,
                "description": "Maximum number of long positions"
            },
            "max_short_positions": {
                "type": "int",
                "default": DEFAULT_MAX_SHORT_POSITIONS,
                "min": 0,
                "max": 20,
                "description": "Maximum number of short positions"
            },
            "allow_both_directions": {
                "type": "bool",
                "default": True,
                "description": "Allow both longs and shorts simultaneously"
            },
            "net_exposure_limit": {
                "type": "int",
                "default": DEFAULT_NET_EXPOSURE_LIMIT,
                "min": 0,
                "max": 20,
                "description": "Maximum net directional exposure (longs - shorts)"
            }
        }


# =============================================================================
# SECTOR FILTER
# =============================================================================

@register_filter
class SectorFilter(BaseFilter):
    """
    Filter to enforce diversification across sectors.
    
    Limits the number of positions per sector to ensure
    portfolio diversification.
    
    Config:
        max_per_sector: Maximum positions allowed per sector
        sector_mapping: Custom symbol -> sector mapping
        use_predefined_mapping: Whether to use predefined sector mapping
        excluded_sectors: Sectors to exclude from trading
    """
    
    name = "sector_filter"
    description = "Enforces diversification by limiting positions per sector"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract configuration with defaults
        self.max_per_sector = self.config.get(
            "max_per_sector",
            DEFAULT_MAX_PER_SECTOR
        )
        self.use_predefined_mapping = self.config.get("use_predefined_mapping", True)
        
        # Custom sector mapping (merged with predefined if enabled)
        custom_mapping = self.config.get("sector_mapping", {})
        if self.use_predefined_mapping:
            self.sector_mapping = {**SECTOR_MAPPING, **custom_mapping}
        else:
            self.sector_mapping = custom_mapping
        
        # Excluded sectors
        self.excluded_sectors = set(self.config.get("excluded_sectors", []))
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if signal should be allowed based on sector limits.
        
        Args:
            signal: Trading signal to evaluate
            context: Current market and portfolio context
            
        Returns:
            FilterDecision with pass/block result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Get sector for the signal's symbol
        signal_sector = get_sector(signal.symbol, self.sector_mapping)
        
        # Check if sector is excluded
        if signal_sector in self.excluded_sectors:
            return create_block_decision(
                self.name,
                f"Sector '{signal_sector}' is excluded from trading",
                sector=signal_sector,
                excluded_sectors=list(self.excluded_sectors)
            )
        
        # Count positions by sector
        sector_counts = count_positions_by_sector(
            context.open_positions,
            self.sector_mapping
        )
        
        current_sector_count = sector_counts.get(signal_sector, 0)
        
        # Check against limit
        if current_sector_count >= self.max_per_sector:
            positions_in_sector = get_positions_in_sector(
                context.open_positions,
                signal_sector,
                self.sector_mapping
            )
            existing_symbols = [p.get("symbol", "?") for p in positions_in_sector]
            
            return create_block_decision(
                self.name,
                f"Max positions in sector '{signal_sector}' reached ({current_sector_count}/{self.max_per_sector})",
                sector=signal_sector,
                current_count=current_sector_count,
                limit=self.max_per_sector,
                existing_symbols=existing_symbols
            )
        
        return create_pass_decision(
            self.name,
            f"Sector check passed ({signal_sector}: {current_sector_count}/{self.max_per_sector})",
            sector=signal_sector,
            current_count=current_sector_count,
            sector_distribution=sector_counts
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for UI."""
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable sector filter"
            },
            "max_per_sector": {
                "type": "int",
                "default": DEFAULT_MAX_PER_SECTOR,
                "min": 1,
                "max": 10,
                "description": "Maximum positions per sector"
            },
            "use_predefined_mapping": {
                "type": "bool",
                "default": True,
                "description": "Use predefined sector classifications"
            },
            "sector_mapping": {
                "type": "dict",
                "default": {},
                "description": "Custom symbol -> sector mapping"
            },
            "excluded_sectors": {
                "type": "list",
                "default": [],
                "options": AVAILABLE_SECTORS,
                "description": "Sectors excluded from trading"
            }
        }
