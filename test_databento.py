#!/usr/bin/env python3
"""
Quick Databento Connection Test
Run this to verify your Databento setup works
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.feeds.databento_fetcher import test_databento_connection


async def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║                  DATABENTO CONNECTION TEST                      ║
║                                                                 ║
║  This will test your Databento API access for CME Gold (GC)   ║
║                                                                 ║
║  Make sure you have:                                           ║
║  1. Set DATABENTO_API_KEY environment variable                 ║
║  2. Active Databento subscription                              ║
║  3. Access to GLBX.MDP3 dataset                                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    input("Press ENTER to start test... ")
    
    success = await test_databento_connection()
    
    if success:
        print("""
╔════════════════════════════════════════════════════════════════╗
║                    ✅ TEST SUCCESSFUL                          ║
║                                                                 ║
║  Your Databento connection is working!                         ║
║                                                                 ║
║  NEXT STEPS:                                                   ║
║  Reply with number 2️⃣ to get Iceberg Detection code          ║
╚════════════════════════════════════════════════════════════════╝
        """)
    else:
        print("""
╔════════════════════════════════════════════════════════════════╗
║                    ❌ TEST FAILED                              ║
║                                                                 ║
║  Please check:                                                 ║
║  1. Your API key is correct                                    ║
║  2. Your subscription is active                                ║
║  3. You have access to GLBX.MDP3 dataset                       ║
║                                                                 ║
║  Contact: support@databento.com                                ║
╚════════════════════════════════════════════════════════════════╝
        """)
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
