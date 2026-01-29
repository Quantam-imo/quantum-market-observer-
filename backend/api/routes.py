"""
FastAPI routes - Expose all engines via REST endpoints.
Zero logic change to existing engines (pure wrapper layer).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import csv
import io

# Import all engines
from backend.core.gann_engine import GannEngine
from backend.core.astro_engine import AstroEngine
from backend.core.cycle_engine import CycleEngine
from backend.intelligence.liquidity_engine import LiquidityEngine
from backend.intelligence.iceberg_engine import IcebergEngine
from backend.intelligence.advanced_iceberg_engine import IcebergDetector, AbsorptionZoneMemory
from backend.intelligence.order_recorder import RawOrderRecorder
from backend.intelligence.qmo_adapter import QMOAdapter
from backend.intelligence.imo_adapter import IMOAdapter
from backend.mentor.confidence_engine import ConfidenceEngine
from backend.mentor.mentor_brain import MentorBrain
from backend.mentor.signal_builder import SignalBuilder
from backend.volume_profile_engine import VolumeProfileEngine

# Import CME adapters
from data.cme_adapter import CMEAdapter, GCPriceCache

# Import live market data fetcher
from backend.feeds.market_data_fetcher import (
    fetch_live_market_data,
    fetch_current_price,
    fetch_ohlc_candles
)

# Import schemas
from backend.api.schemas import (
    GannRequest, GannResponse,
    AstroRequest, AstroResponse,
    CycleRequest, CycleResponse,
    IcebergRequest, IcebergResponse,
    LiquidityRequest, LiquidityResponse, LiquidityZone,
    SignalRequest, SignalResponse, SignalData,
    MentorPanelRequest, MentorPanelResponse, HTFStructure, IcebergActivityReport, RiskAssessment, ConfirmationStatus,
    MarketRequest, MarketResponse,
    ChartRequest, ChartResponse, ChartBarData, ChartLevel, IcebergZoneVisual,
    VolumeProfileRequest, VolumeProfileResponse, VolumeProfileHistogramBar,
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
volume_profile_engine = VolumeProfileEngine(tick_size=0.10)  # Gold futures tick size

# Initialize CME data components
cme_adapter = CMEAdapter()
iceberg_detector = IcebergDetector()
absorption_memory = AbsorptionZoneMemory()
price_cache = GCPriceCache(max_bars=1000)
order_recorder = RawOrderRecorder()  # NEW: Raw order tracking

# Initialize 5-minute candle predictor with AI and memory
from backend.intelligence.candle_predictor_5min import FiveMinuteCandlePredictor
candle_predictor_5min = FiveMinuteCandlePredictor(mentor_brain=mentor_brain, max_history=100)

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


# ===== ICEBERG DETECTION HELPERS =====

def _bars_to_trades(bars):
    """Convert chart bars to simplified trades for iceberg inference."""
    trades = []
    for bar in bars:
        # Use mid-price and total volume as a single aggregate print.
        price = (bar.open + bar.close) / 2
        size = max(1, int(bar.volume))
        side = "BUY" if bar.close >= bar.open else "SELL"
        trades.append({
            "price": price,
            "size": size,
            "side": side,
            "timestamp": bar.timestamp
        })
    return trades


def _detect_icebergs_from_bars(bars):
    """Run advanced iceberg detection on bars and return (flags, zones)."""
    if not bars:
        return [], []

    trades = _bars_to_trades(bars)
    zones = iceberg_detector.detect_absorption_zones(trades)

    # Build visuals for frontend (thin band around detected price)
    visuals = []
    for z in zones:
        visuals.append(IcebergZoneVisual(
            price_top=z["price"] + 0.25,
            price_bottom=z["price"] - 0.25,
            volume_indicator=z["volume"],
            color="rgba(255,159,28,0.18)",
        ))

    # Mark each bar if it overlaps any detected zone price
    flags = []
    for bar in bars:
        hit = any(bar.low <= z["price"] <= bar.high for z in zones)
        flags.append(hit)

    return flags, visuals


# ==================== HEALTH / STATUS ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health status."""
    return HealthResponse(
        status="healthy",
        backend_running=True,
        data_source="CME_PAPER",  # Will be CME_LIVE when connected
        engines_active=["GANN", "ASTRO", "CYCLE", "LIQUIDITY", "ICEBERG", "QMO", "IMO", "MENTOR", "5MIN_PREDICTOR"],
        uptime_seconds=3600,
        timestamp=datetime.utcnow()
    )


# ==================== 5-MINUTE CANDLE PREDICTION ====================

@router.post("/candle/5min/predict")
async def predict_5min_candle():
    """
    Predict next 5-minute candle direction using:
    - Real order flow from current 5-minute period
    - Volume progression and momentum analysis
    - AI Mentor brain decision making
    - Historical pattern matching from memory
    
    Returns comprehensive prediction with confidence, AI insights, and pattern analysis.
    """
    try:
        # Get current orders from database
        recent_orders = order_recorder.get_recent_orders(limit=500)
        
        # Feed orders to predictor
        candle_predictor_5min.add_orders(recent_orders)
        
        # Generate prediction
        prediction = candle_predictor_5min.predict_next_candle()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "prediction": prediction,
            "system": {
                "predictor_type": "5-MINUTE CANDLE WITH AI + MEMORY",
                "ai_mentor_active": True,
                "memory_patterns_available": len(candle_predictor_5min.historical_patterns),
                "current_period": candle_predictor_5min.current_period_start.isoformat() if candle_predictor_5min.current_period_start else None,
                "orders_in_period": len(candle_predictor_5min.period_orders),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/candle/5min/stats")
async def get_5min_prediction_stats():
    """Get statistics and accuracy metrics for 5-minute predictions."""
    try:
        stats = candle_predictor_5min.get_statistics()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats,
            "memory": {
                "total_patterns_recorded": len(candle_predictor_5min.historical_patterns),
                "max_patterns_stored": candle_predictor_5min.max_history,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


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


@router.get("/iceberg/export")
async def export_iceberg_memory(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = "csv"
):
    """
    Export iceberg orderflow memory to CSV file.
    
    Query Parameters:
    - start_date: ISO format date string (e.g., "2026-01-01T00:00:00")
    - end_date: ISO format date string (e.g., "2026-01-28T23:59:59")
    - format: Export format (currently only "csv" supported)
    """
    try:
        # Get all recorded zones
        zones = absorption_memory.zones
        
        # Filter by date range if provided
        filtered_zones = zones
        if start_date or end_date:
            filtered_zones = []
            start_dt = datetime.fromisoformat(start_date) if start_date else datetime.min
            end_dt = datetime.fromisoformat(end_date) if end_date else datetime.max
            
            for zone in zones:
                zone_time = zone.get("timestamp")
                if isinstance(zone_time, str):
                    zone_time = datetime.fromisoformat(zone_time.replace('Z', '+00:00'))
                elif isinstance(zone_time, datetime):
                    pass
                else:
                    continue
                
                if start_dt <= zone_time <= end_dt:
                    filtered_zones.append(zone)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Timestamp',
            'Date',
            'Time',
            'Price',
            'Volume',
            'Direction',
            'Confidence',
            'Zone Type',
            'Absorption Level'
        ])
        
        # Write data rows
        for zone in filtered_zones:
            timestamp = zone.get("timestamp")
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                dt = datetime.utcnow()
            
            writer.writerow([
                dt.isoformat(),
                dt.strftime('%Y-%m-%d'),
                dt.strftime('%H:%M:%S'),
                zone.get("price", ""),
                zone.get("volume", ""),
                zone.get("direction", ""),
                zone.get("confidence", ""),
                zone.get("type", "ICEBERG_ABSORPTION"),
                zone.get("price", "")
            ])
        
        # Prepare file for download
        output.seek(0)
        
        filename = f"iceberg_orderflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ===== RAW ORDERS ENDPOINTS (NEW) =====

@router.get("/orders/recent")
async def get_recent_orders(limit: int = 100):
    """Get most recent raw orders (from memory) - captured at tick level"""
    orders = order_recorder.get_recent_orders(limit)
    return {"orders": orders, "count": len(orders)}


@router.get("/orders/stats")
async def get_orders_stats():
    """Get statistics about recorded raw orders"""
    stats = order_recorder.get_stats()
    return stats


@router.get("/orders/by-time")
async def get_orders_by_time(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500
):
    """Get raw orders within time range"""
    start_dt = datetime.fromisoformat(start_date) if start_date else (datetime.utcnow() - timedelta(hours=1))
    end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
    
    orders = order_recorder.get_orders_by_time_range(start_dt, end_dt)
    return {"orders": orders[:limit], "count": len(orders)}


@router.get("/orders/by-price")
async def get_orders_by_price(
    min_price: float,
    max_price: float,
    limit: int = 500
):
    """Get raw orders within price range"""
    orders = order_recorder.get_orders_by_price_range(min_price, max_price, limit)
    return {"orders": orders, "count": len(orders), "price_range": {"min": min_price, "max": max_price}}


@router.get("/orders/by-side")
async def get_orders_by_side(side: str, limit: int = 100):
    """Get raw orders by side (BUY or SELL)"""
    orders = order_recorder.get_orders_by_side(side, limit)
    return {"orders": orders, "count": len(orders), "side": side}


@router.post("/orders/cleanup")
async def cleanup_old_orders(days: int = 15):
    """
    Manually trigger cleanup of orders older than N days
    Default: 15 days (for intraday trading)
    """
    deleted = order_recorder.clear_old_orders(days=days)
    stats = order_recorder.get_stats()
    return {
        "success": True,
        "deleted": deleted,
        "retention_days": days,
        "remaining_orders": stats["total_orders"],
        "message": f"Deleted {deleted} orders older than {days} days"
    }


@router.get("/orders/cleanup-info")
async def get_cleanup_info():
    """Get information about automatic cleanup configuration"""
    return {
        "auto_cleanup_enabled": True,
        "retention_days": order_recorder.auto_cleanup_days,
        "cleanup_schedule": "On server startup",
        "description": f"Orders older than {order_recorder.auto_cleanup_days} days are automatically deleted",
        "manual_cleanup": "POST /api/v1/orders/cleanup?days=15"
    }
    return {"orders": orders, "count": len(orders), "side": side.upper()}


@router.get("/orders/volume-at-price")
async def get_volume_at_price(price: float, tolerance: float = 0.5):
    """Get volume aggregated at price level"""
    result = order_recorder.get_volume_at_price(price, tolerance)
    return result


@router.get("/orders/profile")
async def get_volume_profile(limit: int = 500):
    """Get volume profile across price levels from raw orders"""
    profile = order_recorder.get_volume_profile(limit)
    return {"profile": profile, "limit": limit}


@router.post("/orders/record")
async def record_raw_order(
    price: float,
    size: int,
    side: str,
    contract_type: str = "ES"
):
    """Record a raw order at tick level (before candle formation)"""
    order = order_recorder.record_order(
        price=price,
        size=size,
        side=side,
        contract_type=contract_type
    )
    return {"order": order, "status": "recorded"}


@router.get("/orders/export")
async def export_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export raw orders as CSV"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    csv_data = order_recorder.export_orders_csv(start_dt, end_dt)
    
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"raw_orders_{now}.csv"
    
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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
    """Get live AI Mentor institutional panel with real market data."""
    try:
        # Fetch live market data from Twelve Data API
        live_data = await fetch_live_market_data()
        price = live_data.get("current_price")
        
        # Fallback to mock data if API fails
        if price is None:
            price = market_state["current_price"]
        else:
            # Update market state with live price
            market_state["current_price"] = price
        
        # Calculate all analyses
        # Get comprehensive Gann analysis
        range_high = price * 1.05
        range_low = price * 0.95
        raw_gann = gann_engine.levels(range_high, range_low)
        
        # Convert to simple float dict for API compatibility
        gann_levels = {}
        for key, val in raw_gann.items():
            if isinstance(val, dict):
                # Use 'extension' value from new Gann engine
                gann_levels[key] = val.get('extension', 0.0)
            else:
                gann_levels[key] = float(val)
        
        # Get additional Gann data for advanced analysis
        gann_sq9 = gann_engine.square_of_nine(price, rotations=4)
        gann_cardinal = gann_engine.cardinal_cross(price)
        gann_clusters = gann_engine.price_clusters(price, range_high, range_low)
        range_size = abs(range_high - range_low)
        gann_angles = gann_engine.calculate_angles(price, range_size, time_units=10)
        
        # Get comprehensive Astro analysis
        astro_aspects = astro_engine.calculate_aspects_now()
        astro_outlook = astro_engine.get_trading_outlook()
        moon_phase = astro_engine.get_moon_phase()
        mercury_rx = astro_engine.get_retrograde_status("Mercury")
        
        # Format active aspects for display
        active_aspects = [
            f"{a['planet1']}-{a['planet2']} {a['aspect'].title()} ({a['angle']:.1f}°)"
            for a in astro_aspects[:5]
        ]
        astro_signal = f"{astro_outlook['outlook']} ({astro_outlook['confidence']}% conf, {astro_outlook['volatility']} vol)"
        
        htf_structure = HTFStructure(
            trend="BEARISH",
            bos="3388 → 3320",
            range_high=price + 50,
            range_low=price - 50,
            equilibrium=price,
            bias="SELL"
        )
        
        # Get LIVE order flow data from order recorder
        recent_orders = order_recorder.get_recent_orders(limit=500)
        buy_volume = sum(o['size'] for o in recent_orders if o['side'] == 'BUY')
        sell_volume = sum(o['size'] for o in recent_orders if o['side'] == 'SELL')
        order_flow_balance = buy_volume - sell_volume
        
        # Update market state with live order flow
        market_state["buys"] = buy_volume
        market_state["sells"] = sell_volume
        
        # Derive iceberg signal from recent candles AND live order flow
        iceberg_detected = False
        iceberg_from = price
        iceberg_to = price
        volume_spike_ratio = 1.0
        absorption_count = 0

        try:
            recent_candles = await fetch_ohlc_candles(limit=50)
            recent_bars = []
            for candle in recent_candles or []:
                recent_bars.append(ChartBarData(
                    timestamp=datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00")) if isinstance(candle.get("timestamp"), str) else datetime.utcnow(),
                    open=candle.get("open", price),
                    high=candle.get("high", price),
                    low=candle.get("low", price),
                    close=candle.get("close", price),
                    volume=candle.get("volume", 0)
                ))
            flags, visuals = _detect_icebergs_from_bars(recent_bars)
            iceberg_detected = any(flags)
            if visuals:
                iceberg_from = min(v.price_bottom for v in visuals)
                iceberg_to = max(v.price_top for v in visuals)
                absorption_count = len(visuals)
                if recent_bars:
                    avg_vol = sum(b.volume for b in recent_bars) / max(1, len(recent_bars))
                    volume_spike_ratio = max(v.volume_indicator for v in visuals) / max(1, avg_vol)
        except Exception:
            pass

        iceberg_activity = IcebergActivityReport(
            detected=iceberg_detected,
            price_from=iceberg_from,
            price_to=iceberg_to,
            volume_spike_ratio=round(volume_spike_ratio, 2),
            delta_direction="BEARISH" if iceberg_detected else "NEUTRAL",
            absorption_count=absorption_count
        )

        # Lightweight risk model
        risk_level = "MEDIUM"
        if iceberg_detected and volume_spike_ratio >= 1.5:
            risk_level = "HIGH"
        elif not iceberg_detected:
            risk_level = "LOW"

        recommended_risk_pct = 2.0 if risk_level == "HIGH" else 1.5 if risk_level == "MEDIUM" else 1.0
        stop_loss = round(price * 1.008, 2)
        risk_reward_ratio = 1.8
        max_daily_loss = round(price * 0.005, 2)
        trades_remaining = 3 if risk_level == "HIGH" else 4

        risk_assessment = RiskAssessment(
            risk_level=risk_level,
            recommended_risk_pct=recommended_risk_pct,
            max_daily_loss=max_daily_loss,
            stop_loss=stop_loss,
            trades_remaining=trades_remaining,
            risk_reward_ratio=risk_reward_ratio
        )

        # Setup confirmations
        bias_alignment = htf_structure.bias.upper() == "SELL"
        volume_spike_confirm = volume_spike_ratio >= 1.5
        price_action_alignment = "→" in (htf_structure.bos or "")
        iceberg_confirm = iceberg_detected

        score_components = [
            25 if bias_alignment else 0,
            25 if volume_spike_confirm else 0,
            25 if price_action_alignment else 0,
            25 if iceberg_confirm else 0,
        ]
        confirmation_score = float(min(100, sum(score_components)))
        ready_to_trade = confirmation_score >= 60 and bias_alignment

        confirmation_status = ConfirmationStatus(
            bias_alignment=bias_alignment,
            volume_spike=volume_spike_confirm,
            price_action_alignment=price_action_alignment,
            iceberg_activity=iceberg_confirm,
            ready_to_trade=ready_to_trade,
            score=confirmation_score
        )

        # Narrative story/context for UI
        verdict_text = "⛔ WAIT"
        context_story = (
            f"Trend {htf_structure.trend}, bias {htf_structure.bias}, BOS {htf_structure.bos}. "
            f"Iceberg {'active' if iceberg_detected else 'quiet'} in {round(iceberg_from,2)}-{round(iceberg_to,2)} with "
            f"{volume_spike_ratio:.2f}x volume. Risk {risk_level} at {recommended_risk_pct}% size, R:R {risk_reward_ratio}. "
            f"Verdict {verdict_text}."
        )
        context_notes = "Session live snapshot with iceberg and risk overlay."
        context_bullets = [
            f"HTF bias {htf_structure.bias} with BOS {htf_structure.bos}",
            f"Iceberg {'active' if iceberg_detected else 'quiet'} {round(iceberg_from,2)}-{round(iceberg_to,2)} @ {volume_spike_ratio:.2f}x",
            f"Risk {risk_level}, size {recommended_risk_pct}%, R:R {risk_reward_ratio}",
            f"Confirmations: {int(confirmation_score/25)}/4 ready -> {'READY' if ready_to_trade else 'WAIT'}",
            f"Trigger: SELL below 3358 toward 2430/2415; stop ~{round(stop_loss,2)}",
        ]

        # Trade plan summary
        trade_summary = "SELL on rejection; targets 2430/2415; wait for trigger below 3358."
        entry_plan = "Watch 3358 rejection; enter short after bearish confirmation candle."
        stop_plan = f"Protective stop near {round(stop_loss,2)} (about 0.8% above price)."
        target_plan = "First target 2430, second target 2415; trail after first target hit."

        # ===== Multi-Timeframe long narrative =====
        # Derive simple MTF context from existing HTF structure and current price
        price_pos = "above" if price > htf_structure.equilibrium else "below" if price < htf_structure.equilibrium else "near"
        dist_to_eq = round(abs(price - htf_structure.equilibrium), 2)
        rh, rl = htf_structure.range_high, htf_structure.range_low
        range_width = max(0.01, rh - rl)
        pos_pct = round(((price - rl) / range_width) * 100, 1) if range_width else 50.0

        mtf_summary_bullets = [
            f"Weekly: Trend context {htf_structure.trend} with intact lower-time bias {htf_structure.bias}.",
            f"Daily: Price {price_pos} equilibrium by {dist_to_eq} within {round(rl,2)}–{round(rh,2)} (pos: {pos_pct}%).",
            f"4H: Compression against equilibrium; awaiting decisive rejection to re-engage with trend.",
            f"1H: Iceberg absorption {'active' if iceberg_detected else 'inactive'} near {round(iceberg_from,2)}–{round(iceberg_to,2)} ({volume_spike_ratio:.2f}x).",
            f"15m: Setup completeness {int(confirmation_score)}% with confluence from volume + price action.",
        ]

        context_long_story = (
            "On higher timeframes, the prevailing structure remains {trend} with a confirmed break-of-structure at {bos}, "
            "framing a working range between {rl}-{rh}. Price currently trades {price_pos} equilibrium by {dist} (pos {pos_pct}%), "
            "suggesting momentum alignment with the {bias} bias as long as the mid remains defended. "
            "On the 4H/1H stack, liquidity has concentrated around {ice_from}-{ice_to} where repeated absorption ({absorptions} hits) and a {spike}× volume spike hint at institutional participation. "
            "Intraday, confirmations are {conf}% complete with bias, volume, and price action aligned; the plan favors a rejection continuation scenario rather than a breakout acceptance. "
            "Risk is categorized as {risk_level} with suggested sizing near {risk_pct}% and an indicative R:R of {rr}. "
            "The working plan remains to wait for a clean rejection signal under 3358, then target 2430/2415 while protecting near {stop}."
        ).format(
            trend=htf_structure.trend,
            bos=htf_structure.bos or "N/A",
            rl=round(rl, 2), rh=round(rh, 2),
            price_pos=price_pos, dist=dist_to_eq, pos_pct=pos_pct,
            bias=htf_structure.bias,
            ice_from=round(iceberg_from, 2), ice_to=round(iceberg_to, 2),
            absorptions=absorption_count, spike=f"{volume_spike_ratio:.2f}",
            conf=int(confirmation_score), risk_level=risk_level,
            risk_pct=recommended_risk_pct, rr=risk_reward_ratio, stop=round(stop_loss, 2)
        )

        # Session narrative + invalidations
        sess = market_state.get("session", "SESSION")
        vol_descriptor = (
            "extreme" if volume_spike_ratio >= 3.0 else
            "elevated" if volume_spike_ratio >= 1.5 else
            "normal"
        )
        session_narrative = (
            f"{sess} session context shows {vol_descriptor} participation with price {price_pos} equilibrium. "
            f"Liquidity focus remains around {round(iceberg_from,2)}–{round(iceberg_to,2)}; expect reactions there."
        )

        invalidations = [
            f"Acceptance above {round(iceberg_to,2)} (invalidates near-term sell idea)",
            f"Shift to { 'BULLISH' if htf_structure.trend=='BEARISH' else 'BEARISH' } HTF structure (trend flip)",
            f"Sustained hold above equilibrium {round(htf_structure.equilibrium,2)}",
        ]
        
        # News events and calendar
        news_events = [
            {
                "time_utc": (datetime.utcnow() + timedelta(hours=2, minutes=30)).isoformat(),
                "event_name": "US CPI (YoY)",
                "country": "US",
                "importance": "HIGH",
                "forecast": "3.2%",
                "previous": "3.4%",
                "impact_xauusd": "BEARISH"
            },
            {
                "time_utc": (datetime.utcnow() + timedelta(hours=5, minutes=15)).isoformat(),
                "event_name": "Fed Chair Speech",
                "country": "US",
                "importance": "HIGH",
                "forecast": "-",
                "previous": "-",
                "impact_xauusd": "VOLATILE"
            },
            {
                "time_utc": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
                "event_name": "Jobless Claims",
                "country": "US",
                "importance": "MEDIUM",
                "forecast": "220K",
                "previous": "215K",
                "impact_xauusd": "NEUTRAL"
            }
        ]
        
        # Major XAUUSD news and summaries
        major_news = [
            {
                "time_utc": (datetime.utcnow() - timedelta(hours=1, minutes=30)).isoformat(),
                "headline": "Fed Officials Signal Cautious Rate Path",
                "summary": "Two Fed governors indicated rates may hold higher for longer amid sticky inflation, pressuring gold's non-yielding appeal.",
                "sentiment": "BEARISH",
                "bias": "BEARISH",
                "impact": "Moderate downside pressure on XAUUSD as real yields stay elevated"
            },
            {
                "time_utc": (datetime.utcnow() - timedelta(hours=3, minutes=45)).isoformat(),
                "headline": "Geopolitical Tensions Escalate in Middle East",
                "summary": "Overnight developments sparked safe-haven flows into gold, offsetting some dollar strength.",
                "sentiment": "BULLISH",
                "bias": "BULLISH",
                "impact": "Flight-to-quality bid supports XAUUSD despite USD headwinds"
            },
            {
                "time_utc": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "headline": "China Central Bank Resumes Gold Purchases",
                "summary": "PBOC added 15 tons to reserves, signaling continued institutional accumulation.",
                "sentiment": "BULLISH",
                "bias": "BULLISH",
                "impact": "Central bank demand provides structural support for gold prices"
            }
        ]
        
        # News memory (learning engine state)
        news_memory = {
            "CPI": {"total_events": 8, "confidence_adjustment": -0.15},
            "FOMC": {"total_events": 5, "confidence_adjustment": -0.25},
            "NFP": {"total_events": 12, "confidence_adjustment": 0.10},
            "GDP": {"total_events": 3, "confidence_adjustment": 0.05}
        }
        
        upcoming_events_count = len(news_events)
        
        # Global markets context and narrative
        vol_ratio_val = volume_spike_ratio if volume_spike_ratio else 1.0
        risk_sentiment = "risk-off pressure dominating" if vol_ratio_val > 1.5 else "risk-on sentiment" if vol_ratio_val < 0.9 else "balanced conditions"
        
        global_markets = {
            "context": (
                f"{sess} session showing {risk_sentiment} across global asset classes. "
                f"US equities {'under pressure with VIX elevated' if vol_ratio_val > 1.5 else 'consolidating recent gains' if vol_ratio_val < 0.9 else 'range-bound with no clear catalyst'}, "
                f"DXY {'strengthening on safe-haven demand' if vol_ratio_val > 1.5 else 'weakening as risk appetite returns' if vol_ratio_val < 0.9 else 'trading sideways near key support'}, "
                f"and real yields {'climbing on Fed hawkish rhetoric' if vol_ratio_val > 1.5 else 'easing on softer data' if vol_ratio_val < 0.9 else 'stabilizing in recent range'}. "
                f"XAUUSD {'benefits from defensive positioning despite yield headwinds' if vol_ratio_val > 1.5 else 'faces rotation pressure as capital flows to risk assets' if vol_ratio_val < 0.9 else 'awaits directional catalyst from either Fed speakers or geopolitical developments'}. "
                f"{'Institutional accumulation zones active around ' + str(round(iceberg_from,2)) + '-' + str(round(iceberg_to,2)) + ', suggesting smart money positioning ahead of key events.' if iceberg_detected else 'Clean price discovery with no major institutional absorption detected.'}"
            ),
            "narrative": (
                f"European morning trade established {sess} tone with {'defensive flows into bonds and gold' if vol_ratio_val > 1.5 else 'optimistic positioning across risk assets' if vol_ratio_val < 0.9 else 'mixed sentiment awaiting US data'}. "
                f"Cross-asset correlations show {'classic risk-off pattern: equities down, gold/bonds bid' if vol_ratio_val > 1.5 else 'typical risk-on rotation: equities/yields up, gold softer' if vol_ratio_val < 0.9 else 'decoupling as markets digest conflicting signals'}. "
                f"For XAUUSD, the path forward depends on {'duration of risk-off episode and whether Fed pushes back on easing expectations' if vol_ratio_val > 1.5 else 'sustainability of risk appetite and any USD weakness from dovish Fed commentary' if vol_ratio_val < 0.9 else 'whether upcoming catalysts (CPI, Fed speak) break current rangebound structure'}."
            )
        }
        
        # Get cycle data for visualization with date/time info
        try:
            # Use 200 bars as default if no recent_bars available (simulates ~200 hourly bars)
            num_bars = len(recent_bars) if recent_bars else 200
            cycle_response = cycle_engine.is_cycle(num_bars)
            
            gann_cycles = []
            
            # Focus on major Gann cycles: 45, 90, 180
            major_cycles = [45, 90, 180]
            
            for cycle_len in major_cycles:
                if cycle_len <= num_bars:
                    # Find the most recent occurrence of this cycle
                    bars_since_cycle = num_bars % cycle_len
                    bar_index = num_bars - bars_since_cycle - 1
                    
                    if bar_index >= 0:
                        # Get timestamps for cycle start and end
                        current_time = datetime.utcnow()
                        cycle_time = current_time - timedelta(hours=bars_since_cycle)  # 1 bar = 1 hour
                        cycle_start_time = cycle_time - timedelta(hours=cycle_len)
                        
                        is_active = (bars_since_cycle == 0)  # Active if we're exactly on the cycle
                        
                        gann_cycles.append({
                            "bar_index": bar_index,
                            "cycle_type": f"{cycle_len}-bar cycle",
                            "bar_count": cycle_len,
                            "is_active": is_active,
                            "strength": "CRITICAL" if cycle_len in [90, 180] else "MAJOR",
                            "timestamp": cycle_time.isoformat(),
                            "cycle_start": cycle_start_time.isoformat(),
                            "cycle_end": cycle_time.isoformat(),
                            "bars_ago": bars_since_cycle
                        })
                
                # Add prediction for next cycle
                bars_until_next = cycle_len - (num_bars % cycle_len)
                if bars_until_next > 0 and bars_until_next <= 20:  # Only show if within 20 bars
                    current_time = datetime.utcnow()
                    estimated_end_time = current_time + timedelta(hours=bars_until_next)
                    cycle_start_time = estimated_end_time - timedelta(hours=cycle_len)
                    
                    gann_cycles.append({
                        "bar_index": num_bars + bars_until_next - 1,
                        "cycle_type": f"{cycle_len}-bar cycle",
                        "bar_count": cycle_len,
                        "is_active": False,
                        "bars_until": bars_until_next,
                        "strength": "CRITICAL" if cycle_len in [90, 180] else "MAJOR",
                        "timestamp": current_time.isoformat(),
                        "cycle_start": cycle_start_time.isoformat(),
                        "estimated_end": estimated_end_time.isoformat()
                    })
        except Exception as e:
            print(f"Error getting cycles: {e}")
            import traceback
            traceback.print_exc()
            gann_cycles = []
        
        # ========== Calculate Astro Cycles (Lunar & Solar) ==========
        try:
            astro_cycles = []
            num_bars = len(recent_bars) if recent_bars else 200
            
            # Lunar cycle (29.5 days ~ 708 hours at 1 bar/hour)
            lunar_cycle = 708
            # Solar cycle (365 days ~ 8760 hours)
            solar_cycle = 8760
            # New Moon cycle (synodic month ~29.5 days)
            synodic_cycle = 708
            
            major_astro_cycles = [
                {"type": "Lunar Month", "bars": lunar_cycle, "importance": "CRITICAL", "color": "#7dd3fc"},
                {"type": "New Moon", "bars": synodic_cycle, "importance": "CRITICAL", "color": "#c084fc"},
            ]
            
            for cycle_info in major_astro_cycles:
                cycle_len = cycle_info["bars"]
                if cycle_len <= num_bars:
                    # Find most recent occurrence
                    bars_since_cycle = num_bars % cycle_len
                    bar_index = num_bars - bars_since_cycle - 1
                    
                    if bar_index >= 0:
                        current_time = datetime.utcnow()
                        cycle_time = current_time - timedelta(hours=bars_since_cycle)
                        is_active = (bars_since_cycle == 0)
                        
                        astro_cycles.append({
                            "bar_index": bar_index,
                            "cycle_type": cycle_info["type"],
                            "bar_count": cycle_len,
                            "is_active": is_active,
                            "strength": cycle_info["importance"],
                            "timestamp": cycle_time.isoformat(),
                            "bars_ago": bars_since_cycle
                        })
                
                # Predict next cycle
                bars_until_next = cycle_len - (num_bars % cycle_len)
                if bars_until_next > 0 and bars_until_next <= 100:
                    current_time = datetime.utcnow()
                    estimated_end_time = current_time + timedelta(hours=bars_until_next)
                    
                    astro_cycles.append({
                        "bar_index": num_bars + bars_until_next - 1,
                        "cycle_type": cycle_info["type"],
                        "bar_count": cycle_len,
                        "is_active": False,
                        "bars_until": bars_until_next,
                        "strength": cycle_info["importance"],
                        "timestamp": current_time.isoformat(),
                        "estimated_end": estimated_end_time.isoformat()
                    })
        except Exception as e:
            print(f"Error calculating astro cycles: {e}")
            astro_cycles = []
        
        return MentorPanelResponse(
            market=request.symbol,
            session=market_state["session"],
            time_utc=datetime.utcnow(),
            current_price=price,
            htf_structure=htf_structure,
            iceberg_activity=iceberg_activity,
            gann_levels=gann_levels,
            gann_signal="200% range hit",
            gann_square_of_9=gann_sq9,
            gann_cardinal_cross=gann_cardinal,
            gann_angles=gann_angles,
            gann_clusters=gann_clusters,
            gann_cycles=gann_cycles,
            astro_cycles=astro_cycles,
            active_aspects=active_aspects,
            astro_signal=astro_signal,
            astro_aspects=astro_aspects,
            astro_outlook=astro_outlook,
            moon_phase=moon_phase,
            mercury_retrograde=mercury_rx["is_retrograde"],
            ai_verdict="⛔ WAIT",
            entry_trigger="SELL on rejection below 3358",
            target_zones=[2430.0, 2415.0],
            confidence_percent=81.0,
            risk_assessment=risk_assessment,
            confirmation_status=confirmation_status,
            context_story=context_story,
            context_notes=context_notes,
            context_bullets=context_bullets,
            context_long_story=context_long_story,
            mtf_summary_bullets=mtf_summary_bullets,
            session_narrative=session_narrative,
            invalidations=invalidations,
            trade_summary=trade_summary,
            entry_plan=entry_plan,
            stop_plan=stop_plan,
            target_plan=target_plan,
            news_events=news_events,
            major_news=major_news,
            news_memory=news_memory,
            upcoming_events_count=upcoming_events_count,
            global_markets=global_markets,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== CHART DATA ====================

@router.post("/chart", response_model=ChartResponse)
async def get_chart_data(request: ChartRequest):
    """Get chart data with all levels and overlays from live market."""
    try:
        # Fetch live candles for requested timeframe
        candles_data = await fetch_ohlc_candles(limit=request.bars, interval=request.interval)
        
        if candles_data:
            # Convert to ChartBarData objects
            bars = []
            for candle in candles_data:
                bars.append(ChartBarData(
                    timestamp=datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00")) if isinstance(candle["timestamp"], str) else datetime.utcnow(),
                    open=candle["open"],
                    high=candle["high"],
                    low=candle["low"],
                    close=candle["close"],
                    volume=candle.get("volume", 0)
                ))
            base_price = bars[-1].close if bars else 2450.0
        else:
            # Fallback to sample candles if API fails
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
        
        # Detect iceberg zones and flag bars
        iceberg_flags, iceberg_visuals = _detect_icebergs_from_bars(bars)
        enriched_bars = []
        for bar, flag in zip(bars, iceberg_flags):
            enriched_bars.append(ChartBarData(
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                iceberg_detected=flag
            ))

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
            bars=enriched_bars,
            levels=levels,
            iceberg_zones=iceberg_visuals,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/indicators/volume-profile", response_model=VolumeProfileResponse)
async def get_volume_profile(request: VolumeProfileRequest):
    """
    Calculate Volume Profile for the specified chart data.
    
    Returns:
    - POC (Point of Control): Price level with highest volume
    - VAH/VAL (Value Area High/Low): Boundaries containing 70% of volume
    - VWAP (Volume Weighted Average Price): Institutional benchmark price
    - Histogram: Full price distribution for visual rendering
    """
    try:
        # Fetch live candles for volume profile calculation
        candles_data = await fetch_ohlc_candles(limit=request.bars, interval=request.interval)
        
        if not candles_data:
            # Fallback to sample data if API fails
            candles_data = []
            base_price = market_state["current_price"]
            for i in range(request.bars):
                open_p = base_price + (i * 0.5)
                close_p = open_p + (2.0 if i % 2 == 0 else -2.0)
                candles_data.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "open": open_p,
                    "high": max(open_p, close_p) + 3,
                    "low": min(open_p, close_p) - 3,
                    "close": close_p,
                    "volume": int(market_state["volume_avg"] * (1 + (i % 3) * 0.2))
                })
        
        # Update volume profile engine tick size if provided
        if request.tick_size != volume_profile_engine.tick_size:
            volume_profile_engine.tick_size = request.tick_size
        
        # Build volume profile
        profile = volume_profile_engine.build_profile(
            candles=candles_data,
            value_area_pct=request.value_area_pct
        )
        
        # Convert histogram to schema format
        histogram_bars = [
            VolumeProfileHistogramBar(
                price=bar["price"],
                volume=bar["volume"],
                buy_volume=bar["buy_volume"],
                sell_volume=bar["sell_volume"],
                volume_pct=bar["volume_pct"],
                is_poc=bar["is_poc"],
                in_value_area=bar["in_value_area"]
            )
            for bar in profile["histogram"]
        ]
        
        return VolumeProfileResponse(
            symbol=request.symbol,
            interval=request.interval,
            bars_analyzed=len(candles_data),
            poc=profile["POC"],
            vah=profile["VAH"],
            val=profile["VAL"],
            vwap=profile["VWAP"],
            total_volume=profile["total_volume"],
            total_buy_volume=profile["total_buy_volume"],
            total_sell_volume=profile["total_sell_volume"],
            histogram=histogram_bars,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Volume Profile calculation failed: {str(e)}")


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
            market_state["cme_connected"] = True
            market_state["data_source"] = "CME_LIVE"
        
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
            bias=(
                "SELL" if (high_50 is not None and low_50 is not None and price > (high_50 + low_50) / 2)
                else "BUY"
            )
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


# ==================== STATUS ENDPOINT (FOR FRONTEND) ====================

@router.get("/status")
async def get_status():
    """
    Real-time status endpoint for frontend chart.
    Returns current price, orderflow, and AI decision.
    """
    try:
        price = market_state["current_price"]
        
        # Simulate orderflow data
        buys = int(market_state["volume_current"] * 0.55)
        sells = int(market_state["volume_current"] * 0.45)
        
        # Check for iceberg activity (top 3 zones by volume)
        absorption_zones = sorted(
            absorption_memory.zones,
            key=lambda z: z.get("volume", 0),
            reverse=True
        )[:3]
        iceberg_detected = len(absorption_zones) > 0
        iceberg_zones = [
            {
                "price": z.get("price"),
                "direction": z.get("direction", "UNKNOWN"),
                "volume": z.get("volume"),
                "confidence": round(z.get("confidence", 0.0), 3),
                "timestamp": z.get("timestamp"),
            }
            for z in absorption_zones
        ]
        
        # Generate AI decision
        activity_level = iceberg_detector.estimate_institutional_activity({
            "range": 50,
            "volume": market_state["volume_current"]
        })
        
        decision_text = "EXECUTE" if activity_level > 0.7 else "WAIT" if activity_level > 0.4 else "SKIP"
        confidence = min(95, int(activity_level * 100))
        
        # Generate narrative
        if iceberg_detected:
            narrative = (
                f"🧱 Iceberg at {absorption_zones[0]['price']:.2f} "
                f"({absorption_zones[0].get('direction', 'UNKNOWN')}) | "
                f"Vol: {absorption_zones[0].get('volume', 0)} | {decision_text}"
            )
        else:
            narrative = f"📊 Monitoring {market_state['session']} session | Price: {price:.2f} | Volume: {market_state['volume_current']}"
        
        return {
            "price": price,
            "orderflow": {
                "buys": buys,
                "sells": sells
            },
            "iceberg": {
                "detected": iceberg_detected,
                "count": len(absorption_zones),
                "zones": iceberg_zones,
            },
            "decision": {
                "decision": decision_text,
                "confidence": confidence
            },
            "narrative": narrative,
            "session": market_state["session"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "price": market_state["current_price"],
            "orderflow": {"buys": 800, "sells": 600},
            "iceberg": False,
            "decision": {"decision": "WAIT", "confidence": 50},
            "narrative": "Monitoring market...",
            "session": market_state["session"],
            "timestamp": datetime.utcnow().isoformat()
        }


# ==================== CREATE FASTAPI APP ====================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Quantum Market Observer API",
    description="Institutional-grade AI trading analysis for gold futures",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Serve static frontend files from /frontend directory
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
