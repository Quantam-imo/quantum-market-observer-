"""
Pydantic schemas for API request/response validation.
Defines all data structures exchanged between frontend and backend.
"""

from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


# ==================== MARKET DATA SCHEMAS ====================

class TickData(BaseModel):
    """Single tick/bar market data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    delta: Optional[int] = None  # Buy volume - Sell volume


class MarketRequest(BaseModel):
    """Request for current market analysis."""
    symbol: str = "XAUUSD"
    interval: str = "1H"  # 1m, 5m, 15m, 1H, 4H, Daily


class MarketResponse(BaseModel):
    """Current market state and levels."""
    symbol: str
    current_price: float
    bid: float
    ask: float
    session: str  # "ASIA", "LONDON", "NEWYORK"
    trend: str  # "BULLISH", "BEARISH", "NEUTRAL"
    
    # Price levels
    support_1: float
    resistance_1: float
    range_high: float
    range_low: float
    range_midpoint: float
    
    # Volume
    volume_avg: float
    volume_current: float
    volume_ratio: float  # current / avg
    
    # Data
    timestamp: datetime


# ==================== GANN ENGINE SCHEMAS ====================

class GannRequest(BaseModel):
    """Request Gann level calculation."""
    high: float
    low: float


class GannResponse(BaseModel):
    """Gann harmonic price levels."""
    range: float
    levels: Dict[str, float]  # {"50%": 100.5, "100%": 201.0, ...}
    timestamp: datetime


# ==================== ASTRO ENGINE SCHEMAS ====================

class AstroRequest(BaseModel):
    """Request astro aspect analysis."""
    degree_1: float  # Planet/angle 1 degrees
    degree_2: float  # Planet/angle 2 degrees


class AstroResponse(BaseModel):
    """Astrological aspect strength."""
    aspect_angle: float
    is_major_aspect: bool
    major_aspects: List[float]
    timestamp: datetime


# ==================== CYCLE ENGINE SCHEMAS ====================

class CycleRequest(BaseModel):
    """Request cycle detection."""
    bars: int


class CycleResponse(BaseModel):
    """Cycle alignment status."""
    bars: int
    is_cycle: bool
    active_cycles: List[int]
    next_cycle: int
    timestamp: datetime


# ==================== LIQUIDITY / ICEBERG SCHEMAS ====================

class IcebergRequest(BaseModel):
    """Request iceberg detection."""
    volume: float
    delta: int  # Volume delta (buy - sell)


class IcebergResponse(BaseModel):
    """Iceberg detection result."""
    detected: bool
    confidence: float  # 0.0 - 1.0
    volume: float
    delta: int
    absorption_level: Optional[float] = None
    timestamp: datetime


class LiquidityZone(BaseModel):
    """Identified institutional liquidity zone."""
    price_from: float
    price_to: float
    volume_absorbed: float
    sweeps_count: int
    session: str
    created_at: datetime


class LiquidityRequest(BaseModel):
    """Request liquidity zone analysis."""
    support: float
    resistance: float
    volume: float


class LiquidityResponse(BaseModel):
    """Liquidity analysis result."""
    detected: bool
    pool_level: Optional[float] = None
    pool_strength: Optional[float] = None
    sweep_probability: float
    zones: List[LiquidityZone]
    timestamp: datetime


# ==================== SIGNAL SCHEMAS ====================

class SignalData(BaseModel):
    """Individual signal component."""
    engine: str  # "QMO", "IMO", "GANN", "ASTRO", "CYCLE"
    value: float  # 0.0 - 1.0
    description: str


class SignalRequest(BaseModel):
    """Request signal generation."""
    market_data: TickData
    qmo_value: float
    imo_value: float
    gann_value: float
    astro_value: float
    cycle_value: float


class SignalResponse(BaseModel):
    """Generated trading signal."""
    decision: Optional[str]  # "BUY", "SELL", None (WAIT)
    confidence: float  # 0.0 - 1.0
    signals: List[SignalData]
    recommendation: str  # "STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"
    target_levels: List[float]
    stop_level: Optional[float] = None
    timestamp: datetime


# ==================== MENTOR PANEL SCHEMAS ====================

class HTFStructure(BaseModel):
    """Higher time frame structure analysis."""
    trend: str  # "BULLISH", "BEARISH", "NEUTRAL"
    bos: Optional[str] = None  # Break of structure "from → to"
    range_high: float
    range_low: float
    equilibrium: float
    bias: str  # "BUY", "SELL", "NEUTRAL"


class IcebergActivityReport(BaseModel):
    """Live iceberg activity summary."""
    detected: bool
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    volume_spike_ratio: Optional[float] = None
    delta_direction: Optional[str] = None  # "BULLISH", "BEARISH"
    absorption_count: int


class MentorPanelRequest(BaseModel):
    """Request live mentor panel update."""
    symbol: str = "XAUUSD"
    refresh: bool = True


class MentorPanelResponse(BaseModel):
    """Live AI Mentor panel for institutional traders."""
    market: str
    session: str
    time_utc: datetime
    current_price: float
    
    # HTF analysis
    htf_structure: HTFStructure
    
    # Iceberg activity
    iceberg_activity: IcebergActivityReport
    
    # Gann levels
    gann_levels: Dict[str, float]
    gann_signal: str
    
    # Astro conditions
    active_aspects: List[str]
    astro_signal: str
    
    # Final verdict
    ai_verdict: str  # "⛔ WAIT", "✅ BUY", "❌ SELL"
    entry_trigger: Optional[str] = None
    target_zones: List[float]
    confidence_percent: float  # 0-100
    
    timestamp: datetime


# ==================== CHART SCHEMAS ====================

class ChartBarData(BaseModel):
    """Single bar for chart rendering."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class ChartLevel(BaseModel):
    """Chart horizontal level (support/resistance/Gann)."""
    price: float
    label: str
    color: str
    style: str  # "solid", "dashed"


class IcebergZoneVisual(BaseModel):
    """Rectangle overlay for iceberg absorption zone."""
    price_top: float
    price_bottom: float
    volume_indicator: float
    color: str  # "rgba(...)"


class ChartRequest(BaseModel):
    """Request chart data."""
    symbol: str = "XAUUSD"
    interval: str = "5m"
    bars: int = 100
    include_levels: bool = True
    include_icebergs: bool = True


class ChartResponse(BaseModel):
    """Complete chart package for frontend."""
    symbol: str
    interval: str
    bars: List[ChartBarData]
    levels: List[ChartLevel]
    iceberg_zones: List[IcebergZoneVisual]
    vwap: Optional[List[float]] = None
    session_boxes: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime


# ==================== HEALTH / STATUS SCHEMAS ====================

class HealthResponse(BaseModel):
    """System health status."""
    status: str  # "healthy", "degraded", "offline"
    backend_running: bool
    data_source: str  # "CME_LIVE", "PAPER", "BACKTEST"
    engines_active: List[str]
    uptime_seconds: int
    timestamp: datetime
