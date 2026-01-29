"""
ICEBERG DETECTION ENGINE
Real institutional orderflow analysis from CME Gold Futures (GC)
Detects hidden large orders through L3 order book data

WHAT IS AN ICEBERG:
- Large orders split into small visible pieces
- Repeatedly executed at same price level
- Price doesn't move despite high volume (absorption)
- Indicates institutional positioning

DETECTION LOGIC:
1. Track order executions at each price level
2. Identify repeated fills without price movement
3. Calculate volume concentration vs average
4. Determine absorption side (buy vs sell)
"""

import databento as db
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import os


class IcebergSide(Enum):
    """Direction of iceberg absorption"""
    BUY_ABSORPTION = "BUY"    # Iceberg buying (bullish institution positioning)
    SELL_ABSORPTION = "SELL"  # Iceberg selling (bearish institution positioning)
    NEUTRAL = "NEUTRAL"       # No clear absorption


@dataclass
class IcebergZone:
    """
    Detected iceberg zone with institutional significance
    """
    price: float
    side: IcebergSide
    total_volume: int
    execution_count: int
    first_seen: datetime
    last_seen: datetime
    avg_size_per_execution: float
    concentration_ratio: float  # volume / avg_volume (higher = stronger iceberg)
    confidence: float  # 0.0 to 1.0
    is_active: bool = True
    
    def __repr__(self):
        symbol = "🟢" if self.side == IcebergSide.BUY_ABSORPTION else "🔴" if self.side == IcebergSide.SELL_ABSORPTION else "⚪"
        return f"{symbol} Iceberg @ ${self.price:.2f} | Vol: {self.total_volume} | Conf: {self.confidence:.1%}"


class IcebergDetector:
    """
    Real-time iceberg detection from L3 order book
    Institutional-grade orderflow analysis
    """
    
    def __init__(
        self,
        min_executions: int = 5,           # Minimum repeated executions
        volume_multiplier: float = 3.0,    # Volume must be X times average
        time_window_seconds: int = 30,     # Detection window
        price_tolerance_ticks: int = 1,    # Allow slight price movement
        min_confidence: float = 0.70,      # Minimum confidence to report
    ):
        # Detection parameters
        self.min_executions = min_executions
        self.volume_multiplier = volume_multiplier
        self.time_window_seconds = time_window_seconds
        self.price_tolerance_ticks = price_tolerance_ticks
        self.min_confidence = min_confidence
        
        # Tracking structures
        self.executions_by_price = defaultdict(list)  # price -> [(timestamp, size, side), ...]
        self.recent_executions = deque(maxlen=1000)   # Rolling window for avg volume
        self.detected_icebergs = []                    # Active iceberg zones
        self.historical_icebergs = []                  # Past icebergs for memory
        
        # Statistics
        self.total_volume = 0
        self.total_executions = 0
        self.avg_execution_size = 0.0
        
        print("❄️  ICEBERG DETECTOR INITIALIZED")
        print(f"   Min executions: {min_executions}")
        print(f"   Volume threshold: {volume_multiplier}x average")
        print(f"   Time window: {time_window_seconds}s")
        print(f"   Confidence threshold: {min_confidence:.0%}")
        
    def update_statistics(self, size: int):
        """Update rolling statistics for baseline comparison"""
        self.total_volume += size
        self.total_executions += 1
        self.avg_execution_size = self.total_volume / self.total_executions
        self.recent_executions.append(size)
        
    def get_rolling_avg_size(self) -> float:
        """Calculate recent average execution size"""
        if not self.recent_executions:
            return 100.0  # Default baseline
        return sum(self.recent_executions) / len(self.recent_executions)
        
    def process_trade(
        self,
        price: float,
        size: int,
        side: str,  # "buy" or "sell"
        timestamp: datetime
    ) -> Optional[IcebergZone]:
        """
        Process individual trade and detect iceberg pattern
        
        Returns newly detected iceberg zone if found, else None
        """
        # Update statistics
        self.update_statistics(size)
        
        # Round price to handle floating point
        price_key = round(price, 2)
        
        # Add to execution tracker
        self.executions_by_price[price_key].append({
            'timestamp': timestamp,
            'size': size,
            'side': side,
        })
        
        # Clean old executions outside time window
        cutoff_time = timestamp - timedelta(seconds=self.time_window_seconds)
        self.executions_by_price[price_key] = [
            ex for ex in self.executions_by_price[price_key]
            if ex['timestamp'] >= cutoff_time
        ]
        
        # Check for iceberg pattern at this price
        return self._detect_iceberg_at_price(price_key, timestamp)
        
    def _detect_iceberg_at_price(
        self,
        price: float,
        current_time: datetime
    ) -> Optional[IcebergZone]:
        """
        Analyze executions at specific price for iceberg pattern
        
        DETECTION CRITERIA:
        1. Multiple executions (min_executions)
        2. High volume concentration (volume_multiplier * avg)
        3. Price stability (minimal movement)
        4. Directional bias (more buying or selling)
        """
        executions = self.executions_by_price[price]
        
        if len(executions) < self.min_executions:
            return None
            
        # Calculate metrics
        total_volume = sum(ex['size'] for ex in executions)
        execution_count = len(executions)
        avg_size = total_volume / execution_count
        
        # Get rolling baseline
        rolling_avg = self.get_rolling_avg_size()
        concentration_ratio = total_volume / (rolling_avg * execution_count) if rolling_avg > 0 else 0
        
        # Check volume concentration threshold
        if concentration_ratio < self.volume_multiplier:
            return None
            
        # Determine absorption side
        buy_volume = sum(ex['size'] for ex in executions if ex['side'].lower() == 'buy')
        sell_volume = sum(ex['size'] for ex in executions if ex['side'].lower() == 'sell')
        
        if buy_volume > sell_volume * 1.5:
            side = IcebergSide.BUY_ABSORPTION
            imbalance = buy_volume / total_volume if total_volume > 0 else 0
        elif sell_volume > buy_volume * 1.5:
            side = IcebergSide.SELL_ABSORPTION
            imbalance = sell_volume / total_volume if total_volume > 0 else 0
        else:
            side = IcebergSide.NEUTRAL
            imbalance = 0.5
            
        # Calculate confidence
        confidence = self._calculate_confidence(
            execution_count=execution_count,
            concentration_ratio=concentration_ratio,
            imbalance=imbalance,
        )
        
        if confidence < self.min_confidence:
            return None
            
        # Create iceberg zone
        iceberg = IcebergZone(
            price=price,
            side=side,
            total_volume=total_volume,
            execution_count=execution_count,
            first_seen=executions[0]['timestamp'],
            last_seen=executions[-1]['timestamp'],
            avg_size_per_execution=avg_size,
            concentration_ratio=concentration_ratio,
            confidence=confidence,
            is_active=True,
        )
        
        # Check if this is new or update to existing
        existing = self._find_existing_iceberg(price)
        if existing:
            # Update existing
            existing.total_volume = total_volume
            existing.execution_count = execution_count
            existing.last_seen = current_time
            existing.confidence = confidence
            return None  # Not a new detection
        else:
            # New iceberg detected
            self.detected_icebergs.append(iceberg)
            print(f"\n❄️  NEW ICEBERG DETECTED: {iceberg}")
            return iceberg
            
    def _calculate_confidence(
        self,
        execution_count: int,
        concentration_ratio: float,
        imbalance: float,
    ) -> float:
        """
        Calculate confidence score for iceberg detection
        
        Factors:
        - More executions = higher confidence
        - Higher concentration = higher confidence
        - Stronger imbalance = higher confidence
        """
        # Execution count score (0.0 to 0.4)
        exec_score = min(execution_count / (self.min_executions * 3), 1.0) * 0.4
        
        # Concentration score (0.0 to 0.4)
        conc_score = min(concentration_ratio / (self.volume_multiplier * 2), 1.0) * 0.4
        
        # Imbalance score (0.0 to 0.2)
        # 0.5 = neutral, 1.0 = all one side
        imbalance_score = (abs(imbalance - 0.5) * 2) * 0.2
        
        return exec_score + conc_score + imbalance_score
        
    def _find_existing_iceberg(self, price: float) -> Optional[IcebergZone]:
        """Find existing iceberg at or near price"""
        for iceberg in self.detected_icebergs:
            if abs(iceberg.price - price) <= self.price_tolerance_ticks * 0.01:
                return iceberg
        return None
        
    def expire_old_icebergs(self, current_time: datetime):
        """Move inactive icebergs to historical"""
        cutoff = current_time - timedelta(seconds=self.time_window_seconds * 2)
        
        active = []
        for iceberg in self.detected_icebergs:
            if iceberg.last_seen >= cutoff:
                active.append(iceberg)
            else:
                iceberg.is_active = False
                self.historical_icebergs.append(iceberg)
                print(f"⏰ Iceberg expired: {iceberg}")
                
        self.detected_icebergs = active
        
    def get_active_icebergs(self) -> List[IcebergZone]:
        """Get currently active iceberg zones"""
        return [iz for iz in self.detected_icebergs if iz.is_active]
        
    def get_buy_icebergs(self) -> List[IcebergZone]:
        """Get active buy absorption icebergs"""
        return [
            iz for iz in self.detected_icebergs
            if iz.is_active and iz.side == IcebergSide.BUY_ABSORPTION
        ]
        
    def get_sell_icebergs(self) -> List[IcebergZone]:
        """Get active sell absorption icebergs"""
        return [
            iz for iz in self.detected_icebergs
            if iz.is_active and iz.side == IcebergSide.SELL_ABSORPTION
        ]
        
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            "total_executions": self.total_executions,
            "total_volume": self.total_volume,
            "avg_execution_size": self.avg_execution_size,
            "active_icebergs": len(self.get_active_icebergs()),
            "buy_icebergs": len(self.get_buy_icebergs()),
            "sell_icebergs": len(self.get_sell_icebergs()),
            "historical_count": len(self.historical_icebergs),
        }


class DatabentoCMIcebergStream:
    """
    Live iceberg detection from Databento L3 data
    Streams CME Gold Futures and processes orderflow
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DATABENTO_API_KEY")
        if not self.api_key:
            raise ValueError("❌ DATABENTO_API_KEY required")
            
        self.detector = IcebergDetector()
        self.client = None
        self.is_running = False
        
    async def stream_with_detection(
        self,
        callback=None,
        duration_seconds: int = None,
    ):
        """
        Stream live L3 orderflow and detect icebergs
        
        Args:
            callback: Optional async function to call on iceberg detection
            duration_seconds: Run for N seconds (None = forever)
        """
        try:
            print("\n" + "="*70)
            print("❄️  STARTING ICEBERG DETECTION STREAM")
            print("="*70)
            print(f"Symbol: GC (COMEX Gold Futures)")
            print(f"Schema: mbo (L3 - Market by Order)")
            print(f"Dataset: GLBX.MDP3 (CME)")
            print("="*70 + "\n")
            
            self.client = db.Live(
                key=self.api_key,
                dataset="GLBX.MDP3",
                schema="mbo",  # L3 required for iceberg detection
                symbols=["GC"],
            )
            
            self.client.start()
            self.is_running = True
            
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            iceberg_count = 0
            
            for msg in self.client:
                message_count += 1
                now = datetime.now(timezone.utc)
                
                # Extract trade data from L3 message
                try:
                    price = getattr(msg, 'price', None)
                    size = getattr(msg, 'size', None)
                    side = getattr(msg, 'side', None)
                    
                    if price and size and side:
                        # Process trade through detector
                        iceberg = self.detector.process_trade(
                            price=price / 1e9,  # Databento price scaling
                            size=size,
                            side='buy' if side == 'B' else 'sell',
                            timestamp=now,
                        )
                        
                        # New iceberg detected
                        if iceberg:
                            iceberg_count += 1
                            print(f"\n🎯 ICEBERG #{iceberg_count}: {iceberg}\n")
                            
                            if callback:
                                await callback(iceberg)
                                
                        # Periodic status update
                        if message_count % 100 == 0:
                            stats = self.detector.get_stats()
                            print(f"📊 Status: {message_count} msgs | "
                                  f"{stats['active_icebergs']} active | "
                                  f"{stats['buy_icebergs']}🟢 {stats['sell_icebergs']}🔴")
                            
                        # Expire old icebergs
                        if message_count % 50 == 0:
                            self.detector.expire_old_icebergs(now)
                            
                except Exception as e:
                    print(f"⚠️  Error processing message: {e}")
                    continue
                    
                # Check duration
                if duration_seconds:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > duration_seconds:
                        print(f"\n⏰ Duration complete: {duration_seconds}s")
                        break
                        
        except db.DBNException as e:
            print(f"❌ Databento error: {e}")
            print("💡 Make sure you have L3 (mbo) schema access")
            
        except Exception as e:
            print(f"❌ Stream error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.client:
                self.client.stop()
                self.is_running = False
                
            # Final stats
            stats = self.detector.get_stats()
            print("\n" + "="*70)
            print("📊 FINAL STATISTICS")
            print("="*70)
            print(f"Messages processed: {message_count}")
            print(f"Total executions: {stats['total_executions']}")
            print(f"Total volume: {stats['total_volume']:,}")
            print(f"Avg execution size: {stats['avg_execution_size']:.0f}")
            print(f"Icebergs detected: {iceberg_count}")
            print(f"Active icebergs: {stats['active_icebergs']}")
            print(f"  🟢 Buy absorption: {stats['buy_icebergs']}")
            print(f"  🔴 Sell absorption: {stats['sell_icebergs']}")
            print("="*70 + "\n")


# ============= TESTING =============

async def test_iceberg_detection():
    """Run live iceberg detection test"""
    streamer = DatabentoCMIcebergStream()
    
    async def on_iceberg_detected(iceberg: IcebergZone):
        """Callback when iceberg found"""
        print(f"\n🚨 ALERT: {iceberg}")
        print(f"   Time: {iceberg.last_seen.strftime('%H:%M:%S')}")
        print(f"   Volume: {iceberg.total_volume:,}")
        print(f"   Executions: {iceberg.execution_count}")
        print(f"   Confidence: {iceberg.confidence:.1%}\n")
        
    # Run for 60 seconds
    await streamer.stream_with_detection(
        callback=on_iceberg_detected,
        duration_seconds=60,
    )


if __name__ == "__main__":
    """
    Run iceberg detection:
    python backend/feeds/iceberg_detector.py
    """
    asyncio.run(test_iceberg_detection())
