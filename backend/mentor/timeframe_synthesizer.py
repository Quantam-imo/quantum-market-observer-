def timeframe_alignment(htf, structure, ltf):
    if htf["trend"] != ltf["direction"]:
        return False
    if structure["bos_against_htf"]:
        return False
    return True
