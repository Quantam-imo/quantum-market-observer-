"""Lightweight API v2 scaffold for stepwise rollout.

Provides a health check and a simple user-context probe to be reused
by downstream endpoints (mentor signal, dashboard, overlays).
"""

from datetime import datetime
from enum import Enum
from fastapi import APIRouter, Header, Depends

# Core mentor/pipeline pieces
from backend.intelligence.step3_imo_pipeline import Step3IMOPipeline
from backend.intelligence.volatility_regime_engine import VolatilityRegimeEngine
from backend.intelligence.edge_decay_engine import EdgeDecayEngine
from backend.intelligence.capital_protection_engine import CapitalProtectionEngine
from backend.pricing.integration import PricingIntegration
from backend.pricing.tier_system import SubscriptionTier
from backend.mentor.progression_engine import TraderPhase
from backend.structure.fvg_engine import FVGEngine
from backend.structure.liquidity_map import LiquidityMap
from backend.structure.htf_structure import HTFStructure
from backend.volume_profile_engine import VolumeProfileEngine
from backend.orderflow.price_ladder import PriceLadder
from backend.backtesting.trade_journal import TradeJournal
from backend.backtesting.backtest_engine import BacktestEngine
from backend.backtesting.historical_loader import HistoricalDataLoader
from backend.intelligence.news_filter import NewsFilter
from backend.session.session_engine import SessionEngine
from backend.risk.position_sizer import PositionSizer
from pydantic import BaseModel
from typing import Optional, List


class Tier(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    ELITE = "ELITE"


class Phase(str, Enum):
    BEGINNER = "BEGINNER"
    ASSISTED = "ASSISTED"
    SUPERVISED_PRO = "SUPERVISED_PRO"
    FULL_PRO = "FULL_PRO"


router = APIRouter(prefix="/api/v2", tags=["v2"])

# Reuse a single pipeline instance for speed (stateless for now)
pipeline = Step3IMOPipeline()
vol_engine = VolatilityRegimeEngine()
edge_decay = EdgeDecayEngine()
cap_protect = CapitalProtectionEngine()
fvg_engine = FVGEngine()
liquidity_map = LiquidityMap()
htf_structure = HTFStructure()
vp_engine = VolumeProfileEngine()
price_ladder = PriceLadder()
trade_journal = TradeJournal()
backtest_engine = BacktestEngine()
historical_loader = HistoricalDataLoader(data_source="simulation")
news_filter = NewsFilter()
session_engine = SessionEngine()
position_sizer = PositionSizer()


def get_user_profile(
    x_user_tier: str | None = Header(default=None),
    x_user_phase: str | None = Header(default=None),
):
    """Basic user profile dependency.

    Defaults to BASIC / BEGINNER if headers are absent. Intended to be
    replaced by auth in later steps.
    """

    tier = Tier[x_user_tier] if x_user_tier and x_user_tier in Tier.__members__ else Tier.BASIC
    phase = Phase[x_user_phase] if x_user_phase and x_user_phase in Phase.__members__ else Phase.BEGINNER
    return {"tier": tier, "phase": phase}


@router.get("/health")
async def health_v2():
    """Lightweight health check for v2 endpoints."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v2",
    }


@router.get("/whoami")
async def whoami(profile=Depends(get_user_profile)):
    """Return the inferred user tier/phase for UI gating tests."""
    return {
        "tier": profile["tier"],
        "phase": profile["phase"],
        "note": "Override via X-User-Tier and X-User-Phase headers",
    }


@router.get("/mentor/signal")
async def mentor_signal(profile=Depends(get_user_profile)):
    """Return a tier-filtered mentor signal (stub data for now).

    Step 2 scaffolds the endpoint with a minimal mock decision to
    exercise pricing integration and UI gating. In later steps this
    will call live Step3IMOPipeline output.
    """

    # Mock tick/candle to keep this endpoint fast and deterministic
    sample_ticks = [
        {"price": 3362.4, "size": 48, "side": "BUY", "timestamp": "10:42:11"},
        {"price": 3362.5, "size": 52, "side": "BUY", "timestamp": "10:42:12"},
        {"price": 3362.4, "size": 45, "side": "SELL", "timestamp": "10:42:13"},
    ]
    sample_candle = {
        "open": 3362.0,
        "high": 3365.5,
        "low": 3361.0,
        "close": 3363.0,
        "volume": 500,
        "time": "10:45:00",
    }

    decision = pipeline.process_tick(sample_ticks, [sample_candle])

    # Build user-friendly signal from IMO decision
    action = "WAIT"
    reason = "Monitoring market structure for institutional signals..."
    
    if decision.get("decision") == "EXECUTE":
        action = "EXECUTE"
        if decision.get("confidence", 0) > 0.85:
            reason = "High institutional conviction - strong setup detected"
        else:
            reason = "Institutional structure confirmed - ready for execution"
    elif decision.get("decision") == "WAIT":
        action = "WAIT"
        reason = "Partial institutional signal - waiting for stronger confirmation"
    else:
        action = "SKIP"
        reason = "No clear institutional structure yet - continue monitoring"

    full_signal = {
        "action": action,
        "confidence": int(decision.get("confidence", 0) * 100),
        "reason": reason,
        "entry_zone": {"min": "3362.0", "max": "3365.0"},
        "stops": {"conservative": "3374.0", "aggressive": "3370.0"},
        "targets": ["3345.0", "3320.0"],
    }

    pricing = PricingIntegration(
        user_tier=SubscriptionTier[profile["tier"].name],
        user_phase=TraderPhase[profile["phase"].name],
    )

    formatted_signal = pricing.format_signal_for_tier(full_signal)
    ui_permissions = pricing.get_ui_permissions()

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "signal": formatted_signal,
        "ui_permissions": ui_permissions,
    }


@router.get("/dashboard")
async def dashboard(profile=Depends(get_user_profile)):
    """Aggregate key metrics for a simple dashboard.

    Uses the last pipeline decision plus volatility regime, edge decay,
    and capital protection snapshots. Intended as a lightweight read-only
    view; no execution side effects.
    """

    # Minimal tick to keep pipeline state non-empty
    sample_ticks = [
        {"price": 3362.4, "size": 48, "side": "BUY", "timestamp": "10:42:11"},
        {"price": 3362.5, "size": 52, "side": "BUY", "timestamp": "10:42:12"},
        {"price": 3362.4, "size": 45, "side": "SELL", "timestamp": "10:42:13"},
    ]
    sample_candle = {
        "open": 3362.0,
        "high": 3365.5,
        "low": 3361.0,
        "close": 3363.0,
        "volume": 500,
        "time": "10:45:00",
    }

    pipeline.process_tick(sample_ticks, [sample_candle])

    dashboard_payload = pipeline.get_dashboard_data()

    # Volatility regime (update with sample bar to keep state fresh)
    vol_engine.update(high=3365.5, low=3361.0, close=3363.0)

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "imo": dashboard_payload.get("imo_decision", {}),
        "memory": dashboard_payload.get("memory", {}),
        "recent_zones": dashboard_payload.get("recent_zones", []),
        "sweeps": dashboard_payload.get("sweep_history", []),
        "decision_quality": dashboard_payload.get("decision_quality", {}),
        "execution_count": dashboard_payload.get("execution_count", 0),
        "imo_explanation": dashboard_payload.get("imo_explanation", ""),
        "volatility": vol_engine.get_all_regime_stats(),
        "edge_decay": edge_decay.get_all_decays(),
        "capital_protection": cap_protect.get_protection_status(),
    }


@router.get("/chart/overlays")
async def chart_overlays(profile=Depends(get_user_profile)):
    """Return chart overlays: iceberg zones, sweeps, FVG, liquidity pools, HTF, volume profile.

    Uses small sample data for now to keep the endpoint deterministic;
    later can be fed by live price/ladder feeds.
    """

    # Sample candles (could be replaced with live feed)
    candles = [
        {"open": 3360.0, "high": 3365.0, "low": 3358.0, "close": 3362.0, "volume": 700},
        {"open": 3362.0, "high": 3366.5, "low": 3360.5, "close": 3365.5, "volume": 820},
        {"open": 3365.5, "high": 3368.0, "low": 3362.0, "close": 3363.0, "volume": 900},
        {"open": 3363.0, "high": 3364.5, "low": 3359.5, "close": 3360.0, "volume": 750},
    ]

    # Build overlays
    iceberg_zones = pipeline.memory.get_zones_for_chart()
    sweeps = pipeline.sweeps.get_recent_sweeps(count=10)
    fvg = fvg_engine.detect(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    liquidity_pools = liquidity_map.detect(highs, lows)
    htf = htf_structure.compute_htf_structure(candles)
    vp = vp_engine.build_profile(candles)

    # Price ladder snapshot (empty unless fed externally)
    ladder = price_ladder.snapshot()

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "iceberg_zones": iceberg_zones,
        "sweeps": sweeps,
        "fvg": fvg,
        "liquidity_pools": liquidity_pools,
        "htf_structure": htf,
        "volume_profile": vp,
        "price_ladder": ladder,
    }


class TradeLogRequest(BaseModel):
    """Request model for logging a trade."""
    entry_time: str
    exit_time: Optional[str] = None
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    r_multiple: Optional[float] = None
    result: Optional[str] = None
    setup_type: str
    ai_confidence: float
    execution_notes: Optional[str] = None
    failure_reason: Optional[str] = None


class BacktestRequest(BaseModel):
    """Request model for running a backtest."""
    instrument: str = "GC"
    start_date: str  # ISO format YYYY-MM-DD
    end_date: str    # ISO format YYYY-MM-DD
    data_source: str = "simulation"


@router.post("/trade/log")
async def log_trade(request: TradeLogRequest, profile=Depends(get_user_profile)):
    """Log a completed or pending trade to the journal.

    Accepts trade details and stores them for later analysis.
    Returns a simple acknowledgment with trade ID.
    """

    trade_data = request.dict()
    trade_journal.log_trade(trade_data)

    return {
        "status": "logged",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "trade": {
            "setup_type": request.setup_type,
            "direction": request.direction,
            "entry_price": request.entry_price,
            "result": request.result or "PENDING",
        },
        "message": "Trade logged successfully",
    }


@router.get("/journal/summary")
async def journal_summary(profile=Depends(get_user_profile)):
    """Get daily journal summary with performance metrics."""

    try:
        analysis = trade_journal.analyze_session()
    except Exception as e:
        # Return empty state if journal fails
        return {
            "status": "empty",
            "message": "No trades logged today",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e)
        }

    if not analysis:
        return {
            "status": "empty",
            "message": "No trades logged today",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "summary": analysis,
    }


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest, profile=Depends(get_user_profile)):
    """Run a backtest on historical data.

    Loads historical data for the specified date range and runs the full
    system pipeline to evaluate performance. Returns win rate, avg R, and
    condition breakdown.
    """

    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)

    # Load historical data
    historical_data = historical_loader.load_date_range(
        start_date=start_date,
        end_date=end_date,
        instrument=request.instrument
    )

    # Run backtest
    results = backtest_engine.run_backtest(
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "backtest": {
            "instrument": request.instrument,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "data_source": request.data_source,
            "candles_processed": len(historical_data),
        },
        "results": results,
        "message": "Backtest completed successfully",
    }


@router.get("/guards")
async def get_guards(profile=Depends(get_user_profile)):
    """Check all guard conditions: news risk, session timing, risk limits.

    Returns the current state of all safety guards and whether trading
    is currently allowed. Used by frontend to show/hide execution buttons.
    """

    # Check news risk (simplified - no major events in sample)
    news_state = {
        "risk_level": "NORMAL",
        "allow_trade": True,
        "active_events": [],
        "next_event": None,
    }
    
    # Check session timing
    current_time = datetime.utcnow().time()
    current_session = session_engine.get_session(current_time)
    
    # Simplified - assume trade allowed for demo
    session_state = {
        "session": current_session,
        "allowed": current_session in ["LONDON", "NEW_YORK"],
        "reason": "Session active" if current_session in ["LONDON", "NEW_YORK"] else "Outside trading hours",
        "next_open": None,
    }
    
    # Check risk limits (sample account state)
    sample_account = {
        "balance": 10000.0,
        "daily_pnl": -150.0,
        "open_trades": 1,
    }
    
    daily_loss_pct = (sample_account["daily_pnl"] / sample_account["balance"]) * 100
    kill_status = position_sizer.kill_switch(sample_account["daily_pnl"] / sample_account["balance"], 0)
    
    risk_state = {
        "can_trade": kill_status != "locked",
        "daily_loss_pct": abs(daily_loss_pct),
        "max_daily_loss_pct": 2.0,
        "open_trades": sample_account["open_trades"],
        "max_concurrent": 3,
        "reason": "Risk limits OK" if kill_status != "locked" else "Daily loss limit exceeded",
    }
    
    # Aggregate allow status
    all_clear = (
        news_state.get("allow_trade", True) and
        session_state.get("allowed", True) and
        risk_state.get("can_trade", True)
    )
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tier": profile["tier"],
        "phase": profile["phase"],
        "trading_allowed": all_clear,
        "guards": {
            "news": news_state,
            "session": session_state,
            "risk": risk_state,
        },
        "message": "Trading allowed" if all_clear else "Trading blocked by guards",
    }
