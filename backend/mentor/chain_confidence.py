def chain_confidence_boost(chain):
    boost = 0.0

    if chain["occurrences"] >= 2:
        boost += 0.10
    if len(chain["sessions"]) >= 2:
        boost += 0.10
    if chain["occurrences"] >= 4:
        boost += 0.15

    return boost
