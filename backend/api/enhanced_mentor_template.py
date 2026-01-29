"""
Enhanced AI Mentor Template with Complete Data Fields

This file shows the COMPLETE mentor data structure with all fields populated.
Copy this into your code to get a fully-featured mentor system.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class VolatilityRegime(str, Enum):
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    NORMAL = "NORMAL"
    LOW_VOL = "LOW_VOL"
    HIGH_VOL = "HIGH_VOL"


class TradeGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    SKIP = "SKIP"


class Recommendation(str, Enum):
    WAIT_FOR_BETTER = "WAIT_FOR_BETTER"
    ACCEPTABLE = "ACCEPTABLE"
    EXCELLENT = "EXCELLENT"


# ==================== SESSION STATISTICS ====================

class SessionStats(BaseModel):
    """Session performance and context metrics."""
    session_open: float
    session_high: float
    session_low: float
    session_close: Optional[float] = None
    session_volume: float
    avg_spread: float
    liquidity_score: float  # 0-100
    volatility_rank: str  # "LOW", "NORMAL", "HIGH", "EXTREME"
    time_remaining_seconds: int
    session_type: str  # "ASIAN", "LONDON", "NEWYORK", "OFF_HOURS"
    session_strength: str  # "WEAK", "NORMAL", "STRONG"
    typical_range: float  # Expected daily range
    actual_range: float  # So far today
    session_progression: float  # 0-100% complete


# ==================== RISK ASSESSMENT ====================

class RiskAssessment(BaseModel):
    """Real-time risk analysis and capital protection."""
    risk_level: RiskLevel
    equity_risk_percent: float  # % of account at risk
    recommended_risk_per_trade: float  # $ amount
    max_loss_before_halt: float  # Account halt level
    trades_remaining_today: int  # Trades before halt
    stop_loss_level: float
    take_profit_level: Optional[float] = None
    risk_reward_ratio: float  # 1.5, 2.0, etc
    correlation_warning: bool  # True if correlated risk
    margin_available: float
    margin_usage_percent: float
    drawdown_today: float
    drawdown_percent: float
    position_size_suggestion: float


# ==================== CONFIRMATION STATUS ====================

class ConfirmationStatus(BaseModel):
    """Multi-timeframe confirmation tracking."""
    required_confirmations: int
    current_confirmations: int
    confirmation_list: List[str]  # ["HTF Bias", "Volume Spike", "Price Action"]
    missing_confirmations: List[str]
    confirmation_progress: float  # 0-100%
    volatility_regime: VolatilityRegime
    timeframe_alignment: str  # "PERFECT", "GOOD", "WEAK"
    confluence_score: float  # 0-100 setup confluence
    ready_to_trade: bool


# ==================== NEWS & ECONOMIC EVENTS ====================

class NewsEvent(BaseModel):
    """Economic calendar events affecting market."""
    time_utc: datetime
    event_name: str  # "US CPI", "Fed Rate Decision"
    country: str  # "US", "CH", "EU", "GB", "JP"
    importance: str  # "HIGH", "MEDIUM", "LOW"
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    time_to_event_minutes: int
    potential_impact_pips: int
    sentiment: str  # "BULLISH", "NEUTRAL", "BEARISH"
    already_published: bool
    expected_volatility: str  # "LOW", "NORMAL", "HIGH"


# ==================== MARKET MICROSTRUCTURE ====================

class MicroStructure(BaseModel):
    """Order book and trade flow analysis."""
    bid_volume: float
    ask_volume: float
    bid_ask_ratio: float
    large_trades_count: int  # > 100 contracts
    large_buy_volume: int
    large_sell_volume: int
    bid_ask_imbalance: str  # "BUYER_DOMINANT", "BALANCED", "SELLER_DOMINANT"
    order_flow_bias: str  # "BUY", "SELL", "NEUTRAL"
    market_depth_score: int  # 0-100
    liquidity_provider_activity: str  # "ACTIVE", "NORMAL", "LOW"
    order_book_quality: str  # "EXCELLENT", "GOOD", "POOR"
    cumulative_delta: int  # Buy volume - Sell volume (last 100 trades)
    delta_trend: str  # "BUYING_PRESSURE", "SELLING_PRESSURE", "BALANCED"


# ==================== PERFORMANCE TRACKING ====================

class TodayPerformance(BaseModel):
    """Session-to-date performance metrics."""
    trades_today: int
    wins_today: int
    losses_today: int
    breakevens_today: int
    win_rate: float  # %
    pnl_today: float  # $
    pnl_percent: float  # % of account
    largest_win: float
    largest_loss: float
    avg_win: float
    avg_loss: float
    profit_factor: float  # Gross profit / gross loss
    equity_curve_status: str  # "RISING", "FALLING", "FLAT"
    consecutive_wins: int
    consecutive_losses: int
    max_consecutive_wins: int
    max_consecutive_losses: int
    best_trade_time: Optional[str] = None  # "09:30-10:00 (London open)"
    worst_trade_time: Optional[str] = None


# ==================== LIQUIDITY ZONES (ENHANCED) ====================

class LiquidityZoneDetail(BaseModel):
    """Institutional liquidity pool locations."""
    price_level: float
    volume_absorbed: float
    zone_strength: str  # "WEAK", "NORMAL", "STRONG", "CRITICAL"
    time_of_formation: datetime
    sweep_probability: float  # %
    institutional_activity: str  # "ACCUMULATING", "DISTRIBUTING", "NEUTRAL"
    likely_direction_after_sweep: str  # "UP", "DOWN", "UNKNOWN"
    distance_to_current: float
    interaction_count: int
    zone_type: str  # "SUPPORT", "RESISTANCE", "PIVOT"
    volume_profile: str  # "POC" (Point of Control), "VWAP", "HIGH_VOL"
    time_since_formed_minutes: int


# ==================== VOLATILITY PROFILE ====================

class VolatilityProfile(BaseModel):
    """Current and expected volatility analysis."""
    current_atr: float
    volatility_ratio: float  # Current / 20-day avg
    expected_move_today: float
    percentile_rank: int  # 0-100
    implied_volatility: Optional[float] = None
    volatility_regime: VolatilityRegime
    hourly_volatility: float
    daily_volatility: float
    vol_expansion_likely: bool
    vol_contraction_signal: bool
    vol_expansion_probability: float  # %
    vol_contraction_probability: float  # %
    volatility_forecast: str  # "RISING", "FALLING", "STABLE"


# ==================== TRADE QUALITY SCORE ====================

class TradeQualityScore(BaseModel):
    """How good is the current setup?"""
    entry_quality: float  # 0-100
    entry_reasons: List[str]
    exit_quality: float  # 0-100
    risk_reward_quality: float  # 0-100
    confirmation_quality: float  # 0-100
    timing_quality: float  # 0-100
    liquidity_quality: float  # 0-100
    overall_setup_quality: float
    setup_grade: TradeGrade
    recommendation: Recommendation
    strength_areas: List[str]  # Where setup excels
    weakness_areas: List[str]  # Where setup is weak
    alternative_setups: Optional[List[str]] = None


# ==================== SCENARIO ANALYSIS ====================

class TradeScenario(BaseModel):
    """Single scenario outcome."""
    description: str
    probability: float  # %
    target_price: float
    stop_loss_price: float
    expected_pips: float
    expected_time_frames: str  # "2-4 hours"
    confidence: float  # 0-100


class ScenarioAnalysis(BaseModel):
    """Multi-outcome scenario analysis."""
    base_case: TradeScenario
    bull_case: TradeScenario
    bear_case: TradeScenario
    black_swan_risk: str  # Potential surprises
    most_likely_scenario: str  # "BASE", "BULL", "BEAR"
    scenario_probabilities: Dict[str, float]  # {"BULL": 0.25, "BASE": 0.60, "BEAR": 0.15}


# ==================== COMPLETE MENTOR RESPONSE ====================

class EnhancedMentorPanelResponse(BaseModel):
    """Complete AI Mentor panel with all institutional data."""
    
    # === EXISTING FIELDS (From Original) ===
    market: str
    session: str
    time_utc: datetime
    current_price: float
    
    # HTF analysis
    htf_structure: Dict[str, Any]  # Existing structure
    
    # Iceberg activity
    iceberg_activity: Dict[str, Any]  # Existing iceberg data
    
    # Gann levels
    gann_levels: Dict[str, float]
    gann_signal: str
    
    # Astro conditions
    active_aspects: List[str]
    astro_signal: str
    
    # Final verdict
    ai_verdict: str
    entry_trigger: Optional[str] = None
    target_zones: List[float]
    confidence_percent: float
    
    # === NEW FIELDS (Enhanced) ===
    
    # Session context
    session_stats: Optional[SessionStats] = None
    
    # Risk management
    risk_assessment: Optional[RiskAssessment] = None
    
    # Setup completeness
    confirmation_status: Optional[ConfirmationStatus] = None
    
    # News impact
    news_events: Optional[List[NewsEvent]] = None
    upcoming_events_count: int = 0
    
    # Order flow
    microstructure: Optional[MicroStructure] = None
    
    # Performance
    today_performance: Optional[TodayPerformance] = None
    
    # Liquidity zones
    liquidity_zones: Optional[List[LiquidityZoneDetail]] = None
    
    # Volatility
    volatility_profile: Optional[VolatilityProfile] = None
    
    # Setup quality
    trade_quality_score: Optional[TradeQualityScore] = None
    
    # Multiple outcomes
    scenario_analysis: Optional[ScenarioAnalysis] = None
    
    timestamp: datetime


# ==================== EXAMPLE USAGE ====================

def get_complete_mentor_response_example() -> EnhancedMentorPanelResponse:
    """Example showing all fields populated."""
    return EnhancedMentorPanelResponse(
        # Core data
        market="XAUUSD",
        session="LONDON",
        time_utc=datetime.utcnow(),
        current_price=4819.10,
        
        # HTF
        htf_structure={
            "trend": "BEARISH",
            "bos": "3388 → 3320",
            "range_high": 4871.5,
            "range_low": 4771.5,
            "equilibrium": 4821.5,
            "bias": "SELL"
        },
        
        # Iceberg
        iceberg_activity={
            "detected": True,
            "price_from": 4826.75,
            "price_to": 4834.75,
            "volume_spike_ratio": 5.06,
            "delta_direction": "BEARISH",
            "absorption_count": 7
        },
        
        # Gann
        gann_levels={
            "50%": 241.07,
            "100%": 482.15,
            "150%": 723.22,
            "200%": 964.30,
            "250%": 1205.37,
        },
        gann_signal="200% range hit",
        
        # Astro
        active_aspects=["Moon square Saturn", "Mars rising"],
        astro_signal="Volatility active",
        
        # Verdict
        ai_verdict="⛔ WAIT",
        entry_trigger="SELL on rejection below 3358",
        target_zones=[2430.0, 2415.0],
        confidence_percent=81.0,
        
        # === NEW ENHANCED DATA ===
        
        # Session
        session_stats=SessionStats(
            session_open=4800.00,
            session_high=4835.50,
            session_low=4785.00,
            session_volume=125000.0,
            avg_spread=0.15,
            liquidity_score=82.0,
            volatility_rank="HIGH",
            time_remaining_seconds=7200,
            session_type="LONDON",
            session_strength="STRONG",
            typical_range=120.0,
            actual_range=50.50,
            session_progression=60.0
        ),
        
        # Risk
        risk_assessment=RiskAssessment(
            risk_level=RiskLevel.MEDIUM,
            equity_risk_percent=2.5,
            recommended_risk_per_trade=250.0,
            max_loss_before_halt=1000.0,
            trades_remaining_today=4,
            stop_loss_level=4860.0,
            risk_reward_ratio=1.8,
            correlation_warning=False,
            margin_available=5000.0,
            margin_usage_percent=35.0,
            drawdown_today=-150.0,
            drawdown_percent=-1.5,
            position_size_suggestion=2.0
        ),
        
        # Confirmations
        confirmation_status=ConfirmationStatus(
            required_confirmations=2,
            current_confirmations=2,
            confirmation_list=["HTF Bias ✓", "Volume Spike ✓", "Price Action ✓"],
            missing_confirmations=[],
            confirmation_progress=100.0,
            volatility_regime=VolatilityRegime.HIGH_VOL,
            timeframe_alignment="PERFECT",
            confluence_score=92.0,
            ready_to_trade=True
        ),
        
        # News
        news_events=[
            NewsEvent(
                time_utc=datetime.utcnow().replace(hour=13, minute=30),
                event_name="US CPI",
                country="US",
                importance="HIGH",
                forecast="0.2%",
                previous="0.3%",
                time_to_event_minutes=45,
                potential_impact_pips=150,
                sentiment="BEARISH",
                already_published=False,
                expected_volatility="HIGH"
            )
        ],
        upcoming_events_count=1,
        
        # Microstructure
        microstructure=MicroStructure(
            bid_volume=850.0,
            ask_volume=720.0,
            bid_ask_ratio=1.18,
            large_trades_count=12,
            large_buy_volume=1200,
            large_sell_volume=950,
            bid_ask_imbalance="BUYER_DOMINANT",
            order_flow_bias="BUY",
            market_depth_score=78,
            liquidity_provider_activity="ACTIVE",
            order_book_quality="GOOD",
            cumulative_delta=450,
            delta_trend="BUYING_PRESSURE"
        ),
        
        # Performance
        today_performance=TodayPerformance(
            trades_today=2,
            wins_today=2,
            losses_today=0,
            breakevens_today=0,
            win_rate=100.0,
            pnl_today=350.0,
            pnl_percent=3.5,
            largest_win=200.0,
            largest_loss=0.0,
            avg_win=175.0,
            avg_loss=0.0,
            profit_factor=float('inf'),
            equity_curve_status="RISING",
            consecutive_wins=2,
            consecutive_losses=0,
            max_consecutive_wins=2,
            max_consecutive_losses=1,
            best_trade_time="09:30-10:00 (London open)",
            worst_trade_time="14:00-15:00 (US pre-open)"
        ),
        
        # Liquidity zones
        liquidity_zones=[
            LiquidityZoneDetail(
                price_level=4830.0,
                volume_absorbed=8500.0,
                zone_strength="STRONG",
                time_of_formation=datetime.utcnow().replace(hour=9, minute=15),
                sweep_probability=35.0,
                institutional_activity="ACCUMULATING",
                likely_direction_after_sweep="UP",
                distance_to_current=10.9,
                interaction_count=3,
                zone_type="SUPPORT",
                volume_profile="HIGH_VOL",
                time_since_formed_minutes=285
            ),
            LiquidityZoneDetail(
                price_level=4870.0,
                volume_absorbed=6200.0,
                zone_strength="NORMAL",
                time_of_formation=datetime.utcnow().replace(hour=11, minute=45),
                sweep_probability=55.0,
                institutional_activity="DISTRIBUTING",
                likely_direction_after_sweep="DOWN",
                distance_to_current=50.9,
                interaction_count=1,
                zone_type="RESISTANCE",
                volume_profile="POC",
                time_since_formed_minutes=90
            )
        ],
        
        # Volatility
        volatility_profile=VolatilityProfile(
            current_atr=45.50,
            volatility_ratio=1.25,
            expected_move_today=120.0,
            percentile_rank=72,
            implied_volatility=18.5,
            volatility_regime=VolatilityRegime.EXPANSION,
            hourly_volatility=38.0,
            daily_volatility=42.5,
            vol_expansion_likely=True,
            vol_contraction_signal=False,
            vol_expansion_probability=72.0,
            vol_contraction_probability=28.0,
            volatility_forecast="RISING"
        ),
        
        # Quality
        trade_quality_score=TradeQualityScore(
            entry_quality=82.0,
            entry_reasons=[
                "Rejection of key level $4834",
                "Volume spike 5x average",
                "3 consecutive bearish bars",
                "HTF bias down confirmed"
            ],
            exit_quality=85.0,
            risk_reward_quality=90.0,  # 1.8:1 ratio
            confirmation_quality=100.0,  # 2/2 confirmations
            timing_quality=75.0,  # Mid-session, slight disadvantage
            liquidity_quality=88.0,  # Good spread, decent volume
            overall_setup_quality=87.0,
            setup_grade=TradeGrade.A,
            recommendation=Recommendation.EXCELLENT,
            strength_areas=[
                "Perfect confluence of HTF + iceberg",
                "Excellent risk/reward ratio",
                "High volatility for target hits",
                "Institutional participation confirmed"
            ],
            weakness_areas=[
                "Close to key news event (CPI in 45 min)",
                "Mid-session timing slightly weak"
            ],
            alternative_setups=["Wait for rejection at $4870 for better entry", "Scale in below $4825"]
        ),
        
        # Scenarios
        scenario_analysis=ScenarioAnalysis(
            base_case=TradeScenario(
                description="Rejection holds, sell moves to first target",
                probability=60.0,
                target_price=2430.0,
                stop_loss_price=4860.0,
                expected_pips=389.0,
                expected_time_frames="2-4 hours",
                confidence=85.0
            ),
            bull_case=TradeScenario(
                description="Key level breaks, squeeze up",
                probability=15.0,
                target_price=4895.0,
                stop_loss_price=4815.0,
                expected_pips=76.0,
                expected_time_frames="1-2 hours",
                confidence=40.0
            ),
            bear_case=TradeScenario(
                description="Institutional distribution continues, extend lower",
                probability=25.0,
                target_price=2415.0,
                stop_loss_price=4860.0,
                expected_pips=404.0,
                expected_time_frames="4-8 hours",
                confidence=88.0
            ),
            black_swan_risk="Unexpected CPI number could reverse setup; Fed surprise possible",
            most_likely_scenario="BASE",
            scenario_probabilities={"BULL": 0.15, "BASE": 0.60, "BEAR": 0.25}
        ),
        
        timestamp=datetime.utcnow()
    )


# ==================== IMPLEMENTATION GUIDE ====================

"""
TO IMPLEMENT IN YOUR CODE:

1. ADD TO schemas.py:
   - Copy all the classes above
   - Replace your MentorPanelResponse with EnhancedMentorPanelResponse

2. UPDATE routes.py /mentor endpoint:
   - Follow the example_usage() function pattern
   - Populate each field with real calculations
   - Keep existing mentor logic, add new data sources

3. FRONTEND USAGE:
   - You now have access to all fields
   - Display in mentor panel with sections for each category
   - Use for trade decision-making

4. IMPLEMENTATION ORDER:
   Phase 1: Risk, Session, Confirmations (High priority)
   Phase 2: Quality score, Volatility, Liquidity (Medium priority)  
   Phase 3: News, Microstructure, Scenarios (Nice to have)

5. TESTING:
   - Use example_usage() to validate structure
   - Test API returns all fields
   - Check frontend displays each section

"""
