class RiskEngine:
    def can_trade(self, session_state):
        if session_state["locked"]:
            return False
        if session_state["losses"] >= 1:
            return False
        return True

    def position_size(self, balance, risk_pct, stop_points):
        risk_amount = balance * risk_pct
        return risk_amount / stop_points
