#!/usr/bin/env python3
"""
Test Iceberg Detection Engine
Run this after confirming Databento connection works
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.feeds.iceberg_detector import test_iceberg_detection


async def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║              ICEBERG DETECTION ENGINE TEST                      ║
║                                                                 ║
║  This will stream live CME Gold (GC) orderflow and detect     ║
║  institutional iceberg orders in real-time.                    ║
║                                                                 ║
║  WHAT TO EXPECT:                                               ║
║  - Live L3 orderflow data streaming                            ║
║  - Automatic iceberg pattern detection                         ║
║  - Buy/Sell absorption identification                          ║
║  - Confidence scoring for each detection                       ║
║                                                                 ║
║  DETECTION CRITERIA:                                           ║
║  • 5+ executions at same price                                 ║
║  • 3x average volume concentration                             ║
║  • Minimal price movement (absorption)                         ║
║  • 70%+ confidence threshold                                   ║
║                                                                 ║
║  Duration: 60 seconds                                          ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    input("Press ENTER to start iceberg detection... ")
    
    try:
        await test_iceberg_detection()
        
        print("""
╔════════════════════════════════════════════════════════════════╗
║                    ✅ TEST COMPLETE                            ║
║                                                                 ║
║  If you saw icebergs detected:                                 ║
║  → You have L3 access ✅                                       ║
║  → Institutional orderflow is working                          ║
║  → Core edge is operational                                    ║
║                                                                 ║
║  NEXT STEP:                                                    ║
║  Reply with 2️⃣ to build Volume Profile engine                ║
╚════════════════════════════════════════════════════════════════╝
        """)
        
    except Exception as e:
        if "mbo" in str(e).lower() or "schema" in str(e).lower():
            print("""
╔════════════════════════════════════════════════════════════════╗
║                  ⚠️  L3 ACCESS REQUIRED                        ║
║                                                                 ║
║  Iceberg detection requires L3 (mbo) schema access.           ║
║                                                                 ║
║  ACTION REQUIRED:                                              ║
║  1. Log in to Databento dashboard                              ║
║  2. Check your subscription includes L3/mbo access            ║
║  3. If not available, contact support@databento.com           ║
║                                                                 ║
║  L3 = Market by Order = Iceberg detection capability          ║
╚════════════════════════════════════════════════════════════════╝
            """)
        else:
            print(f"""
╔════════════════════════════════════════════════════════════════╗
║                    ❌ ERROR OCCURRED                           ║
║                                                                 ║
║  {str(e)[:60]}
║                                                                 ║
║  Please share this error for troubleshooting.                  ║
╚════════════════════════════════════════════════════════════════╝
            """)


if __name__ == "__main__":
    asyncio.run(main())
