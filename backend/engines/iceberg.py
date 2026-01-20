from config import ICEBERG_MIN_QTY, ICEBERG_RATIO

class IcebergEngine:
    def detect(self, price, buys, sells):
        if sells > ICEBERG_MIN_QTY and sells > buys * ICEBERG_RATIO:
            return {
                "type": "SELL_ABSORPTION",
                "price": price,
                "strength": sells - buys
            }
        if buys > ICEBERG_MIN_QTY and buys > sells * ICEBERG_RATIO:
            return {
                "type": "BUY_ABSORPTION",
                "price": price,
                "strength": buys - sells
            }
        return None
