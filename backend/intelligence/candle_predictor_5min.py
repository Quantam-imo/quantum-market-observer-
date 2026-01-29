"""
5-Minute Candle Predictor with AI & Memory Integration

Analyzes order flow WITHIN a 5-minute candle period:
- Volume progression tracking
- Order flow strength through the period
- AI-powered pattern recognition
- Historical memory pattern matching
- Confidence scoring based on multiple factors
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import math
import json


class FiveMinuteCandlePredictor:
    """
    Analyzes orders within 5-minute periods to predict next candle direction.
    Uses real order flow volume analysis combined with AI insights and memory patterns.
    """

    def __init__(self, mentor_brain=None, max_history=100):
        """
        Initialize 5-minute predictor.
        
        Args:
            mentor_brain: MentorBrain instance for AI analysis
            max_history: Number of past 5-min patterns to remember
        """
        self.mentor_brain = mentor_brain
        self.max_history = max_history
        
        # Current 5-minute period tracking
        self.current_period_start = None
        self.period_orders = []  # Orders in current 5-min period only
        self.volume_timeline = deque(maxlen=300)  # Second-by-second volume tracking
        
        # Historical patterns for memory-based prediction
        self.historical_patterns = deque(maxlen=max_history)
        
        # Prediction cache
        self.last_prediction = None
        self.prediction_updated_at = None

    def get_5min_period_start(self, timestamp: datetime) -> datetime:
        """Get the start time of the 5-minute period containing this timestamp."""
        # Floor to nearest 5-minute boundary
        minute = timestamp.minute
        period_minute = (minute // 5) * 5
        
        return timestamp.replace(
            minute=period_minute,
            second=0,
            microsecond=0
        )

    def add_orders(self, orders: List[Dict[str, Any]]) -> None:
        """
        Add orders to current 5-minute period.
        Automatically resets when period boundary is crossed.
        
        Args:
            orders: List of order dicts with timestamp, price, size, side
        """
        if not orders:
            return

        now = datetime.utcnow()
        current_period_start = self.get_5min_period_start(now)
        
        # Reset if period changed
        if (self.current_period_start is None or 
            current_period_start > self.current_period_start):
            
            # Save previous period to history if it had data
            if self.period_orders and self.current_period_start is not None:
                self._save_period_pattern()
            
            self.current_period_start = current_period_start
            self.period_orders = []
            self.volume_timeline = deque(maxlen=300)
        
        # Filter and add orders from current 5-minute period
        for order in orders:
            try:
                order_time = datetime.fromisoformat(order.get('timestamp', ''))
                # Only include orders within current 5-minute period
                period_end = self.current_period_start + timedelta(minutes=5)
                if self.current_period_start <= order_time < period_end:
                    # Avoid duplicates
                    if order not in self.period_orders:
                        self.period_orders.append(order)
                        self._update_volume_timeline(order, order_time)
            except (ValueError, TypeError):
                # Skip malformed timestamps
                continue

    def _update_volume_timeline(self, order: Dict, timestamp: datetime) -> None:
        """Track volume progression second-by-second through the period."""
        if self.current_period_start is None:
            return
        # Determine which second within the 5-minute period (0-299)
        seconds_into_period = (timestamp - self.current_period_start).total_seconds()
        if 0 <= seconds_into_period < 300:
            side = order.get('side', 'BUY')
            size = order.get('size', 0)
            self.volume_timeline.append({
                'second': int(seconds_into_period),
                'side': side,
                'volume': size,
                'timestamp': timestamp.isoformat()
            })

    def predict_next_candle(self) -> Dict[str, Any]:
        """
        Predict the next 5-minute candle direction based on:
        1. Current period order flow volume
        2. Volume progression/acceleration
        3. AI analysis via MentorBrain
        4. Pattern matching from historical memory
        
        Returns:
            Dict with prediction, confidence, reasoning, etc.
        """
        if not self.period_orders:
            return self._neutral_prediction("No orders in current period")
        
        # Analyze order flow within this 5-minute period
        analysis = self._analyze_5min_orderflow()
        
        # Get AI insights from MentorBrain
        ai_insights = self._get_ai_insights(analysis)
        
        # Check historical patterns for similarity
        pattern_match = self._find_matching_patterns(analysis)
        
        # Synthesize final prediction
        prediction = self._synthesize_prediction(analysis, ai_insights, pattern_match)
        
        self.last_prediction = prediction
        self.prediction_updated_at = datetime.utcnow()
        
        return prediction

    def _analyze_5min_orderflow(self) -> Dict[str, Any]:
        """Analyze order flow within the 5-minute period."""
        if not self.period_orders:
            return {}
        
        # Separate BUY and SELL orders
        buy_orders = [o for o in self.period_orders if o.get('side') == 'BUY']
        sell_orders = [o for o in self.period_orders if o.get('side') == 'SELL']
        
        # Calculate volumes
        buy_volume = sum(o.get('size', 0) for o in buy_orders)
        sell_volume = sum(o.get('size', 0) for o in sell_orders)
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return {'balance': 0, 'buy_volume': 0, 'sell_volume': 0}
        
        # Balance and ratios
        balance = buy_volume - sell_volume
        buy_ratio = buy_volume / total_volume * 100
        sell_ratio = sell_volume / total_volume * 100
        
        # Volume progression (is volume accelerating?)
        volume_acceleration = self._calculate_acceleration()
        
        # Time-weighted volume (orders arriving later have more weight)
        time_weighted_buy = self._calculate_time_weighted_volume(buy_orders)
        time_weighted_sell = self._calculate_time_weighted_volume(sell_orders)
        
        # Average order size (bigger orders = more conviction)
        avg_buy_size = buy_volume / len(buy_orders) if buy_orders else 0
        avg_sell_size = sell_volume / len(sell_orders) if sell_orders else 0
        
        return {
            'total_orders': len(self.period_orders),
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_volume': total_volume,
            'balance': balance,
            'buy_ratio': buy_ratio,
            'sell_ratio': sell_ratio,
            'balance_ratio': abs(balance) / total_volume * 100 if total_volume > 0 else 0,
            'volume_acceleration': volume_acceleration,
            'time_weighted_buy': time_weighted_buy,
            'time_weighted_sell': time_weighted_sell,
            'avg_buy_size': avg_buy_size,
            'avg_sell_size': avg_sell_size,
            'order_flow_momentum': self._calculate_momentum(),
            'volume_distribution': self._analyze_volume_distribution(),
        }

    def _calculate_acceleration(self) -> float:
        """Calculate if volume is accelerating or decelerating."""
        if len(self.period_orders) < 4:
            return 0.0
        
        # Compare early vs late volume
        mid_point = len(self.period_orders) // 2
        early_orders = self.period_orders[:mid_point]
        late_orders = self.period_orders[mid_point:]
        
        early_vol = sum(o.get('size', 0) for o in early_orders)
        late_vol = sum(o.get('size', 0) for o in late_orders)
        
        if early_vol == 0:
            return 0.0
        
        # Positive = accelerating, negative = decelerating
        return (late_vol - early_vol) / early_vol

    def _calculate_time_weighted_volume(self, orders: List[Dict]) -> float:
        """Assign higher weight to orders arriving later in the period."""
        if not orders:
            return 0.0
        
        total_weighted = 0.0
        for i, order in enumerate(orders):
            # Weight increases from 0.5 to 1.5 across the period
            weight = 0.5 + (i / len(orders)) if orders else 0.5
            total_weighted += order.get('size', 0) * weight
        
        return total_weighted

    def _calculate_momentum(self) -> str:
        """Determine if order flow momentum is building or declining."""
        if len(self.volume_timeline) < 5:
            return "BUILDING"
        
        # Look at recent vs earlier volume in timeline
        mid = len(self.volume_timeline) // 2
        recent = list(self.volume_timeline)[mid:]
        earlier = list(self.volume_timeline)[:mid]
        
        recent_volume = sum(v.get('volume', 0) for v in recent)
        earlier_volume = sum(v.get('volume', 0) for v in earlier)
        
        if recent_volume > earlier_volume * 1.2:
            return "ACCELERATING"
        elif recent_volume < earlier_volume * 0.8:
            return "DECELERATING"
        else:
            return "STEADY"

    def _analyze_volume_distribution(self) -> Dict[str, Any]:
        """Analyze how volume is distributed across the 5-minute period."""
        if not self.volume_timeline:
            return {}
        
        # Group by periods (0-60s, 60-120s, etc.)
        periods = {}
        for entry in self.volume_timeline:
            second = entry.get('second', 0)
            period_key = second // 60  # 0-4 for 5-minute period
            
            if period_key not in periods:
                periods[period_key] = {'buy': 0, 'sell': 0}
            
            if entry.get('side') == 'BUY':
                periods[period_key]['buy'] += entry.get('volume', 0)
            else:
                periods[period_key]['sell'] += entry.get('volume', 0)
        
        return periods

    def _get_ai_insights(self, analysis: Dict) -> Dict[str, Any]:
        """Use MentorBrain for AI-powered prediction insights."""
        if not self.mentor_brain:
            return {'available': False, 'reason': 'No MentorBrain instance'}
        
        # Prepare context for MentorBrain
        ctx = {
            'qmo': {
                'signal_type': 'ORDER_FLOW_5MIN',
                'balance': analysis.get('balance', 0),
                'buy_ratio': analysis.get('buy_ratio', 50),
                'volume_momentum': analysis.get('order_flow_momentum', 'STEADY'),
                'volume_acceleration': analysis.get('volume_acceleration', 0),
            },
            'imo': {  # Incoming market observation
                'total_volume': analysis.get('total_volume', 0),
                'distribution': analysis.get('volume_distribution', {}),
            },
            'confidence': self._calculate_base_confidence(analysis),
            'confirmations': self._count_confirmations(analysis),
        }
        
        try:
            decision = self.mentor_brain.decide(ctx)
            return {
                'available': True,
                'decision': decision.get('decision', 'UNKNOWN'),
                'confidence_boost': 0.1 if decision.get('decision') == 'EXECUTE' else 0,
                'regime': decision.get('regime', 'UNKNOWN'),
                'reasoning': f"AI analysis: {decision}",
            }
        except Exception as e:
            return {'available': True, 'error': str(e), 'reasoning': 'AI analysis error'}

    def _calculate_base_confidence(self, analysis: Dict) -> float:
        """Calculate base confidence from order flow analysis."""
        balance_ratio = analysis.get('balance_ratio', 0)
        
        # Confidence based on how imbalanced the orders are
        if balance_ratio >= 40:
            return 0.95
        elif balance_ratio >= 30:
            return 0.85
        elif balance_ratio >= 20:
            return 0.75
        elif balance_ratio >= 10:
            return 0.65
        else:
            return 0.50

    def _count_confirmations(self, analysis: Dict) -> int:
        """Count confirmation signals from the order flow."""
        confirmations = 0
        
        # Confirmation 1: Strong imbalance
        if abs(analysis.get('balance', 0)) >= 20:
            confirmations += 1
        
        # Confirmation 2: Volume acceleration
        if analysis.get('volume_acceleration', 0) > 0.2:
            confirmations += 1
        
        # Confirmation 3: Order size consistency
        avg_buy = analysis.get('avg_buy_size', 0)
        avg_sell = analysis.get('avg_sell_size', 0)
        if avg_buy > 0 and avg_sell > 0:
            size_ratio = max(avg_buy, avg_sell) / min(avg_buy, avg_sell)
            if size_ratio < 2:  # Sizes are similar = consistent trading
                confirmations += 1
        
        # Confirmation 4: Momentum building
        if analysis.get('order_flow_momentum') == 'ACCELERATING':
            confirmations += 1
        
        return min(confirmations, 4)  # Max 4 confirmations

    def _find_matching_patterns(self, current_analysis: Dict) -> Dict[str, Any]:
        """Find similar historical patterns and their outcomes."""
        if not self.historical_patterns:
            return {'match_found': False, 'similar_patterns': 0}
        
        matching_patterns = []
        current_balance = current_analysis.get('balance', 0)
        current_ratio = current_analysis.get('balance_ratio', 0)
        
        for pattern in self.historical_patterns:
            # Find patterns with similar balance ratio
            pattern_ratio = pattern.get('balance_ratio', 0)
            
            if abs(current_ratio - pattern_ratio) < 15:  # Within 15% similarity
                matching_patterns.append(pattern)
        
        if not matching_patterns:
            return {'match_found': False, 'similar_patterns': 0}
        
        # Analyze outcomes of matching patterns
        positive_outcomes = sum(1 for p in matching_patterns if p.get('actual_direction') == 'UP')
        total_patterns = len(matching_patterns)
        success_rate = positive_outcomes / total_patterns * 100 if total_patterns > 0 else 0
        
        return {
            'match_found': True,
            'similar_patterns': total_patterns,
            'historical_success_rate': success_rate,
            'historical_accuracy': f"{success_rate:.1f}%",
            'memory_confidence': 0.05 * (total_patterns / 100),  # Up to 5% boost from memory
        }

    def _synthesize_prediction(
        self,
        analysis: Dict,
        ai_insights: Dict,
        pattern_match: Dict
    ) -> Dict[str, Any]:
        """Synthesize final prediction from all signals."""
        
        balance = analysis.get('balance', 0)
        balance_ratio = analysis.get('balance_ratio', 0)
        total_volume = analysis.get('total_volume', 0)
        
        # Determine direction
        if balance > 0:
            direction = 'BULLISH'
            color = '#3fb950'  # Green
            icon = '🟢'
        elif balance < 0:
            direction = 'BEARISH'
            color = '#f85149'  # Red
            icon = '🔴'
        else:
            direction = 'NEUTRAL'
            color = '#9ca3af'  # Gray
            icon = '⚪'
        
        # Calculate confidence from multiple sources
        base_confidence = self._calculate_base_confidence(analysis)
        
        # AI boost
        ai_boost = ai_insights.get('confidence_boost', 0)
        
        # Pattern memory boost
        pattern_boost = pattern_match.get('memory_confidence', 0)
        
        # Momentum boost
        momentum_boost = 0.05 if analysis.get('order_flow_momentum') == 'ACCELERATING' else 0
        
        # Final confidence (capped at 0.95)
        final_confidence = min(
            base_confidence + ai_boost + pattern_boost + momentum_boost,
            0.95
        )
        
        return {
            'period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'prediction': direction,
            'next_candle_direction': f"{direction} ⬆️" if balance > 0 else f"{direction} ⬇️" if balance < 0 else f"{direction} ↔️",
            'color': color,
            'icon': icon,
            'confidence': int(final_confidence * 100),
            'confidence_decimal': round(final_confidence, 2),
            
            # Order flow details
            'order_flow': {
                'total_orders': analysis.get('total_orders', 0),
                'buy_volume': analysis.get('buy_volume', 0),
                'sell_volume': analysis.get('sell_volume', 0),
                'balance': analysis.get('balance', 0),
                'buy_ratio': round(analysis.get('buy_ratio', 0), 1),
                'sell_ratio': round(analysis.get('sell_ratio', 0), 1),
            },
            
            # Volume dynamics
            'volume_dynamics': {
                'momentum': analysis.get('order_flow_momentum', 'STEADY'),
                'acceleration': round(analysis.get('volume_acceleration', 0), 2),
                'distribution': analysis.get('volume_distribution', {}),
            },
            
            # AI analysis
            'ai_analysis': {
                'decision': ai_insights.get('decision'),
                'regime': ai_insights.get('regime'),
            },
            
            # Historical memory
            'pattern_memory': {
                'similar_patterns': pattern_match.get('similar_patterns', 0),
                'historical_accuracy': pattern_match.get('historical_accuracy', 'N/A'),
            },
            
            'timestamp': datetime.utcnow().isoformat(),
            'reasoning': self._generate_reasoning(analysis, ai_insights, pattern_match, direction),
        }

    def _generate_reasoning(
        self,
        analysis: Dict,
        ai_insights: Dict,
        pattern_match: Dict,
        direction: str
    ) -> str:
        """Generate human-readable reasoning for the prediction."""
        reasons = []
        
        # Order flow reason
        buy_vol = analysis.get('buy_volume', 0)
        sell_vol = analysis.get('sell_volume', 0)
        
        if direction == 'BULLISH':
            reasons.append(f"Strong buy bias: {buy_vol} BUY vs {sell_vol} SELL contracts")
        elif direction == 'BEARISH':
            reasons.append(f"Strong sell pressure: {sell_vol} SELL vs {buy_vol} BUY contracts")
        else:
            reasons.append(f"Balanced orders: {buy_vol} BUY vs {sell_vol} SELL")
        
        # Momentum reason
        momentum = analysis.get('order_flow_momentum', 'STEADY')
        if momentum == 'ACCELERATING':
            reasons.append(f"Volume {momentum.lower()}: orders building conviction")
        elif momentum == 'DECELERATING':
            reasons.append(f"Volume {momentum.lower()}: orders losing momentum")
        
        # AI reason
        if ai_insights.get('decision') == 'EXECUTE':
            reasons.append("AI analysis confirms signal strength")
        
        # Memory reason
        if pattern_match.get('match_found'):
            accuracy = pattern_match.get('historical_accuracy', 'N/A')
            reasons.append(f"Similar patterns succeeded {accuracy} of the time")
        
        return " | ".join(reasons)

    def _save_period_pattern(self) -> None:
        """Save the completed 5-minute period to historical memory."""
        if not self.period_orders:
            return
        
        analysis = self._analyze_5min_orderflow()
        
        if self.current_period_start is not None:
            period_start = self.current_period_start.isoformat()
            period_end = (self.current_period_start + timedelta(minutes=5)).isoformat()
        else:
            period_start = None
            period_end = None
        pattern = {
            'period_start': period_start,
            'period_end': period_end,
            'balance_ratio': analysis.get('balance_ratio', 0),
            'buy_volume': analysis.get('buy_volume', 0),
            'sell_volume': analysis.get('sell_volume', 0),
            'order_count': analysis.get('total_orders', 0),
            'momentum': analysis.get('order_flow_momentum', 'STEADY'),
            'actual_direction': None,  # To be filled by external feedback
            'stored_at': datetime.utcnow().isoformat(),
        }
        self.historical_patterns.append(pattern)

    def _neutral_prediction(self, reason: str) -> Dict[str, Any]:
        """Return a neutral prediction."""
        return {
            'prediction': 'NEUTRAL',
            'next_candle_direction': 'NEUTRAL ↔️',
            'color': '#9ca3af',
            'icon': '⚪',
            'confidence': 50,
            'confidence_decimal': 0.50,
            'order_flow': {
                'total_orders': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'balance': 0,
            },
            'reasoning': reason,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def record_actual_outcome(self, actual_direction: str) -> None:
        """
        Record actual candle outcome for machine learning feedback.
        Call this after the 5-minute candle closes.
        
        Args:
            actual_direction: 'UP', 'DOWN', or 'SIDEWAYS'
        """
        if self.historical_patterns:
            # Update the most recent pattern with actual outcome
            self.historical_patterns[-1]['actual_direction'] = actual_direction

    def get_statistics(self) -> Dict[str, Any]:
        """Get prediction accuracy statistics from memory."""
        if not self.historical_patterns:
            return {
                'total_patterns': 0, 
                'recorded_outcomes': 0,
                'accuracy': 'No data collected yet'
            }
        
        correct_predictions = sum(
            1 for p in self.historical_patterns 
            if p.get('actual_direction') is not None
        )
        
        if correct_predictions == 0:
            return {
                'total_patterns': len(self.historical_patterns),
                'recorded_outcomes': 0,
                'accuracy': 'Outcomes not yet recorded',
            }
        
        return {
            'total_patterns': len(self.historical_patterns),
            'recorded_outcomes': correct_predictions,
            'historical_data_quality': f"{(correct_predictions/len(self.historical_patterns))*100:.1f}%",
        }
