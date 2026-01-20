def evaluate_iceberg(zone, future_prices, min_move=15):
    entry = (zone["price_low"] + zone["price_high"]) / 2

    max_up = max(future_prices) - entry
    max_down = entry - min(future_prices)

    if zone["side"] == "SELL" and max_down >= min_move:
        return "SUCCESS"
    if zone["side"] == "BUY" and max_up >= min_move:
        return "SUCCESS"

    return "FAIL"
