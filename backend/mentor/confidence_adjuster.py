def iceberg_confidence_boost(zone_score):
    if zone_score >= 3:
        return 0.15
    if zone_score == 2:
        return 0.10
    if zone_score == 1:
        return 0.05
    if zone_score <= -1:
        return -0.10
    return 0.0
