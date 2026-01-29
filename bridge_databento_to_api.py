"""Bridge live Databento trades into FastAPI /api/v1/cme/ingest.

Usage:
    export DATABENTO_API_KEY="..."
    python bridge_databento_to_api.py --symbol GCG6 --batch-seconds 1 --api http://localhost:8000

This streams L1 trades from Databento and periodically POSTs them to the backend
so AbsorptionZoneMemory and /api/v1/status can reflect real iceberg zones.
"""
import os
import time
import json
import argparse
from datetime import datetime, timezone

import databento as db
import requests

DEFAULT_SYMBOL = "GCG6"  # Gold Feb 2026
DEFAULT_DATASET = "GLBX.MDP3"
DEFAULT_API = "http://localhost:8000"


def stream_and_forward(api_key: str, symbol: str, dataset: str, api_base: str, batch_seconds: float):
    client = db.Live(key=api_key)
    client.subscribe(dataset=dataset, schema="trades", symbols=[symbol])

    print(f"✅ Connected to Databento | {dataset}:{symbol} | Forwarding to {api_base}/api/v1/cme/ingest")
    trades_batch = []
    last_flush = time.time()

    try:
        for msg in client:
            now = datetime.now(timezone.utc).isoformat()
            if not hasattr(msg, "price") or not hasattr(msg, "size"):
                continue

            trade = {
                "type": "TRADE",
                "price": msg.price,
                "size": msg.size,
                "side": "BUY" if getattr(msg, "side", "B") == "B" else "SELL",
                "timestamp": now,
            }
            trades_batch.append(trade)

            # Flush batch
            if time.time() - last_flush >= batch_seconds and trades_batch:
                try:
                    resp = requests.post(
                        f"{api_base}/api/v1/cme/ingest",
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(trades_batch),
                        timeout=5,
                    )
                    if resp.status_code != 200:
                        print(f"⚠️  Ingest failed {resp.status_code}: {resp.text[:200]}")
                    else:
                        body = resp.json()
                        print(f"📨 Sent {len(trades_batch)} trades | Price {body.get('current_price')} | Iceberg zones: {body.get('iceberg_zones_detected')}")
                except Exception as e:
                    print(f"⚠️  HTTP error: {e}")
                trades_batch = []
                last_flush = time.time()
    finally:
        try:
            client.stop()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--api", default=DEFAULT_API, help="Backend base URL (e.g., http://localhost:8000)")
    parser.add_argument("--batch-seconds", type=float, default=1.0, help="Flush trades every N seconds")
    args = parser.parse_args()

    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        raise SystemExit("DATABENTO_API_KEY is required")

    stream_and_forward(api_key, args.symbol, args.dataset, args.api, args.batch_seconds)


if __name__ == "__main__":
    main()
