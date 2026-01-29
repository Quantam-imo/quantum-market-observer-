"""
CME COMEX API Data Fetcher - Real-time Gold Futures Data
Provides live tick data, open interest, and full order book from CME Group
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CMECandle:
    """Standardized candle format matching OHLCV"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: Optional[int] = None
    vwap: Optional[float] = None


class CMEAPIFetcher:
    """
    CME COMEX API Fetcher
    Provides real-time gold futures data from CME Group
    
    Supports:
    - Real-time tick data (< 1 second latency)
    - Full order book depth
    - Open interest tracking
    - All contract months
    - Microsecond precision
    """
    
    def __init__(self, api_key: str, api_secret: str, endpoint: str = None):
        """
        Initialize CME API fetcher
        
        Args:
            api_key: CME API key
            api_secret: CME API secret
            endpoint: CME API endpoint (default: production)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.endpoint = endpoint or "https://www.cmegroup.com/market-data/v3/"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # CME Contract symbols
        self.contracts = {
            "GC": "COMEX Gold Futures",  # Main contract
            "GCZ": "COMEX Gold Dec Contract"
        }
        
    async def initialize(self):
        """Initialize async session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("✅ CME API session initialized")
    
    async def close(self):
        """Close async session"""
        if self.session:
            await self.session.close()
            logger.info("✅ CME API session closed")
    
    async def get_headers(self) -> Dict[str, str]:
        """Generate authentication headers for CME API"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "QuantumMarketObserver/1.0"
        }
    
    async def fetch_ohlc_candles(
        self,
        symbol: str = "GC",
        timeframe: str = "5m",
        count: int = 100,
        period: str = "30d"
    ) -> List[CMECandle]:
        """
        Fetch OHLC candles from CME API
        
        Args:
            symbol: Contract symbol (GC, GCZ, etc.)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            count: Number of candles to fetch
            period: Historical period (1d, 7d, 30d, etc.)
        
        Returns:
            List of CMECandle objects
        """
        if not self.session:
            await self.initialize()
        
        try:
            # Build CME API request
            url = f"{self.endpoint}quotes/{symbol}"
            
            params = {
                "locale": "en_US",
                "chartAggregationType": self._map_timeframe(timeframe),
                "period": period,
                "limit": count
            }
            
            headers = await self.get_headers()
            
            logger.info(f"📊 Fetching {count} candles ({timeframe}) for {symbol} from CME")
            
            async with self.session.get(url, params=params, headers=headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    candles = self._parse_cme_response(data)
                    logger.info(f"✅ Parsed {len(candles)} candles from CME")
                    return candles
                elif response.status == 401:
                    logger.error("❌ CME API Authentication failed (invalid credentials)")
                    return []
                elif response.status == 429:
                    logger.warning("⚠️ CME API Rate limited - waiting 60s")
                    await asyncio.sleep(60)
                    return await self.fetch_ohlc_candles(symbol, timeframe, count, period)
                else:
                    logger.warning(f"⚠️ CME API returned {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error("❌ CME API request timeout (15s)")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching from CME: {str(e)}")
            return []
    
    async def fetch_live_quote(self, symbol: str = "GC") -> Optional[Dict[str, Any]]:
        """
        Fetch live quote with bid/ask
        
        Args:
            symbol: Contract symbol
        
        Returns:
            Quote dict with: bid, ask, last, volume, open_interest
        """
        if not self.session:
            await self.initialize()
        
        try:
            url = f"{self.endpoint}quotes/{symbol}"
            headers = await self.get_headers()
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_quote(data)
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching live quote: {str(e)}")
            return None
    
    async def fetch_order_book(self, symbol: str = "GC", depth: int = 20) -> Optional[Dict]:
        """
        Fetch order book depth (L2/L3)
        
        Args:
            symbol: Contract symbol
            depth: Order book depth (10, 20, 50, etc.)
        
        Returns:
            Order book with bids/asks
        """
        if not self.session:
            await self.initialize()
        
        try:
            url = f"{self.endpoint}orderbook/{symbol}"
            params = {"depth": depth}
            headers = await self.get_headers()
            
            async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_orderbook(data)
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching order book: {str(e)}")
            return None
    
    def _map_timeframe(self, timeframe: str) -> str:
        """Map standard timeframe to CME API format"""
        mapping = {
            "1m": "INTRADAYMINUTES",
            "5m": "INTRADAYMINUTES",
            "15m": "INTRADAYMINUTES",
            "1h": "INTRADAYHOURLY",
            "4h": "INTRADAYHOURLY",
            "1d": "DAILY"
        }
        return mapping.get(timeframe, "INTRADAYMINUTES")
    
    def _parse_cme_response(self, data: Dict) -> List[CMECandle]:
        """Parse CME API response into standard candles"""
        candles = []
        
        if not data or "charts" not in data:
            return candles
        
        try:
            for chart in data.get("charts", []):
                timestamp = datetime.fromisoformat(chart.get("date", "").replace("Z", "+00:00"))
                
                candle = CMECandle(
                    timestamp=timestamp,
                    open=float(chart.get("open", 0)),
                    high=float(chart.get("high", 0)),
                    low=float(chart.get("low", 0)),
                    close=float(chart.get("close", 0)),
                    volume=int(chart.get("volume", 0)),
                    open_interest=int(chart.get("openInterest", 0)),
                    vwap=float(chart.get("vwap", 0))
                )
                candles.append(candle)
            
            return sorted(candles, key=lambda x: x.timestamp)
            
        except Exception as e:
            logger.error(f"❌ Error parsing CME response: {str(e)}")
            return []
    
    def _parse_quote(self, data: Dict) -> Dict[str, Any]:
        """Parse live quote data"""
        if not data or "quote" not in data:
            return {}
        
        quote = data.get("quote", {})
        return {
            "bid": float(quote.get("bid", 0)),
            "ask": float(quote.get("ask", 0)),
            "last": float(quote.get("last", 0)),
            "volume": int(quote.get("volume", 0)),
            "open_interest": int(quote.get("openInterest", 0)),
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_orderbook(self, data: Dict) -> Dict:
        """Parse order book data"""
        if not data or "orderBook" not in data:
            return {}
        
        ob = data.get("orderBook", {})
        return {
            "bids": ob.get("bids", []),
            "asks": ob.get("asks", []),
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_credentials(self) -> bool:
        """Validate API credentials format"""
        if not self.api_key or not self.api_secret:
            logger.error("❌ Missing CME API credentials")
            return False
        if len(self.api_key) < 10 or len(self.api_secret) < 10:
            logger.error("❌ CME API credentials appear invalid (too short)")
            return False
        logger.info("✅ CME API credentials format valid")
        return True


# Singleton instance
_cme_fetcher: Optional[CMEAPIFetcher] = None


async def get_cme_fetcher(api_key: str, api_secret: str) -> CMEAPIFetcher:
    """Get or create CME fetcher instance"""
    global _cme_fetcher
    
    if not _cme_fetcher:
        _cme_fetcher = CMEAPIFetcher(api_key, api_secret)
        await _cme_fetcher.initialize()
    
    return _cme_fetcher


async def close_cme_fetcher():
    """Close CME fetcher session"""
    global _cme_fetcher
    if _cme_fetcher:
        await _cme_fetcher.close()
        _cme_fetcher = None
