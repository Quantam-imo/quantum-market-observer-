def orderflow_bias(ladder, current_price):
    level = ladder.get(current_price)
    if not level:
        return None
    if level["absorbed"] and level["sell_qty"] > level["buy_qty"]:
        return {
            "bias": "SELL",
            "confidence_boost": 0.20,
            "reason": "Sell absorption at current price"
        }
    if level["absorbed"] and level["buy_qty"] > level["sell_qty"]:
        return {
            "bias": "BUY",
            "confidence_boost": 0.20,
            "reason": "Buy absorption at current price"
        }
    return None
