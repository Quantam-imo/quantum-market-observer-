"""
STEP 23: Replay Engine (Enhanced)
Candle-by-candle reconstruction of AI decision logic
Institutional-grade backtesting (not bulk optimization)

STEP 23-B: Session + News + Iceberg-aware replay
"""

from backtesting.session_engine import SessionEngine
from backtesting.news_engine import NewsEngine
from backtesting.iceberg_memory import IcebergMemory
from backtesting.replay_filters import ReplayFilters
from backtesting.explanation_engine import ExplanationEngine
from backtesting.timeline_builder import TimelineBuilder
from backtesting.chart_packet_builder import ChartPacketBuilder
from backtesting.signal_lifecycle import SignalLifecycle
from backtesting.replay_cursor import ReplayCursor
from backtesting.heatmap_engine import HeatmapEngine


class ReplayEngine:
    """
    Core replay loop: exactly how live trading will behave
    For each candle: update state → run AI → save snapshot
    
    STEP 23-B: Now includes session awareness, news injection, iceberg memory
    """

    def __init__(
        self,
        qmo,
        imo,
        gann,
        astro,
        cycle,
        mentor,
        snapshot_store,
        news_events=None,
    ):
        self.qmo = qmo
        self.imo = imo
        self.gann = gann
        self.astro = astro
        self.cycle = cycle
        self.mentor = mentor
        self.snapshots = snapshot_store
        
        # ---- STEP 23-B ADDITIONS ----
        self.session_engine = SessionEngine()
        self.news_engine = NewsEngine(news_events or [])
        self.iceberg_memory = IcebergMemory()
        self.replay_filters = ReplayFilters()
        
        # ---- STEP 23-C ADDITIONS ----
        self.explainer = ExplanationEngine()
        self.timeline = TimelineBuilder()
        self.chart_packet_builder = ChartPacketBuilder()
        
        # ---- STEP 23-D ADDITIONS ----
        self.lifecycle = SignalLifecycle()
        self.cursor = None  # Will be initialized in run()
        self.heatmap_engine = HeatmapEngine()
        self.candles_store = None  # Store for cursor access

    def run(self, candles):
        """
        Process historical candles in sequence.
        
        Args:
            candles: list of dicts with keys:
                time, open, high, low, close, volume
        """
        # ---- STEP 23-D: INITIALIZE CURSOR & STORE CANDLES ----
        self.candles_store = candles
        self.cursor = ReplayCursor(candles, self.timeline.export())
        
        for i in range(len(candles)):
            candle = candles[i]

            # ---- MARKET STATE UPDATE ----
            # Same order as live trading
            qmo_state = self.qmo.update(candle)
            liquidity = self.imo.update(candle)
            gann_levels = self.gann.update(candle)
            astro_state = self.astro.update(candle)
            cycle_state = self.cycle.update(i)
            
            # ---- STEP 23-B: SESSION & NEWS ----
            session = self.session_engine.get_session(candle["time"])
            killzone = self.session_engine.is_killzone(session, candle["time"])
            news = self.news_engine.check_news_window(candle["time"])
            
            # ---- STEP 23-B: ICEBERG MEMORY ----
            iceberg_score = self.iceberg_memory.persistence_score(
                candle["close"]
            )

            # ---- AI CONTEXT ----
            context = {
                "time": candle["time"],
                "price": candle["close"],
                "qmo": qmo_state,
                "liquidity": liquidity,
                "gann": gann_levels,
                "astro": astro_state,
                "cycle": cycle_state,
                # STEP 23-B additions
                "session": session,
                "killzone": killzone,
                "news": news,
                "iceberg_score": iceberg_score,
            }

            # ---- STEP 23-B: SIGNAL QUALITY GATE ----
            if not self.replay_filters.allow_signal(context):
                decision = None
            else:
                # ---- AI DECISION ----
                decision = self.mentor.evaluate(context)
            
            # ---- STEP 23-D: SIGNAL LIFECYCLE TRACKING ----
            # Update signal state machine
            lifecycle_state = self.lifecycle.update(context, decision)
            context["lifecycle"] = lifecycle_state
            
            # ---- STEP 23-C: EXPLANATION + TIMELINE + CHART ----
            # Build explanation for this candle's decision
            explanation = self.explainer.build(context, decision)
            
            # Record to institutional audit trail
            self.timeline.record(
                candle=candle,
                context=context,
                decision=decision,
                explanation=explanation,
            )
            
            # Build chart-ready packet
            chart_packet = self.chart_packet_builder.record(
                candle=candle,
                context=context,
                decision=decision,
                explanation=explanation,
            )

            # ---- SNAPSHOT SAVE ----
            self.snapshots.store(
                candle=candle,
                context=context,
                decision=decision,
            )

    def get_snapshots(self):
        """Return all recorded snapshots"""
        return self.snapshots.all()
    
    def get_timeline(self):
        """Return institutional audit trail (STEP 23-C)"""
        return self.timeline.export()
    
    def get_chart_packets(self):
        """Return chart-ready data packets (STEP 23-C)"""
        return self.chart_packet_builder.export()
    
    def export_timeline_json(self, filepath):
        """Export timeline to JSON file"""
        return self.timeline.export_json(filepath)
    
    def export_timeline_csv(self, filepath):
        """Export timeline to CSV file"""
        return self.timeline.export_csv(filepath)
    
    def export_chart_packets(self, filepath):
        """Export chart packets to JSON"""
        return self.chart_packet_builder.export_json(filepath)
    
    def get_cursor(self):
        """Return replay cursor for time-travel (STEP 23-D)"""
        return self.cursor
    
    def get_lifecycle_history(self):
        """Return signal lifecycle history (STEP 23-D)"""
        return self.lifecycle.get_history()
    
    def get_lifecycle_summary(self):
        """Return signal lifecycle summary (STEP 23-D)"""
        return self.lifecycle.lifecycle_summary()
    
    def get_heatmaps(self):
        """Return all generated heatmaps (STEP 23-D)"""
        if not self.timeline.export():
            return {}
        return self.heatmap_engine.generate_all_heatmaps(self.timeline.export())
    
    def get_heatmap(self, heatmap_type):
        """Get specific heatmap (confidence, activity, session, killzone, news, iceberg)"""
        return self.heatmap_engine.get_heatmap(heatmap_type)
    
    def export_heatmaps(self, filepath):
        """Export all heatmaps to JSON"""
        return self.heatmap_engine.export_heatmaps_json(filepath)
