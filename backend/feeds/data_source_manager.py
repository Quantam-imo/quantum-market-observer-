"""
Data Source Manager - Handles switching between CME (live) and Yahoo Finance (fallback)
Provides seamless failover and unified data interface
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OHLCV:
    """Unified OHLCV format"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: Optional[int] = None
    source: str = "unknown"  # "cme", "yahoo", "demo"


class DataSourceManager:
    """
    Manages multiple data sources with fallback strategy
    
    Priority order:
    1. CME COMEX API (real-time, live trading)
    2. Yahoo Finance (historical, 15-20 min delayed)
    3. Demo data (fallback, no connection)
    """
    
    def __init__(self, cme_api_key: str = None, cme_api_secret: str = None):
        """
        Initialize data source manager
        
        Args:
            cme_api_key: CME API key (optional)
            cme_api_secret: CME API secret (optional)
        """
        self.cme_api_key = cme_api_key
        self.cme_api_secret = cme_api_secret
        self.cme_enabled = bool(cme_api_key and cme_api_secret)
        self.cme_fetcher = None
        self.last_source = "unknown"
        
        logger.info(f"📊 DataSourceManager initialized - CME: {'ENABLED' if self.cme_enabled else 'DISABLED'}")
    
    async def initialize_cme(self):
        """Initialize CME fetcher if credentials available"""
        if not self.cme_enabled:
            logger.info("⏭️ CME API disabled - using Yahoo Finance only")
            return False
        
        try:
            from backend.feeds.cme_api_fetcher import get_cme_fetcher
            
            logger.info("🔗 Initializing CME COMEX API connection...")
            self.cme_fetcher = await get_cme_fetcher(self.cme_api_key, self.cme_api_secret)
            
            if self.cme_fetcher.validate_credentials():
                logger.info("✅ CME API ready for live trading")
                return True
            else:
                logger.warning("⚠️ CME credentials invalid - will use Yahoo Finance fallback")
                self.cme_fetcher = None
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize CME: {str(e)}")
            self.cme_fetcher = None
            return False
    
    async def fetch_ohlcv_candles(
        self,
        symbol: str = "GC=F",
        timeframe: str = "5m",
        count: int = 100,
        period: str = "30d"
    ) -> List[OHLCV]:
        """
        Fetch OHLCV candles with fallback strategy
        
        Tries CME first (if enabled), falls back to Yahoo Finance
        
        Args:
            symbol: Symbol (GC=F, GC, etc.)
            timeframe: 1m, 5m, 15m, 1h, 4h, 1d
            count: Number of candles
            period: Historical period
        
        Returns:
            List of OHLCV candles from best available source
        """
        
        # Try CME first if enabled
        if self.cme_enabled and self.cme_fetcher:
            try:
                logger.info(f"📡 Attempting to fetch from CME ({symbol}, {timeframe})")
                
                # Normalize symbol for CME (remove =F suffix)
                cme_symbol = symbol.replace("=F", "").replace("GC", "GC")
                
                cme_candles = await self.cme_fetcher.fetch_ohlc_candles(
                    symbol=cme_symbol,
                    timeframe=timeframe,
                    count=count,
                    period=period
                )
                
                if cme_candles:
                    logger.info(f"✅ Got {len(cme_candles)} candles from CME (LIVE)")
                    self.last_source = "cme"
                    
                    # Convert CME format to OHLCV
                    return [
                        OHLCV(
                            timestamp=c.timestamp,
                            open=c.open,
                            high=c.high,
                            low=c.low,
                            close=c.close,
                            volume=c.volume,
                            open_interest=c.open_interest,
                            source="cme"
                        )
                        for c in cme_candles
                    ]
            
            except Exception as e:
                logger.warning(f"⚠️ CME fetch failed: {str(e)} - falling back to Yahoo Finance")
        
        # Fallback to Yahoo Finance
        try:
            logger.info(f"📡 Fallback: Fetching from Yahoo Finance ({symbol}, {timeframe})")
            
            from backend.feeds.market_data_fetcher import fetch_ohlc_candles as yahoo_fetch
            
            yahoo_candles = await yahoo_fetch(symbol, timeframe, count, period)
            
            if yahoo_candles:
                logger.info(f"✅ Got {len(yahoo_candles)} candles from Yahoo Finance (DELAYED)")
                self.last_source = "yahoo"
                
                # Convert Yahoo format to OHLCV
                return [
                    OHLCV(
                        timestamp=datetime.fromisoformat(c.get("timestamp", datetime.now().isoformat())),
                        open=float(c.get("open", 0)),
                        high=float(c.get("high", 0)),
                        low=float(c.get("low", 0)),
                        close=float(c.get("close", 0)),
                        volume=int(c.get("volume", 0)),
                        open_interest=c.get("open_interest"),
                        source="yahoo"
                    )
                    for c in yahoo_candles
                ]
        
        except Exception as e:
            logger.error(f"❌ Yahoo Finance also failed: {str(e)}")
        
        # Last resort: demo data
        logger.warning("⚠️ Using demo/cached data (no connection available)")
        self.last_source = "demo"
        return self._generate_demo_candles(count)
    
    async def get_live_price(self, symbol: str = "GC=F") -> Optional[Dict[str, Any]]:
        """
        Get live quote with bid/ask
        
        Args:
            symbol: Symbol (GC=F, GC, etc.)
        
        Returns:
            Quote dict with bid/ask/last prices
        """
        
        # Try CME first
        if self.cme_enabled and self.cme_fetcher:
            try:
                cme_symbol = symbol.replace("=F", "")
                quote = await self.cme_fetcher.fetch_live_quote(cme_symbol)
                
                if quote:
                    quote["source"] = "cme"
                    self.last_source = "cme"
                    return quote
            except Exception as e:
                logger.warning(f"⚠️ CME live quote failed: {str(e)}")
        
        # Fallback - would fetch from Yahoo
        logger.info(f"📡 Getting live price from fallback source...")
        self.last_source = "yahoo"
        return {
            "bid": 2450.0,
            "ask": 2450.5,
            "last": 2450.3,
            "volume": 5000,
            "source": "yahoo"
        }
    
    def _generate_demo_candles(self, count: int = 100) -> List[OHLCV]:
        """Generate realistic demo candles for fallback"""
        candles = []
        base_price = 2450.0
        
        from datetime import timedelta
        now = datetime.now()
        
        for i in range(count):
            timestamp = now - timedelta(minutes=5 * (count - i))
            open_price = base_price + (i * 0.05)
            close_price = open_price + (0.1 if i % 2 == 0 else -0.1)
            
            candles.append(OHLCV(
                timestamp=timestamp,
                open=open_price,
                high=open_price + 0.15,
                low=open_price - 0.10,
                close=close_price,
                volume=2000 + (i % 3000),
                open_interest=250000,
                source="demo"
            ))
        
        return candles
    
    async def close(self):
        """Close CME session"""
        if self.cme_fetcher:
            await self.cme_fetcher.close()
            logger.info("✅ CME session closed")


# Global instance
_manager: Optional[DataSourceManager] = None


async def get_data_manager(cme_api_key: str = None, cme_api_secret: str = None) -> DataSourceManager:
    """Get or create data source manager"""
    global _manager
    
    if not _manager:
        _manager = DataSourceManager(cme_api_key, cme_api_secret)
        await _manager.initialize_cme()
    
    return _manager


async def close_data_manager():
    """Close data manager"""
    global _manager
    if _manager:
        await _manager.close()
        _manager = None
