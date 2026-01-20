class IMOAdapter:
    def liquidity_taken(self, structure):
        return structure.get("sweep", False)
