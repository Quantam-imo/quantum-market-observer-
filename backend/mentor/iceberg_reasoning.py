def iceberg_context(current_price, memory_zones):
    for zone in memory_zones:
        if zone["price_low"] <= current_price <= zone["price_high"]:
            return {
                "bias": zone["side"],
                "confidence_boost": 0.15,
                "reason": "Returning to prior iceberg zone"
            }
    return None
