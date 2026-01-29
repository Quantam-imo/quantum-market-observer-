# config.py

SYMBOL = "XAUUSD"
BASE_TIMEFRAME = "5m"
HTF = ["1H", "4H"]

ICEBERG_MIN_QTY = 3000
ICEBERG_RATIO = 3.0

CONFIDENCE_THRESHOLD = 0.70

# ==================== DATA SOURCE PRIORITY ====================
# 1. CME COMEX API (real-time, live trading) - if enabled & available
# 2. Yahoo Finance (fallback, 15-20 min delayed)
# 3. Demo data (no connection)

# ==================== CME GROUP COMEX API ====================
# For live COMEX Gold Futures trading
# Get credentials from: https://www.cmegroup.com/market-data/
CME_API_ENABLED = False  # Set to True when you have credentials
CME_API_KEY = ""         # Insert your CME API key
CME_API_SECRET = ""      # Insert your CME API secret
CME_ENDPOINT = "https://www.cmegroup.com/market-data/v3/"
CME_SYMBOL = "GC"        # Gold Futures contract

# ==================== YAHOO FINANCE (FALLBACK) ====================
# Free tier - no API key required
# Provides 15-20 min delayed data
# Used when CME API is unavailable
DATA_SOURCE = "Yahoo Finance (Fallback)"
YAHOO_SYMBOL = "GC=F"    # Gold Futures (COMEX)
YAHOO_INTERVAL = "5m"    # 5-minute candles

# ==================== DATA SOURCE CONFIGURATION ====================
DATA_SOURCES = {
    "primary": "cme" if CME_API_ENABLED else "yahoo",
    "fallback": "yahoo",
    "demo": "demo_data"
}

print(f"📊 Data Source Priority: {'CME → Yahoo → Demo' if CME_API_ENABLED else 'Yahoo → Demo'}")

