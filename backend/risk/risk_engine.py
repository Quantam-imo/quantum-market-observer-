# backend/risk/risk_engine.py

class RiskEngine:
    def __init__(self, account_balance):
        self.balance = account_balance
        self.daily_loss = 0
        self.max_daily_loss = 0.015 * account_balance
        self.loss_streak = 0

    def register_trade(self, pnl):
        self.daily_loss += max(0, -pnl)

        if pnl < 0:
            self.loss_streak += 1
        else:
            self.loss_streak = 0

    def can_trade(self):
        if self.daily_loss >= self.max_daily_loss:
            return False
        if self.loss_streak >= 3:
            return False
        return True
