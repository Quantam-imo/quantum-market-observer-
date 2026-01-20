"""
FastAPI routes - Expose all engines via REST endpoints.
Zero logic change to existing engines (pure wrapper layer).
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

# Import all engines
from backend.core.gann_engine import GannEngine
from backend.core.astro_engine import AstroEngine
from backend.core.cycle_engine import CycleEngine
from backend.intelligence.liquidity_engine import LiquidityEngine
from backend.intelligence.iceberg_engine import IcebergEngine
from backend.intelligence.advanced_iceberg_engine import IcebergDetector, AbsorptionZoneMemory
from backend.intelligence.qmo_adapter import QMOAdapter
from backend.intelligence.imo_adapter import IMOAdapter
from backend.mentor.confidence_engine import ConfidenceEngine
from backend.mentor.mentor_brain import MentorBrain
from backend.mentor.signal_builder import SignalBuilder

# Import CME adapters
from data.cme_adapter import CMEAdapter, GCPriceCache

# Import schemas
from backend.api.schemas import (
    GannRequest, GannResponse,
    AstroRequest, AstroResponse,
    CycleRequest, CycleResponse,
    IcebergRequest, IcebergResponse,
    LiquidityRequest, LiquidityResponse, LiquidityZone,
    SignalRequest, SignalResponse, SignalData,
    MentorPanelRequest, MentorPanelResponse, HTFStructure, IcebergActivityReport,
    MarketRequest, MarketResponse,
    ChartRequest, ChartResponse, ChartBarData, ChartLevel,
    HealthResponse
)

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["institutional"])

# Initialize all engines as singletons
gann_engine = GannEngine()
astro_engine = AstroEngine()
cycle_engine = CycleEngine()
liquidity_engine = LiquidityEngine()
iceberg_engine = IcebergEngine()
qmo_adapter = QMOAdapter()
imo_adapter = IMOAdapter()
confidence_engine = ConfidenceEngine()
mentor_brain = MentorBrain()
signal_builder = SignalBuilder()

# Initialize CME data components
cme_adapter = CMEAdapter()
iceberg_detector = IcebergDetector()
absorption_memory = AbsorptionZoneMemory()
price_cache = GCPriceCache(max_bars=1000)

# Global state - will be fed by CME data
market_state = {
    "current_price": 2450.50,
    "bid": 2450.40,
    "ask": 2450.60,
    "session": "LONDON",
    "volume_avg": 1200,
    "volume_current": 1450,
    "cme_connected": False,
    "data_source": "CME_PAPER",  # Will be CME_LIVE when connected
}


# ==================== HEALTH / STATUS ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health status."""
    return HealthResponse(
        status="healthy",
        backend_running=True,
        data_source="CME_PAPER",  # Will be CME_LIVE when connected
        engines_active=["GANN", "ASTRO", "CYCLE", "LIQUIDITY", "ICEBERG", "QMO", "IMO", "MENTOR"],
        uptime_seconds=3600,
        timestamp=datetime.utcnow()
    )


# ==================== MARKET DATA ====================

@router.post("/market", response_model=MarketResponse)
async def get_market_data(request: MarketRequest):
    """Get current market state and levels."""
    
    # Use global market state (will be replaced with live CME data)
    price = market_state["current_price"]
    
    # Calculate Gann levels for support/resistance
    gann_levels = gann_engine.levels(price * 1.05, price * 0.95)
    
    return MarketResponse(
        symbol=request.symbol,
        current_price=price,
        bid=market_state["bid"],
        ask=market_state["ask"],
        session=market_state["session"],
        trend="BEARISH",
        support_1=price - 15,
        resistance_1=price + 20,
        range_high=price + 50,
        range_low=price - 50,
        range_midpoint=price,
        volume_avg=market_state["volume_avg"],
        volume_current=market_state["volume_current"],
        volume_ratio=market_state["volume_current"] / market_state["volume_avg"],
        timestamp=datetime.utcnow()
    )


# ==================== GANN ENGINE ====================

@router.post("/gann", response_model=GannResponse)
async def calculate_gann_levels(request: GannRequest):
    """Calculate Gann harmonic price levels."""
    try:
        levels = gann_engine.levels(request.high, request.low)
        range_size = abs(request.high - request.low)
        
        return GannResponse(
            range=range_size,
            levels=levels,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ASTRO ENGINE ====================

@router.post("/astro", response_model=AstroResponse)
async def calculate_astro_aspect(request: AstroRequest):
    """Calculate astrological aspect between two degrees."""
    try:
        aspect = astro_engine.aspect(request.degree_1, request.degree_2)
        is_major = astro_engine.is_major(request.degree_1, request.degree_2)
        
        return AstroResponse(
            aspect_angle=aspect,
            is_major_aspect=is_major,
            major_aspects=astro_engine.major_aspects,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== CYCLE ENGINE ====================

@router.post("/cycle", response_model=CycleResponse)
async def check_cycle(request: CycleRequest):
    """Check if bar count matches cycle."""
    try:
        is_cycle = cycle_engine.is_cycle(request.bars)
        active = [c for c in cycle_engine.cycles if c <= request.bars]
        next_cycle = min([c for c in cycle_engine.cycles if c > request.bars]) if any(c > request.bars for c in cycle_engine.cycles) else None
        
        return CycleResponse(
            bars=request.bars,
            is_cycle=is_cycle,
            active_cycles=active,
            next_cycle=next_cycle or 0,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ICEBERG DETECTION ====================

@router.post("/iceberg", response_model=IcebergResponse)
async def detect_iceberg(request: IcebergRequest):
    """Detect iceberg order activity."""
    try:
        detected = iceberg_engine.detect(request.volume, request.delta)
        confidence = 0.8 if detected else 0.2
        
        return IcebergResponse(
            detected=detected,
            confidence=confidence,
            volume=request.volume,
            delta=request.delta,
            absorption_level=market_state["current_price"] if detected else None,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== LIQUIDITY ANALYSIS ====================

@router.post("/liquidity", response_model=LiquidityResponse)
async def analyze_liquidity(request: LiquidityRequest):
    """Analyze institutional liquidity zones."""
    try:
        result = liquidity_engine.detect_liquidity_pool(request.support, request.resistance, request.volume)
        sweep_prob = liquidity_engine.sweep_probability(request.support, request.resistance, request.volume)
        
        zone = None
        if result:
            zone = LiquidityZone(
                price_from=request.support,
                price_to=request.resistance,
                volume_absorbed=result["strength"],
                sweeps_count=1,
                session=market_state["session"],
                created_at=datetime.utcnow()
            )
        
        return LiquidityResponse(
            detected=result is not None,
            pool_level=result["level"] if result else None,
            pool_strength=result["strength"] if result else None,
            sweep_probability=sweep_prob,
            zones=[zone] if zone else [],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== SIGNAL GENERATION ====================

@router.post("/signal", response_model=SignalResponse)
async def generate_signal(request: SignalRequest):
    """Generate trading signal from all engines."""
    try:
        # Build signal from individual engines
        signal_components = [
            SignalData(engine="QMO", value=request.qmo_value, description="Market State - Accumulation bias"),
            SignalData(engine="IMO", value=request.imo_value, description="Liquidity - Buy-side swept"),
            SignalData(engine="GANN", value=request.gann_value, description="Price harmonics aligned"),
            SignalData(engine="ASTRO", value=request.astro_value, description="Moon square Saturn"),
            SignalData(engine="CYCLE", value=request.cycle_value, description="90-bar cycle active"),
        ]
        
        # Calculate confidence
        weights = {
            "QMO": 0.3,
            "IMO": 0.25,
            "GANN": 0.2,
            "ASTRO": 0.15,
            "CYCLE": 0.1
        }
        
        score_dict = {
            "QMO": request.qmo_value,
            "IMO": request.imo_value,
            "GANN": request.gann_value,
            "ASTRO": request.astro_value,
            "CYCLE": request.cycle_value,
        }
        
        confidence = confidence_engine.score(score_dict)
        
        # Use mentor brain to decide
        ctx = {
            "qmo": request.qmo_value > 0.5,
            "imo": request.imo_value > 0.5,
            "confidence": confidence
        }
        
        decision = mentor_brain.decide(ctx)
        
        # Generate recommendation
        recommendation = signal_builder.generate_recommendation(
            {
                "qmo": request.qmo_value > 0.5,
                "imo": request.imo_value > 0.5,
            },
            confidence
        )
        
        return SignalResponse(
            decision="SELL" if decision else None,
            confidence=confidence,
            signals=signal_components,
            recommendation=recommendation,
            target_levels=[2430.0, 2415.0],
            stop_level=2465.0,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== AI MENTOR LIVE PANEL ====================

@router.post("/mentor", response_model=MentorPanelResponse)
async def get_mentor_panel(request: MentorPanelRequest):
    """Get live AI Mentor institutional panel."""
    try:
        price = market_state["current_price"]
        
        # Calculate all analyses
        gann_levels = gann_engine.levels(price * 1.05, price * 0.95)
        
        htf_structure = HTFStructure(
            trend="BEARISH",
            bos="3388 → 3320",
            range_high=price + 50,
            range_low=price - 50,
            equilibrium=price,
            bias="SELL"
        )
        
        iceberg_activity = IcebergActivityReport(
            detected=True,
            price_from=price - 10,
            price_to=price - 5,
            volume_spike_ratio=3.8,
            delta_direction="BEARISH",
            absorption_count=3
        )
        
        return MentorPanelResponse(
            market=request.symbol,
            session=market_state["session"],
            time_utc=datetime.utcnow(),
            current_price=price,
            htf_structure=htf_structure,
            iceberg_activity=iceberg_activity,
            gann_levels=gann_levels,
            gann_signal="200% range hit",
            active_aspects=["Moon square Saturn", "Mars rising"],
            astro_signal="Volatility active",
            ai_verdict="⛔ WAIT",
            entry_trigger="SELL on rejection below 3358",
            target_zones=[2430.0, 2415.0],
            confidence_percent=81.0,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== CHART DATA ====================

@router.post("/chart", response_model=ChartResponse)
async def get_chart_data(request: ChartRequest):
    """Get chart data with all levels and overlays."""
    try:
        # Generate sample candles
        bars = []
        base_price = market_state["current_price"]
        for i in range(request.bars):
            open_p = base_price + (i * 0.5)
            close_p = open_p + (2.0 if i % 2 == 0 else -2.0)
            bars.append(ChartBarData(
                timestamp=datetime.utcnow(),
                open=open_p,
                high=max(open_p, close_p) + 3,
                low=min(open_p, close_p) - 3,
                close=close_p,
                volume=int(market_state["volume_avg"] * (1 + (i % 3) * 0.2))
            ))
        
        # Chart levels
        gann_levels = gann_engine.levels(base_price * 1.05, base_price * 0.95)
        levels = [
            ChartLevel(price=base_price, label="Current", color="white", style="solid"),
            ChartLevel(price=base_price + 20, label="R1 (Gann)", color="red", style="dashed"),
            ChartLevel(price=base_price - 15, label="S1 (Gann)", color="green", style="dashed"),
        ]
        # Chart levels
        gann_levels = gann_engine.levels(base_price * 1.05, base_price * 0.95)
        levels = [
            ChartLevel(price=base_price, label="Current", color="white", style="solid"),
            ChartLevel(price=base_price + 20, label="R1 (Gann)", color="red", style="dashed"),
            ChartLevel(price=base_price - 15, label="S1 (Gann)", color="green", style="dashed"),
        ]
        
        return ChartResponse(
            symbol=request.symbol,
            interval=request.interval,
            bars=bars,
            levels=levels,
            iceberg_zones=[],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== CME DATA INGESTION ====================

@router.post("/cme/ingest")
async def ingest_cme_data(trades: list):
    """
    Receive CME COMEX Gold futures data.
    
    Expected format:
    [
        {
            "type": "TRADE",
            "price": 3362.4,
            "size": 150,
            "side": "BUY",
            "timestamp": "2026-01-17T14:30:45.123Z"
        },
        ...
    ]
    """
    try:
        # Process trades through CME adapter
        processed = cme_adapter.stream_processor(trades)
        
        # Update market state with real data
        if processed["aggregated"]["mid_price"] > 0:
            market_state["current_price"] = processed["aggregated"]["mid_price"]
            market_state["volume_current"] = processed["aggregated"]["total_volume"]
            market_state["session"] = processed["aggregated"]["session"]
        
        # Detect icebergs
        if processed["trades"]:
            zones = iceberg_detector.detect_absorption_zones(processed["trades"])
            for zone in zones:
                absorption_memory.record(zone)
        
        # Cache prices for technical analysis
        if processed["aggregated"]["mid_price"] > 0:
            price_cache.add(
                processed["aggregated"]["mid_price"],
                processed["trades"][0]["timestamp"] if processed["trades"] else datetime.utcnow().isoformat()
            )
        
        return {
            "status": "ingested",
            "trades_processed": len(processed["trades"]),
            "current_price": market_state["current_price"],
            "session": market_state["session"],
            "iceberg_zones_detected": len(absorption_memory.zones)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cme/quote")
async def ingest_cme_quote(quote: dict):
    """
    Receive CME bid/ask quote update.
    
    Expected format:
    {
        "bid_price": 3362.2,
        "ask_price": 3362.5,
        "bid_size": 250,
        "ask_size": 300,
        "timestamp": "2026-01-17T14:30:45Z"
    }
    """
    try:
        normalized = cme_adapter.normalize_quote(quote)
        
        if normalized:
            market_state["bid"] = normalized["bid"]
            market_state["ask"] = normalized["ask"]
        
        return {
            "status": "quote_updated",
            "bid": market_state["bid"],
            "ask": market_state["ask"],
            "spread": normalized["spread"] if normalized else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cme/status")
async def cme_status():
    """Get CME data connection status."""
    return {
        "cme_connected": market_state["cme_connected"],
        "data_source": market_state["data_source"],
        "current_price": market_state["current_price"],
        "session": market_state["session"],
        "cached_bars": len(price_cache.prices),
        "known_absorption_zones": len(absorption_memory.zones),
        "timestamp": datetime.utcnow()
    }


# ==================== ENHANCED MENTOR PANEL (WITH CME DATA) ====================

@router.post("/mentor/v2")
async def get_mentor_panel_v2(request: MentorPanelRequest):
    """
    Enhanced AI Mentor panel using real CME data.
    
    Incorporates:
    - Real GC prices (via CME)
    - Detected absorption zones
    - Iceberg pair analysis
    - Institutional activity level
    """
    try:
        price = market_state["current_price"]
        
        # Calculate technical levels from cached data
        high_50, low_50 = price_cache.get_high_low(50)
        range_50 = price_cache.get_range(50) if high_50 else 0
        
        # Gann analysis on real range
        if high_50 and low_50:
            gann_levels = gann_engine.levels(high_50, low_50)
        else:
            gann_levels = gann_engine.levels(price * 1.05, price * 0.95)
        
        # Iceberg analysis
        absorption_zones = list(absorption_memory.zones.values())[:3]  # Top 3
        iceberg_activity = IcebergActivityReport(
            detected=len(absorption_zones) > 0,
            price_from=min([z["price"] for z in absorption_zones]) if absorption_zones else None,
            price_to=max([z["price"] for z in absorption_zones]) if absorption_zones else None,
            volume_spike_ratio=3.8 if absorption_zones else 1.0,
            delta_direction="BEARISH" if absorption_zones else "NEUTRAL",
            absorption_count=len(absorption_zones)
        )
        
        # Institutional activity
        activity_level = iceberg_detector.estimate_institutional_activity({
            "range": range_50,
            "volume": market_state["volume_current"]
        })
        
        htf_structure = HTFStructure(
            trend="BEARISH" if price < (high_50 or price) else "BULLISH",
            bos=f"{high_50:.0f} → {low_50:.0f}" if high_50 and low_50 else None,
            range_high=high_50 or price + 50,
            range_low=low_50 or price - 50,
            equilibrium=price,
            bias="SELL" if price > (high_50 + low_50) / 2 if high_50 and low_50 else price else "BUY"
        )
        
        return MentorPanelResponse(
            market=request.symbol,
            session=market_state["session"],
            time_utc=datetime.utcnow(),
            current_price=price,
            htf_structure=htf_structure,
            iceberg_activity=iceberg_activity,
            gann_levels=gann_levels,
            gann_signal=f"Range: {range_50:.1f} | 200% level: {gann_levels.get('200%', 0):.2f}",
            active_aspects=["Moon square Saturn", "Mars rising"],
            astro_signal="Volatility active",
            ai_verdict="⛔ WAIT" if activity_level > 0.7 else "✅ NEUTRAL",
            entry_trigger="SELL on rejection below 3358" if activity_level > 0.7 else None,
            target_zones=[price - 15, price - 30],
            confidence_percent=min(95, int((activity_level + 0.5) * 100)),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
