"""
Quantum Market Observer + OIS Engine
Main entry point - Starts the FastAPI backend server
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("🚀 Quantum Market Observer + OIS Engine")
print("=" * 60)
print("")
print("✅ All engines initialized:")
print("   • Gann Engine")
print("   • Astro Engine")
print("   • Cycle Engine")
print("   • Liquidity Engine")
print("   • Iceberg Engine")
print("   • QMO Adapter")
print("   • IMO Adapter")
print("   • Confidence Engine")
print("   • Mentor Brain")
print("")
print("📡 FastAPI Backend:")
print("   Start with: uvicorn backend.api.server:app --reload")
print("   API Docs: http://localhost:8000/api/docs")
print("   ReDoc: http://localhost:8000/api/redoc")
print("")
print("🎨 Frontend:")
print("   Open: frontend/index.html in your browser")
print("")
print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    from backend.api.server import app
    
    print("\n🎯 Starting Quantum Market Observer API Server...\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
