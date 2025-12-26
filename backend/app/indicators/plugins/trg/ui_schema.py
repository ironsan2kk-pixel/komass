# -*- coding: utf-8 -*-
"""
TRG Plugin - UI Schema
======================
Defines the complete UI schema for dynamic frontend generation.
Includes sidebar sections, tabs, field definitions, and helpers.

Version: 1.0.0
Compatible with: TRG Plugin v1.4.0
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


# =============================================================================
# ENUMS
# =============================================================================

class FieldType(str, Enum):
    """UI Field types"""
    NUMBER = "number"
    SLIDER = "slider"
    SELECT = "select"
    CHECKBOX = "checkbox"
    TOGGLE = "toggle"
    BUTTON_GROUP = "button_group"
    TEXT = "text"
    COLOR = "color"
    RANGE = "range"
    DYNAMIC_LIST = "dynamic_list"


class SectionType(str, Enum):
    """Section types"""
    STATIC = "static"
    COLLAPSIBLE = "collapsible"
    DYNAMIC = "dynamic"


class TabType(str, Enum):
    """Tab content types"""
    CHART = "chart"
    STATS = "stats"
    TABLE = "table"
    PANEL = "panel"
    CUSTOM = "custom"


# =============================================================================
# FIELD DEFINITIONS
# =============================================================================

@dataclass
class FieldOption:
    """Option for select/button_group fields"""
    value: Any
    label: str
    icon: str = ""
    color: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class UIField:
    """Definition of a UI field"""
    id: str
    type: FieldType
    label: str
    default: Any = None
    
    # Number/Slider constraints
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    
    # Select/Button group options
    options: List[FieldOption] = field(default_factory=list)
    
    # Formatting
    suffix: str = ""
    prefix: str = ""
    format: str = ""  # "percent", "currency", "decimal"
    
    # Behavior
    disabled: bool = False
    hidden: bool = False
    depends_on: Optional[str] = None  # Show only if another field is truthy
    depends_value: Any = None  # Show only if another field equals this value
    
    # Validation
    required: bool = False
    validation: str = ""  # Custom validation rule
    
    # Description/Help
    description: str = ""
    placeholder: str = ""
    tooltip: str = ""
    
    # Styling
    width: str = "full"  # "full", "half", "third", "quarter"
    color_scheme: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, FieldType) else self.type,
            "label": self.label,
        }
        
        # Add optional fields only if set
        if self.default is not None:
            result["default"] = self.default
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.step is not None:
            result["step"] = self.step
        if self.options:
            result["options"] = [o.to_dict() for o in self.options]
        if self.suffix:
            result["suffix"] = self.suffix
        if self.prefix:
            result["prefix"] = self.prefix
        if self.format:
            result["format"] = self.format
        if self.disabled:
            result["disabled"] = self.disabled
        if self.hidden:
            result["hidden"] = self.hidden
        if self.depends_on:
            result["depends_on"] = self.depends_on
        if self.depends_value is not None:
            result["depends_value"] = self.depends_value
        if self.required:
            result["required"] = self.required
        if self.validation:
            result["validation"] = self.validation
        if self.description:
            result["description"] = self.description
        if self.placeholder:
            result["placeholder"] = self.placeholder
        if self.tooltip:
            result["tooltip"] = self.tooltip
        if self.width != "full":
            result["width"] = self.width
        if self.color_scheme:
            result["color_scheme"] = self.color_scheme
            
        return result


# =============================================================================
# SECTION DEFINITIONS
# =============================================================================

@dataclass
class UISection:
    """Definition of a UI section (sidebar panel)"""
    id: str
    title: str
    icon: str
    fields: List[UIField]
    
    type: SectionType = SectionType.COLLAPSIBLE
    default_open: bool = True
    order: int = 0
    
    # Dynamic section options
    dynamic_source: str = ""  # For dynamic sections, the data source
    dynamic_template: str = ""  # Template for dynamic field generation
    
    # Description
    description: str = ""
    help_link: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "title": self.title,
            "icon": self.icon,
            "type": self.type.value if isinstance(self.type, SectionType) else self.type,
            "default_open": self.default_open,
            "order": self.order,
            "fields": [f.to_dict() for f in self.fields],
        }
        
        if self.dynamic_source:
            result["dynamic_source"] = self.dynamic_source
        if self.dynamic_template:
            result["dynamic_template"] = self.dynamic_template
        if self.description:
            result["description"] = self.description
        if self.help_link:
            result["help_link"] = self.help_link
            
        return result


# =============================================================================
# TAB DEFINITIONS
# =============================================================================

@dataclass
class UITab:
    """Definition of a UI tab"""
    id: str
    label: str
    icon: str
    type: TabType = TabType.CUSTOM
    
    # Tab configuration
    order: int = 0
    default: bool = False  # Is this the default tab?
    disabled: bool = False
    hidden: bool = False
    
    # Component configuration
    component: str = ""  # React component name
    props: Dict[str, Any] = field(default_factory=dict)
    
    # Description
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "label": self.label,
            "icon": self.icon,
            "type": self.type.value if isinstance(self.type, TabType) else self.type,
            "order": self.order,
        }
        
        if self.default:
            result["default"] = self.default
        if self.disabled:
            result["disabled"] = self.disabled
        if self.hidden:
            result["hidden"] = self.hidden
        if self.component:
            result["component"] = self.component
        if self.props:
            result["props"] = self.props
        if self.description:
            result["description"] = self.description
            
        return result


# =============================================================================
# TRG UI SCHEMA DEFINITION
# =============================================================================

class TRGUISchema:
    """
    Complete UI Schema for TRG Plugin.
    
    Provides:
    - Sidebar sections with all settings
    - Tab definitions for main content area
    - Helper methods for dynamic UI generation
    - Validation schemas
    - Default values
    """
    
    VERSION = "1.0.0"
    PLUGIN_VERSION = "1.4.0"
    
    def __init__(self):
        self._sections = self._build_sections()
        self._tabs = self._build_tabs()
        self._defaults = self._build_defaults()
        self._validation = self._build_validation_rules()
    
    # =========================================================================
    # SECTION BUILDERS
    # =========================================================================
    
    def _build_indicator_section(self) -> UISection:
        """TRG Indicator settings (i1, i2)"""
        return UISection(
            id="indicator",
            title="TRG Indicator",
            icon="📊",
            order=1,
            default_open=True,
            description="Core TRG indicator parameters",
            fields=[
                UIField(
                    id="trg_atr_length",
                    type=FieldType.NUMBER,
                    label="i1 (ATR Length)",
                    default=45,
                    min=10,
                    max=200,
                    step=1,
                    description="ATR period for volatility calculation",
                    tooltip="Higher values = smoother, slower signals"
                ),
                UIField(
                    id="trg_multiplier",
                    type=FieldType.NUMBER,
                    label="i2 (Multiplier)",
                    default=4.0,
                    min=1.0,
                    max=10.0,
                    step=0.5,
                    description="ATR multiplier for channel width",
                    tooltip="Higher values = wider channels, fewer signals"
                ),
            ]
        )
    
    def _build_take_profit_section(self) -> UISection:
        """Take Profit settings (10 levels)"""
        # TP count selector
        tp_count_options = [
            FieldOption(value=i, label=str(i)) for i in range(1, 11)
        ]
        
        fields = [
            UIField(
                id="tp_count",
                type=FieldType.BUTTON_GROUP,
                label="Count",
                default=4,
                options=tp_count_options,
                description="Number of active take profit levels"
            ),
        ]
        
        # Generate 10 TP level fields
        tp_colors = [
            "#22c55e",  # TP1 - green
            "#3b82f6",  # TP2 - blue
            "#a855f7",  # TP3 - purple
            "#f97316",  # TP4 - orange
            "#06b6d4",  # TP5 - cyan
            "#ec4899",  # TP6 - pink
            "#eab308",  # TP7 - yellow
            "#84cc16",  # TP8 - lime
            "#6366f1",  # TP9 - indigo
            "#14b8a6",  # TP10 - teal
        ]
        
        tp_defaults = [
            (1.05, 50), (1.95, 30), (3.75, 15), (6.0, 5),
            (8.0, 0), (10.0, 0), (12.0, 0), (15.0, 0),
            (20.0, 0), (25.0, 0)
        ]
        
        for i in range(1, 11):
            percent_default, amount_default = tp_defaults[i - 1]
            color = tp_colors[i - 1]
            
            fields.append(UIField(
                id=f"tp{i}_percent",
                type=FieldType.NUMBER,
                label=f"TP{i} %",
                default=percent_default,
                min=0.1,
                max=100.0,
                step=0.1,
                suffix="%",
                width="half",
                color_scheme=color,
                depends_on="tp_count",
                depends_value=list(range(i, 11)),  # Show if tp_count >= i
                description=f"Take profit level {i} percentage"
            ))
            
            fields.append(UIField(
                id=f"tp{i}_amount",
                type=FieldType.NUMBER,
                label=f"TP{i} Amount",
                default=amount_default,
                min=0,
                max=100,
                step=5,
                suffix="%",
                width="half",
                color_scheme=color,
                depends_on="tp_count",
                depends_value=list(range(i, 11)),
                description=f"Position size to close at TP{i}"
            ))
        
        return UISection(
            id="take_profit",
            title="Take Profits",
            icon="🎯",
            order=2,
            default_open=True,
            description="Configure up to 10 take profit levels",
            fields=fields
        )
    
    def _build_stop_loss_section(self) -> UISection:
        """Stop Loss settings"""
        return UISection(
            id="stop_loss",
            title="Stop Loss",
            icon="🛑",
            order=3,
            default_open=True,
            description="Stop loss configuration and trailing modes",
            fields=[
                UIField(
                    id="sl_percent",
                    type=FieldType.NUMBER,
                    label="SL %",
                    default=8.0,
                    min=1.0,
                    max=50.0,
                    step=0.5,
                    suffix="%",
                    description="Initial stop loss percentage from entry"
                ),
                UIField(
                    id="sl_trailing_mode",
                    type=FieldType.BUTTON_GROUP,
                    label="Trailing",
                    default="breakeven",
                    options=[
                        FieldOption(value="no", label="Фикс", icon="🔒"),
                        FieldOption(value="breakeven", label="БУ", icon="⚖️"),
                        FieldOption(value="moving", label="Каскад", icon="📶"),
                    ],
                    description="Stop loss trailing mode"
                ),
                UIField(
                    id="sl_breakeven_trigger",
                    type=FieldType.SELECT,
                    label="БУ Триггер",
                    default="tp1",
                    options=[
                        FieldOption(value="tp1", label="После TP1"),
                        FieldOption(value="tp2", label="После TP2"),
                        FieldOption(value="tp3", label="После TP3"),
                    ],
                    depends_on="sl_trailing_mode",
                    depends_value=["breakeven", "moving"],
                    description="When to move stop to breakeven"
                ),
                UIField(
                    id="sl_cascade_levels",
                    type=FieldType.CHECKBOX,
                    label="Каскадные уровни",
                    default=True,
                    depends_on="sl_trailing_mode",
                    depends_value="moving",
                    description="Move SL to each TP level as they hit"
                ),
            ]
        )
    
    def _build_leverage_section(self) -> UISection:
        """Leverage and Commission settings"""
        return UISection(
            id="leverage",
            title="Плечо и комиссия",
            icon="⚡",
            order=4,
            default_open=False,
            description="Leverage and commission settings",
            fields=[
                UIField(
                    id="leverage",
                    type=FieldType.NUMBER,
                    label="Leverage",
                    default=1,
                    min=1,
                    max=125,
                    step=1,
                    suffix="x",
                    description="Trading leverage multiplier"
                ),
                UIField(
                    id="use_commission",
                    type=FieldType.CHECKBOX,
                    label="Учитывать комиссию",
                    default=False,
                    description="Include commission in PnL calculations"
                ),
                UIField(
                    id="commission_percent",
                    type=FieldType.NUMBER,
                    label="Комиссия",
                    default=0.1,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    suffix="%",
                    depends_on="use_commission",
                    depends_value=True,
                    description="Commission percentage per trade"
                ),
            ]
        )
    
    def _build_filters_section(self) -> UISection:
        """Signal filters settings"""
        return UISection(
            id="filters",
            title="Фильтры",
            icon="🔍",
            order=5,
            default_open=False,
            description="Enable additional filters to improve signal quality",
            fields=[
                # SuperTrend
                UIField(
                    id="use_supertrend",
                    type=FieldType.CHECKBOX,
                    label="SuperTrend",
                    default=False,
                    description="Filter signals with SuperTrend direction"
                ),
                UIField(
                    id="supertrend_period",
                    type=FieldType.NUMBER,
                    label="ST Period",
                    default=10,
                    min=5,
                    max=50,
                    step=1,
                    depends_on="use_supertrend",
                    depends_value=True,
                ),
                UIField(
                    id="supertrend_multiplier",
                    type=FieldType.NUMBER,
                    label="ST Multiplier",
                    default=3.0,
                    min=1.0,
                    max=10.0,
                    step=0.5,
                    depends_on="use_supertrend",
                    depends_value=True,
                ),
                
                # RSI
                UIField(
                    id="use_rsi_filter",
                    type=FieldType.CHECKBOX,
                    label="RSI Filter",
                    default=False,
                    description="Filter overbought/oversold conditions"
                ),
                UIField(
                    id="rsi_period",
                    type=FieldType.NUMBER,
                    label="RSI Period",
                    default=14,
                    min=5,
                    max=50,
                    step=1,
                    depends_on="use_rsi_filter",
                    depends_value=True,
                ),
                UIField(
                    id="rsi_overbought",
                    type=FieldType.NUMBER,
                    label="Overbought",
                    default=70,
                    min=50,
                    max=100,
                    step=1,
                    depends_on="use_rsi_filter",
                    depends_value=True,
                ),
                UIField(
                    id="rsi_oversold",
                    type=FieldType.NUMBER,
                    label="Oversold",
                    default=30,
                    min=0,
                    max=50,
                    step=1,
                    depends_on="use_rsi_filter",
                    depends_value=True,
                ),
                
                # ADX
                UIField(
                    id="use_adx_filter",
                    type=FieldType.CHECKBOX,
                    label="ADX Filter",
                    default=False,
                    description="Filter by trend strength"
                ),
                UIField(
                    id="adx_period",
                    type=FieldType.NUMBER,
                    label="ADX Period",
                    default=14,
                    min=5,
                    max=50,
                    step=1,
                    depends_on="use_adx_filter",
                    depends_value=True,
                ),
                UIField(
                    id="adx_threshold",
                    type=FieldType.NUMBER,
                    label="ADX Threshold",
                    default=25,
                    min=10,
                    max=50,
                    step=1,
                    depends_on="use_adx_filter",
                    depends_value=True,
                ),
                
                # Volume
                UIField(
                    id="use_volume_filter",
                    type=FieldType.CHECKBOX,
                    label="Volume Filter",
                    default=False,
                    description="Filter by volume spike"
                ),
                UIField(
                    id="volume_ma_period",
                    type=FieldType.NUMBER,
                    label="Volume MA Period",
                    default=20,
                    min=5,
                    max=100,
                    step=1,
                    depends_on="use_volume_filter",
                    depends_value=True,
                ),
                UIField(
                    id="volume_threshold",
                    type=FieldType.NUMBER,
                    label="Volume Threshold",
                    default=1.5,
                    min=1.0,
                    max=5.0,
                    step=0.1,
                    suffix="x",
                    depends_on="use_volume_filter",
                    depends_value=True,
                ),
            ]
        )
    
    def _build_reentry_section(self) -> UISection:
        """Re-entry settings"""
        return UISection(
            id="reentry",
            title="Повторные входы",
            icon="🔄",
            order=6,
            default_open=False,
            description="Configure re-entry after trade closure",
            fields=[
                UIField(
                    id="allow_reentry",
                    type=FieldType.CHECKBOX,
                    label="Разрешить повторный вход",
                    default=False,
                    description="Allow re-entering position after closure"
                ),
                UIField(
                    id="reentry_after_sl",
                    type=FieldType.CHECKBOX,
                    label="После SL",
                    default=True,
                    depends_on="allow_reentry",
                    depends_value=True,
                    description="Re-enter after stop loss hit"
                ),
                UIField(
                    id="reentry_after_tp",
                    type=FieldType.CHECKBOX,
                    label="После TP",
                    default=True,
                    depends_on="allow_reentry",
                    depends_value=True,
                    description="Re-enter after all take profits hit"
                ),
                UIField(
                    id="reentry_delay_bars",
                    type=FieldType.NUMBER,
                    label="Задержка (свечей)",
                    default=1,
                    min=0,
                    max=10,
                    step=1,
                    depends_on="allow_reentry",
                    depends_value=True,
                    description="Bars to wait before re-entry"
                ),
            ]
        )
    
    def _build_adaptive_section(self) -> UISection:
        """Adaptive optimization settings"""
        return UISection(
            id="adaptive",
            title="Адаптивный режим",
            icon="🧠",
            order=7,
            default_open=False,
            description="Auto-adjust parameters based on recent performance",
            fields=[
                UIField(
                    id="adaptive_mode",
                    type=FieldType.SELECT,
                    label="Режим",
                    default="",
                    options=[
                        FieldOption(value="", label="Выключен"),
                        FieldOption(value="indicator", label="Индикатор"),
                        FieldOption(value="tp", label="Take Profits"),
                        FieldOption(value="all", label="Всё"),
                    ],
                    description="What to auto-optimize"
                ),
                UIField(
                    id="adaptive_lookback",
                    type=FieldType.NUMBER,
                    label="Lookback (сделок)",
                    default=20,
                    min=10,
                    max=100,
                    step=5,
                    depends_on="adaptive_mode",
                    description="Number of trades to analyze"
                ),
                UIField(
                    id="adaptive_recalc_trades",
                    type=FieldType.NUMBER,
                    label="Пересчёт каждые",
                    default=20,
                    min=5,
                    max=50,
                    step=5,
                    suffix="сделок",
                    depends_on="adaptive_mode",
                    description="Recalculate every N trades"
                ),
            ]
        )
    
    def _build_capital_section(self) -> UISection:
        """Capital and risk management"""
        return UISection(
            id="capital",
            title="Капитал",
            icon="💰",
            order=8,
            default_open=False,
            description="Initial capital and position sizing",
            fields=[
                UIField(
                    id="initial_capital",
                    type=FieldType.NUMBER,
                    label="Начальный капитал",
                    default=10000,
                    min=100,
                    max=10000000,
                    step=100,
                    suffix="$",
                    format="currency",
                    description="Starting capital for backtest"
                ),
                UIField(
                    id="position_size_type",
                    type=FieldType.SELECT,
                    label="Размер позиции",
                    default="percent",
                    options=[
                        FieldOption(value="percent", label="% от капитала"),
                        FieldOption(value="fixed", label="Фиксированный"),
                        FieldOption(value="risk", label="По риску"),
                    ],
                    description="How to calculate position size"
                ),
                UIField(
                    id="position_size_value",
                    type=FieldType.NUMBER,
                    label="Значение",
                    default=100,
                    min=1,
                    max=100,
                    step=1,
                    suffix="%",
                    description="Position size value"
                ),
            ]
        )
    
    def _build_data_section(self) -> UISection:
        """Data source settings"""
        return UISection(
            id="data",
            title="Данные",
            icon="📈",
            order=0,
            default_open=True,
            type=SectionType.STATIC,
            description="Select trading pair and timeframe",
            fields=[
                UIField(
                    id="symbol",
                    type=FieldType.SELECT,
                    label="Пара",
                    default="BTCUSDT",
                    options=[],  # Populated dynamically
                    description="Trading pair"
                ),
                UIField(
                    id="timeframe",
                    type=FieldType.SELECT,
                    label="Таймфрейм",
                    default="1h",
                    options=[
                        FieldOption(value="1m", label="1m"),
                        FieldOption(value="3m", label="3m"),
                        FieldOption(value="5m", label="5m"),
                        FieldOption(value="15m", label="15m"),
                        FieldOption(value="30m", label="30m"),
                        FieldOption(value="1h", label="1h"),
                        FieldOption(value="2h", label="2h"),
                        FieldOption(value="4h", label="4h"),
                        FieldOption(value="6h", label="6h"),
                        FieldOption(value="8h", label="8h"),
                        FieldOption(value="12h", label="12h"),
                        FieldOption(value="1d", label="1D"),
                        FieldOption(value="3d", label="3D"),
                        FieldOption(value="1w", label="1W"),
                    ],
                    description="Candlestick timeframe"
                ),
            ]
        )
    
    def _build_sections(self) -> List[UISection]:
        """Build all sidebar sections"""
        return [
            self._build_data_section(),
            self._build_indicator_section(),
            self._build_take_profit_section(),
            self._build_stop_loss_section(),
            self._build_leverage_section(),
            self._build_filters_section(),
            self._build_reentry_section(),
            self._build_adaptive_section(),
            self._build_capital_section(),
        ]
    
    # =========================================================================
    # TAB BUILDERS
    # =========================================================================
    
    def _build_tabs(self) -> List[UITab]:
        """Build all tabs"""
        return [
            UITab(
                id="chart",
                label="График",
                icon="📈",
                type=TabType.CHART,
                order=1,
                default=True,
                component="ChartPanel",
                description="Candlestick chart with indicators and trades"
            ),
            UITab(
                id="stats",
                label="Статистика",
                icon="📊",
                type=TabType.STATS,
                order=2,
                component="StatsPanel",
                description="Trading statistics and performance metrics"
            ),
            UITab(
                id="trades",
                label="Сделки",
                icon="📋",
                type=TabType.TABLE,
                order=3,
                component="TradesTable",
                description="Detailed trade history"
            ),
            UITab(
                id="monthly",
                label="Месяцы",
                icon="📅",
                type=TabType.PANEL,
                order=4,
                component="MonthlyPanel",
                description="Monthly PnL breakdown"
            ),
            UITab(
                id="optimizer",
                label="Оптимизация",
                icon="🔥",
                type=TabType.PANEL,
                order=5,
                component="AutoOptimizePanel",
                description="Parameter optimization with multi-core support"
            ),
            UITab(
                id="heatmap",
                label="Heatmap",
                icon="🗺️",
                type=TabType.PANEL,
                order=6,
                component="HeatmapPanel",
                description="i1/i2 parameter heatmap visualization"
            ),
        ]
    
    # =========================================================================
    # DEFAULTS AND VALIDATION
    # =========================================================================
    
    def _build_defaults(self) -> Dict[str, Any]:
        """Build default values dictionary"""
        defaults = {}
        for section in self._sections:
            for field in section.fields:
                if field.default is not None:
                    defaults[field.id] = field.default
        return defaults
    
    def _build_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Build validation rules for each field"""
        rules = {}
        for section in self._sections:
            for field in section.fields:
                rule = {"type": field.type.value}
                if field.min is not None:
                    rule["min"] = field.min
                if field.max is not None:
                    rule["max"] = field.max
                if field.required:
                    rule["required"] = True
                if field.options:
                    rule["options"] = [o.value for o in field.options]
                rules[field.id] = rule
        return rules
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get complete UI schema.
        
        Returns:
            Complete schema with sections, tabs, defaults, and validation
        """
        return {
            "version": self.VERSION,
            "plugin_version": self.PLUGIN_VERSION,
            "sidebar": {
                "sections": [s.to_dict() for s in self._sections]
            },
            "tabs": [t.to_dict() for t in self._tabs],
            "defaults": self._defaults,
            "validation": self._validation,
        }
    
    def get_sidebar_schema(self) -> Dict[str, Any]:
        """Get only sidebar sections"""
        return {
            "sections": [s.to_dict() for s in self._sections]
        }
    
    def get_tabs_schema(self) -> List[Dict[str, Any]]:
        """Get only tabs"""
        return [t.to_dict() for t in self._tabs]
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for all fields"""
        return self._defaults.copy()
    
    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get validation rules"""
        return self._validation.copy()
    
    def get_section(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Get specific section by ID"""
        for section in self._sections:
            if section.id == section_id:
                return section.to_dict()
        return None
    
    def get_field(self, field_id: str) -> Optional[Dict[str, Any]]:
        """Get specific field by ID"""
        for section in self._sections:
            for field in section.fields:
                if field.id == field_id:
                    return field.to_dict()
        return None
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate settings against schema.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        for field_id, rule in self._validation.items():
            if field_id not in settings:
                if rule.get("required"):
                    errors.append(f"Missing required field: {field_id}")
                continue
            
            value = settings[field_id]
            field_type = rule.get("type")
            
            # Type validation
            if field_type in ("number", "slider"):
                if not isinstance(value, (int, float)):
                    errors.append(f"{field_id}: Expected number, got {type(value).__name__}")
                    continue
                if "min" in rule and value < rule["min"]:
                    errors.append(f"{field_id}: Value {value} below minimum {rule['min']}")
                if "max" in rule and value > rule["max"]:
                    errors.append(f"{field_id}: Value {value} above maximum {rule['max']}")
            
            elif field_type in ("select", "button_group"):
                if "options" in rule and value not in rule["options"]:
                    errors.append(f"{field_id}: Invalid option '{value}'")
            
            elif field_type == "checkbox":
                if not isinstance(value, bool):
                    errors.append(f"{field_id}: Expected boolean, got {type(value).__name__}")
        
        return len(errors) == 0, errors
    
    def to_json(self) -> str:
        """Export schema as JSON string"""
        return json.dumps(self.get_schema(), indent=2, ensure_ascii=False)
    
    def get_optimization_ranges(self) -> Dict[str, Dict[str, Any]]:
        """
        Get parameter ranges for optimization.
        
        Returns:
            Dictionary of field_id -> {min, max, step, default}
        """
        ranges = {}
        
        # Indicator parameters
        ranges["trg_atr_length"] = {
            "min": 10, "max": 200, "step": 5, "default": 45,
            "optimization_range": [20, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100, 120]
        }
        ranges["trg_multiplier"] = {
            "min": 1.0, "max": 10.0, "step": 0.5, "default": 4.0,
            "optimization_range": [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8]
        }
        
        # TP parameters
        for i in range(1, 11):
            ranges[f"tp{i}_percent"] = {
                "min": 0.1, "max": 100.0, "step": 0.5, "default": 1.0
            }
            ranges[f"tp{i}_amount"] = {
                "min": 0, "max": 100, "step": 5, "default": 25
            }
        
        # SL parameters
        ranges["sl_percent"] = {
            "min": 1.0, "max": 50.0, "step": 0.5, "default": 8.0,
            "optimization_range": [3, 4, 5, 6, 7, 8, 10, 12, 15]
        }
        
        return ranges
    
    def get_filter_presets(self) -> List[Dict[str, Any]]:
        """
        Get predefined filter presets.
        
        Returns:
            List of filter configuration presets
        """
        return [
            {
                "name": "No Filters",
                "use_supertrend": False,
                "use_rsi_filter": False,
                "use_adx_filter": False,
                "use_volume_filter": False
            },
            {
                "name": "SuperTrend Only",
                "use_supertrend": True,
                "supertrend_period": 10,
                "supertrend_multiplier": 3.0,
                "use_rsi_filter": False,
                "use_adx_filter": False,
                "use_volume_filter": False
            },
            {
                "name": "RSI Filter",
                "use_supertrend": False,
                "use_rsi_filter": True,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "use_adx_filter": False,
                "use_volume_filter": False
            },
            {
                "name": "Trend + Momentum",
                "use_supertrend": True,
                "supertrend_period": 10,
                "supertrend_multiplier": 3.0,
                "use_rsi_filter": True,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "use_adx_filter": True,
                "adx_period": 14,
                "adx_threshold": 25,
                "use_volume_filter": False
            },
            {
                "name": "Full Filters",
                "use_supertrend": True,
                "supertrend_period": 10,
                "supertrend_multiplier": 3.0,
                "use_rsi_filter": True,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "use_adx_filter": True,
                "adx_period": 14,
                "adx_threshold": 25,
                "use_volume_filter": True,
                "volume_ma_period": 20,
                "volume_threshold": 1.5
            },
        ]
    
    def get_tp_presets(self) -> List[Dict[str, Any]]:
        """
        Get predefined TP configuration presets.
        
        Returns:
            List of TP configuration presets
        """
        return [
            {
                "name": "Conservative",
                "tp_count": 4,
                "tp1_percent": 0.8, "tp1_amount": 50,
                "tp2_percent": 1.5, "tp2_amount": 30,
                "tp3_percent": 2.5, "tp3_amount": 15,
                "tp4_percent": 4.0, "tp4_amount": 5,
            },
            {
                "name": "Balanced (Default)",
                "tp_count": 4,
                "tp1_percent": 1.05, "tp1_amount": 50,
                "tp2_percent": 1.95, "tp2_amount": 30,
                "tp3_percent": 3.75, "tp3_amount": 15,
                "tp4_percent": 6.0, "tp4_amount": 5,
            },
            {
                "name": "Aggressive",
                "tp_count": 4,
                "tp1_percent": 1.5, "tp1_amount": 40,
                "tp2_percent": 3.0, "tp2_amount": 30,
                "tp3_percent": 5.0, "tp3_amount": 20,
                "tp4_percent": 8.0, "tp4_amount": 10,
            },
            {
                "name": "Scalping",
                "tp_count": 3,
                "tp1_percent": 0.3, "tp1_amount": 60,
                "tp2_percent": 0.6, "tp2_amount": 30,
                "tp3_percent": 1.0, "tp3_amount": 10,
            },
            {
                "name": "Swing",
                "tp_count": 4,
                "tp1_percent": 2.0, "tp1_amount": 40,
                "tp2_percent": 5.0, "tp2_amount": 30,
                "tp3_percent": 10.0, "tp3_amount": 20,
                "tp4_percent": 20.0, "tp4_amount": 10,
            },
        ]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global schema instance
_schema_instance: Optional[TRGUISchema] = None


def get_ui_schema() -> TRGUISchema:
    """
    Get the singleton UI schema instance.
    
    Returns:
        TRGUISchema instance
    """
    global _schema_instance
    if _schema_instance is None:
        _schema_instance = TRGUISchema()
    return _schema_instance


def get_schema_dict() -> Dict[str, Any]:
    """
    Get the complete schema as dictionary.
    Convenience function for API endpoints.
    
    Returns:
        Complete schema dictionary
    """
    return get_ui_schema().get_schema()


def get_defaults() -> Dict[str, Any]:
    """
    Get default values for all fields.
    Convenience function.
    
    Returns:
        Defaults dictionary
    """
    return get_ui_schema().get_defaults()


def validate_settings(settings: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate settings against schema.
    Convenience function.
    
    Args:
        settings: Settings to validate
        
    Returns:
        Tuple of (is_valid, errors)
    """
    return get_ui_schema().validate_settings(settings)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "FieldType",
    "SectionType",
    "TabType",
    
    # Classes
    "FieldOption",
    "UIField",
    "UISection",
    "UITab",
    "TRGUISchema",
    
    # Functions
    "get_ui_schema",
    "get_schema_dict",
    "get_defaults",
    "validate_settings",
]


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    schema = get_ui_schema()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "json":
            print(schema.to_json())
        
        elif cmd == "defaults":
            import pprint
            pprint.pprint(schema.get_defaults())
        
        elif cmd == "validate":
            # Test validation
            test_settings = {
                "trg_atr_length": 45,
                "trg_multiplier": 4.0,
                "tp_count": 4,
                "sl_percent": 8.0,
            }
            is_valid, errors = schema.validate_settings(test_settings)
            print(f"Valid: {is_valid}")
            if errors:
                print("Errors:", errors)
        
        elif cmd == "sections":
            for section in schema._sections:
                print(f"- {section.icon} {section.title} ({section.id}): {len(section.fields)} fields")
        
        elif cmd == "tabs":
            for tab in schema._tabs:
                print(f"- {tab.icon} {tab.label} ({tab.id})")
        
        else:
            print(f"Unknown command: {cmd}")
            print("Available: json, defaults, validate, sections, tabs")
    
    else:
        # Default: print summary
        print(f"TRG UI Schema v{schema.VERSION}")
        print(f"Plugin version: {schema.PLUGIN_VERSION}")
        print(f"Sections: {len(schema._sections)}")
        print(f"Tabs: {len(schema._tabs)}")
        print(f"Default fields: {len(schema._defaults)}")
        print(f"\nRun with: json, defaults, validate, sections, tabs")
