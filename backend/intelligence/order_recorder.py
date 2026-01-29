"""
Raw Order Recorder - Capture live orders at tick level before chart formation
Records: timestamp, price, size, side (buy/sell)
Storage: SQLite for persistence and queryability
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import threading
from collections import deque

DB_PATH = Path(__file__).parent.parent.parent / "data" / "orders.db"


class RawOrderRecorder:
    """Record and query raw orders at tick level"""
    
    def __init__(self, db_path: Path = DB_PATH, max_memory: int = 10000, auto_cleanup_days: int = 15):
        self.db_path = db_path
        self.max_memory = max_memory
        self.auto_cleanup_days = auto_cleanup_days  # Days to retain data
        self.memory_orders = deque(maxlen=max_memory)  # Recent orders in memory
        self.lock = threading.Lock()
        self._init_db()
        self._load_memory_from_db()  # Load existing orders into memory
        
        # Run automatic cleanup on startup (delete orders older than retention period)
        if self.auto_cleanup_days > 0:
            self.auto_cleanup_on_startup(self.auto_cleanup_days)
    
    def _init_db(self):
        """Initialize SQLite database for order persistence"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create orders table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                price REAL NOT NULL,
                size INTEGER NOT NULL,
                side TEXT NOT NULL,  -- 'BUY' or 'SELL'
                contract_type TEXT DEFAULT 'ES',  -- E-mini S&P 500 default
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON orders(timestamp DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price 
            ON orders(price)
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_memory_from_db(self):
        """Load recent orders from database into memory on startup"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Load last 10,000 orders (or max_memory) into memory
            cursor.execute('''
                SELECT timestamp, price, size, side, contract_type
                FROM orders
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (self.max_memory,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Load in chronological order (reverse of DESC order)
            with self.lock:
                for row in reversed(rows):
                    self.memory_orders.append({
                        "timestamp": row[0],
                        "price": row[1],
                        "size": row[2],
                        "side": row[3],
                        "contract_type": row[4]
                    })
            
            print(f"✅ Loaded {len(self.memory_orders)} orders into memory from database")
        except Exception as e:
            print(f"⚠️ Could not load orders into memory: {e}")
    
    def record_order(self, price: float, size: int, side: str, 
                     timestamp: Optional[datetime] = None, 
                     contract_type: str = "ES") -> Dict:
        """
        Record a single order at tick level
        
        Args:
            price: Order price
            size: Order size in contracts
            side: 'BUY' or 'SELL'
            timestamp: Order timestamp (auto-generated if None)
            contract_type: Contract (default ES for E-mini S&P)
        
        Returns:
            Order record dict
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = timestamp
        
        order = {
            "timestamp": timestamp_str,
            "price": float(price),
            "size": int(size),
            "side": side.upper(),
            "contract_type": contract_type
        }
        
        with self.lock:
            # Store in memory for fast access
            self.memory_orders.append(order)
            
            # Persist to database
            self._save_to_db(order)
        
        return order
    
    def record_orders_batch(self, orders: List[Dict]):
        """Record multiple orders efficiently"""
        with self.lock:
            for order in orders:
                self.memory_orders.append(order)
            self._save_to_db_batch(orders)
    
    def _save_to_db(self, order: Dict):
        """Save single order to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (timestamp, price, size, side, contract_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            order["timestamp"],
            order["price"],
            order["size"],
            order["side"],
            order.get("contract_type", "ES")
        ))
        
        conn.commit()
        conn.close()
    
    def _save_to_db_batch(self, orders: List[Dict]):
        """Save multiple orders to database efficiently"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        for order in orders:
            cursor.execute('''
                INSERT INTO orders (timestamp, price, size, side, contract_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                order["timestamp"],
                order["price"],
                order["size"],
                order["side"],
                order.get("contract_type", "ES")
            ))
        
        conn.commit()
        conn.close()
    
    def get_recent_orders(self, limit: int = 100) -> List[Dict]:
        """Get most recent orders from database (persistent storage)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, size, side, contract_type
            FROM orders
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "price": row[1],
                "size": row[2],
                "side": row[3],
                "contract_type": row[4]
            }
            for row in rows
        ]
    
    def get_orders_by_time_range(self, start_time: datetime, 
                                 end_time: datetime) -> List[Dict]:
        """Get orders within time range from database"""
        start_iso = start_time.isoformat() if isinstance(start_time, datetime) else start_time
        end_iso = end_time.isoformat() if isinstance(end_time, datetime) else end_time
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, size, side, contract_type
            FROM orders
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
        ''', (start_iso, end_iso))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "price": row[1],
                "size": row[2],
                "side": row[3],
                "contract_type": row[4]
            }
            for row in rows
        ]
    
    def get_orders_by_price_range(self, min_price: float, 
                                  max_price: float, limit: int = 500) -> List[Dict]:
        """Get orders within price range"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, size, side, contract_type
            FROM orders
            WHERE price >= ? AND price <= ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (min_price, max_price, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "price": row[1],
                "size": row[2],
                "side": row[3],
                "contract_type": row[4]
            }
            for row in rows
        ]
    
    def get_orders_by_side(self, side: str, limit: int = 100) -> List[Dict]:
        """Get orders by side (BUY or SELL)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price, size, side, contract_type
            FROM orders
            WHERE side = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (side.upper(), limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "price": row[1],
                "size": row[2],
                "side": row[3],
                "contract_type": row[4]
            }
            for row in rows
        ]
    
    def get_volume_at_price(self, price: float, tolerance: float = 0.5) -> Dict:
        """Get total volume at specific price level ±tolerance"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT side, SUM(size) as total_volume
            FROM orders
            WHERE price >= ? AND price <= ?
            GROUP BY side
        ''', (price - tolerance, price + tolerance))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = {
            "price": price,
            "buy_volume": 0,
            "sell_volume": 0,
            "net_volume": 0
        }
        
        for side, volume in rows:
            if side == "BUY":
                result["buy_volume"] = volume
            elif side == "SELL":
                result["sell_volume"] = volume
        
        result["net_volume"] = result["buy_volume"] - result["sell_volume"]
        return result
    
    def get_volume_profile(self, limit: int = 500) -> Dict:
        """Get volume profile across price levels"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ROUND(price * 2) / 2 as price_level, side, COUNT(*) as count, SUM(size) as total_size
            FROM orders
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        profile = {}
        for price_level, side, count, total_size in rows:
            if price_level not in profile:
                profile[price_level] = {"buy": 0, "sell": 0, "net": 0, "count": 0}
            
            if side == "BUY":
                profile[price_level]["buy"] += total_size
            elif side == "SELL":
                profile[price_level]["sell"] += total_size
            
            profile[price_level]["net"] = profile[price_level]["buy"] - profile[price_level]["sell"]
            profile[price_level]["count"] += count
        
        return profile
    
    def export_orders_csv(self, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> str:
        """Export orders as CSV string"""
        import csv
        import io
        
        # Get orders
        if start_time and end_time:
            orders = self.get_orders_by_time_range(start_time, end_time)
        else:
            # Last 24 hours
            end = datetime.utcnow()
            start = end - timedelta(hours=24)
            orders = self.get_orders_by_time_range(start, end)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Timestamp", "Price", "Size", "Side", "Contract"])
        for order in reversed(orders):  # Chronological order
            writer.writerow([
                order["timestamp"],
                order["price"],
                order["size"],
                order["side"],
                order["contract_type"]
            ])
        
        return output.getvalue()
    
    def get_stats(self) -> Dict:
        """Get statistics about recorded orders"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total orders
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]
        
        # Buy/Sell breakdown
        cursor.execute('''
            SELECT side, COUNT(*) as count, SUM(size) as total_size
            FROM orders
            GROUP BY side
        ''')
        
        buy_count, buy_size, sell_count, sell_size = 0, 0, 0, 0
        for row in cursor.fetchall():
            if row[0] == "BUY":
                buy_count, buy_size = row[1], row[2] or 0
            elif row[0] == "SELL":
                sell_count, sell_size = row[1], row[2] or 0
        
        # Price range
        cursor.execute("SELECT MIN(price), MAX(price) FROM orders")
        min_price, max_price = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_orders": total_orders,
            "buy_orders": buy_count,
            "sell_orders": sell_count,
            "buy_volume": buy_size,
            "sell_volume": sell_size,
            "net_volume": buy_size - sell_size,
            "min_price": min_price,
            "max_price": max_price,
            "price_range": max_price - min_price if min_price and max_price else 0
        }
    
    def clear_old_orders(self, days: int = 15):
        """
        Clear orders older than N days (default 15 days for intraday trading)
        
        Args:
            days: Number of days to retain (default 15)
        
        Returns:
            Number of orders deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Count before deletion
        cursor.execute("SELECT COUNT(*) FROM orders WHERE timestamp < ?", (cutoff_iso,))
        count_before = cursor.fetchone()[0]
        
        # Delete old orders
        cursor.execute("DELETE FROM orders WHERE timestamp < ?", (cutoff_iso,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"🗑️  Auto-cleanup: Deleted {deleted:,} orders older than {days} days")
            print(f"   Cutoff date: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"✅ Auto-cleanup: No orders older than {days} days (all data is recent)")
        
        return deleted
    
    def auto_cleanup_on_startup(self, retention_days: int = 15):
        """Run cleanup automatically when recorder starts"""
        print(f"\n🧹 Running automatic cleanup (retention: {retention_days} days)...")
        deleted = self.clear_old_orders(days=retention_days)
        return deleted


# Global instance
order_recorder = RawOrderRecorder()
