"""
STEP 23: Replay Runner
One-command entry point to run institutional replay
"""

from backtesting.replay_engine import ReplayEngine
from backtesting.ai_snapshot import AISnapshotStore
from backtesting.trade_outcome import TradeOutcomeAnalyzer
from backtesting.edge_metrics import EdgeMetrics


def run_replay(candles, engines, config=None, news_events=None):
    """
    Run complete replay with outcome analysis.

    Args:
        candles: list of dicts with OHLCV data
        engines: dict with keys {qmo, imo, gann, astro, cycle, mentor}
        config: optional replay configuration
        news_events: optional list of news dicts (STEP 23-B)

    Returns:
        {
            "snapshots": all AI states,
            "outcomes": signal outcomes,
            "metrics": institutional metrics,
            "summary": executive summary
        }
    """
    snapshot_store = AISnapshotStore()

    # ---- RUN REPLAY ----
    replay = ReplayEngine(
        qmo=engines["qmo"],
        imo=engines["imo"],
        gann=engines["gann"],
        astro=engines["astro"],
        cycle=engines["cycle"],
        mentor=engines["mentor"],
        snapshot_store=snapshot_store,
        news_events=news_events,  # STEP 23-B
    )

    replay.run(candles)
    snapshots = snapshot_store.all()

    # ---- EVALUATE OUTCOMES ----
    analyzer = TradeOutcomeAnalyzer()
    outcomes = []

    for i, snapshot in enumerate(snapshots):
        if i + 1 < len(candles):
            future_candles = candles[i + 1 :]
            outcome = analyzer.evaluate_signal(
                snapshot, future_candles, max_lookahead=30
            )
        else:
            outcome = None

        outcomes.append(outcome)

    # ---- CALCULATE METRICS ----
    metrics = EdgeMetrics()
    for snapshot, outcome in zip(snapshots, outcomes):
        if outcome:
            metrics.record(snapshot, outcome)

    return {
        "snapshots": snapshots,
        "outcomes": outcomes,
        "metrics": metrics.summary(),
        "snapshot_stats": snapshot_store.count(),
        "confidence_dist": snapshot_store.confidence_distribution(),
    }


def replay_report(replay_result):
    """
    Generate readable report from replay results.

    Args:
        replay_result: output from run_replay()

    Returns:
        formatted summary dict
    """
    return {
        "replay_overview": {
            "total_candles": replay_result["snapshot_stats"]["total_candles"],
            "signals_generated": replay_result["snapshot_stats"]["signals"],
            "signals_skipped": replay_result["snapshot_stats"]["skips"],
            "signal_rate_pct": round(
                replay_result["snapshot_stats"]["signal_rate"] * 100, 1
            ),
        },
        "ai_confidence": {
            "min": replay_result["confidence_dist"].get("min", 0),
            "max": replay_result["confidence_dist"].get("max", 0),
            "avg": replay_result["confidence_dist"].get("avg", 0),
            "above_70_count": replay_result["confidence_dist"].get(
                "total_above_70", 0
            ),
        },
        "edge_metrics": replay_result["metrics"],
    }
