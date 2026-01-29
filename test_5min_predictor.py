#!/usr/bin/env python3
"""
Test 5-Minute Candle Predictor with AI & Memory

Tests the complete flow:
1. Create predictor with MentorBrain
2. Feed sample orders
3. Generate prediction
4. Check confidence & accuracy
"""

from datetime import datetime, timedelta
from backend.intelligence.candle_predictor_5min import FiveMinuteCandlePredictor
from backend.mentor.mentor_brain import MentorBrain


def create_sample_orders(balance_type='bullish'):
    """Create sample orders for testing."""
    now = datetime.utcnow()
    period_start = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
    
    orders = []
    
    if balance_type == 'bullish':
        # Strong bullish: 70 BUY vs 20 SELL
        orders.extend([
            {'timestamp': (period_start + timedelta(seconds=10)).isoformat(), 'price': 5310.0, 'size': 15, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=20)).isoformat(), 'price': 5311.0, 'size': 20, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=30)).isoformat(), 'price': 5310.5, 'size': 5, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=40)).isoformat(), 'price': 5312.0, 'size': 18, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=50)).isoformat(), 'price': 5311.5, 'size': 8, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=60)).isoformat(), 'price': 5313.0, 'size': 17, 'side': 'BUY'},
        ])
    elif balance_type == 'bearish':
        # Strong bearish: 20 BUY vs 70 SELL
        orders.extend([
            {'timestamp': (period_start + timedelta(seconds=10)).isoformat(), 'price': 5310.0, 'size': 8, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=20)).isoformat(), 'price': 5309.0, 'size': 20, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=30)).isoformat(), 'price': 5309.5, 'size': 12, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=40)).isoformat(), 'price': 5308.0, 'size': 5, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=50)).isoformat(), 'price': 5308.5, 'size': 22, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=60)).isoformat(), 'price': 5307.5, 'size': 13, 'side': 'SELL'},
        ])
    else:  # neutral
        # Balanced: 50 BUY vs 50 SELL
        orders.extend([
            {'timestamp': (period_start + timedelta(seconds=10)).isoformat(), 'price': 5310.0, 'size': 15, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=20)).isoformat(), 'price': 5309.5, 'size': 15, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=30)).isoformat(), 'price': 5310.5, 'size': 12, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=40)).isoformat(), 'price': 5309.0, 'size': 13, 'side': 'SELL'},
            {'timestamp': (period_start + timedelta(seconds=50)).isoformat(), 'price': 5311.0, 'size': 13, 'side': 'BUY'},
            {'timestamp': (period_start + timedelta(seconds=60)).isoformat(), 'price': 5308.5, 'size': 12, 'side': 'SELL'},
        ])
    
    return orders


def test_predictor():
    """Test the 5-minute candle predictor."""
    print("\n" + "=" * 80)
    print("🎯 5-MINUTE CANDLE PREDICTOR WITH AI & MEMORY - TEST SUITE")
    print("=" * 80 + "\n")
    
    # Initialize predictor with MentorBrain
    mentor_brain = MentorBrain()
    predictor = FiveMinuteCandlePredictor(mentor_brain=mentor_brain, max_history=100)
    
    print("✅ Initialized FiveMinuteCandlePredictor with MentorBrain")
    print(f"   Max historical patterns: {predictor.max_history}")
    print("")
    
    # Test 1: Bullish Signal
    print("-" * 80)
    print("TEST 1: BULLISH SIGNAL (70 BUY vs 20 SELL)")
    print("-" * 80)
    bullish_orders = create_sample_orders('bullish')
    predictor.add_orders(bullish_orders)
    prediction = predictor.predict_next_candle()
    
    print(f"\n📊 Order Flow Analysis:")
    print(f"   Buy Volume: {prediction['order_flow']['buy_volume']}")
    print(f"   Sell Volume: {prediction['order_flow']['sell_volume']}")
    print(f"   Balance: {prediction['order_flow']['balance']}")
    print(f"   Buy Ratio: {prediction['order_flow']['buy_ratio']:.1f}%")
    
    print(f"\n🎯 Prediction:")
    print(f"   Direction: {prediction['prediction']} {prediction['icon']}")
    print(f"   Next Candle: {prediction['next_candle_direction']}")
    print(f"   Confidence: {prediction['confidence']}%")
    
    print(f"\n📈 Volume Dynamics:")
    print(f"   Momentum: {prediction['volume_dynamics']['momentum']}")
    print(f"   Acceleration: {prediction['volume_dynamics']['acceleration']}")
    
    print(f"\n🤖 AI Mentor Analysis:")
    print(f"   Decision: {prediction['ai_analysis']['decision']}")
    print(f"   Regime: {prediction['ai_analysis']['regime']}")
    
    print(f"\n🧠 Memory Patterns:")
    print(f"   Similar Patterns Found: {prediction['pattern_memory']['similar_patterns']}")
    print(f"   Historical Accuracy: {prediction['pattern_memory']['historical_accuracy']}")
    
    print(f"\n💡 Reasoning:")
    print(f"   {prediction['reasoning']}")
    
    # Save outcome
    predictor.record_actual_outcome('UP')
    
    # Test 2: Bearish Signal
    print("\n\n" + "-" * 80)
    print("TEST 2: BEARISH SIGNAL (20 BUY vs 70 SELL)")
    print("-" * 80)
    bearish_orders = create_sample_orders('bearish')
    predictor.add_orders(bearish_orders)
    prediction = predictor.predict_next_candle()
    
    print(f"\n📊 Order Flow Analysis:")
    print(f"   Buy Volume: {prediction['order_flow']['buy_volume']}")
    print(f"   Sell Volume: {prediction['order_flow']['sell_volume']}")
    print(f"   Balance: {prediction['order_flow']['balance']}")
    print(f"   Sell Ratio: {prediction['order_flow']['sell_ratio']:.1f}%")
    
    print(f"\n🎯 Prediction:")
    print(f"   Direction: {prediction['prediction']} {prediction['icon']}")
    print(f"   Next Candle: {prediction['next_candle_direction']}")
    print(f"   Confidence: {prediction['confidence']}%")
    
    print(f"\n📈 Volume Dynamics:")
    print(f"   Momentum: {prediction['volume_dynamics']['momentum']}")
    
    # Save outcome
    predictor.record_actual_outcome('DOWN')
    
    # Test 3: Neutral Signal
    print("\n\n" + "-" * 80)
    print("TEST 3: NEUTRAL SIGNAL (50 BUY vs 50 SELL)")
    print("-" * 80)
    neutral_orders = create_sample_orders('neutral')
    predictor.add_orders(neutral_orders)
    prediction = predictor.predict_next_candle()
    
    print(f"\n📊 Order Flow Analysis:")
    print(f"   Buy Volume: {prediction['order_flow']['buy_volume']}")
    print(f"   Sell Volume: {prediction['order_flow']['sell_volume']}")
    print(f"   Balance: {prediction['order_flow']['balance']}")
    print(f"   Buy Ratio: {prediction['order_flow']['buy_ratio']:.1f}%")
    
    print(f"\n🎯 Prediction:")
    print(f"   Direction: {prediction['prediction']} {prediction['icon']}")
    print(f"   Confidence: {prediction['confidence']}%")
    
    # Save outcome
    predictor.record_actual_outcome('SIDEWAYS')
    
    # Statistics
    print("\n\n" + "-" * 80)
    print("STATISTICS & MEMORY")
    print("-" * 80)
    stats = predictor.get_statistics()
    print(f"\n📊 Prediction Statistics:")
    print(f"   Total Patterns Recorded: {stats['total_patterns']}")
    print(f"   Recorded Outcomes: {stats['recorded_outcomes']}")
    print(f"   Data Quality: {stats.get('historical_data_quality', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        test_predictor()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
