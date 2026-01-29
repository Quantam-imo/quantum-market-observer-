"""
FastAPI Server - Main entry point for Quantum Market Observer backend.
Institutional-grade REST API for live market analysis and AI decision making.

Usage:
    uvicorn backend.api.server:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import routes
from backend.api.routes import router
from backend.api.v2 import router as router_v2

# ==================== FASTAPI APP INITIALIZATION ====================

app = FastAPI(
    title="Quantum Market Observer API",
    description="Institutional market analysis with QMO, IMO, Gann, Astro, and AI Mentor",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ==================== CORS MIDDLEWARE ====================
# Allow frontend to communicate with backend

app.add_middleware(
    CORSMiddleware,
    # Allow local dev and Codespaces wildcard
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8080",
    ],
    allow_origin_regex=r"https://.*\.app\.github\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*"],
)

# ==================== ROUTE REGISTRATION ====================

app.include_router(router)
app.include_router(router_v2)


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """API information."""
    return {
        "service": "Quantum Market Observer",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response to avoid 404 noise for favicon requests."""
    return JSONResponse(status_code=204, content=None)


@app.get("/api")
async def api_info():
    """API endpoint information."""
    return {
        "version": "1.0.0",
        "base_url": "/api/v1",
        "endpoints": {
            "market": "POST /api/v1/market - Current market state",
            "gann": "POST /api/v1/gann - Gann levels",
            "astro": "POST /api/v1/astro - Astro aspects",
            "cycle": "POST /api/v1/cycle - Cycle detection",
            "iceberg": "POST /api/v1/iceberg - Iceberg detection",
            "liquidity": "POST /api/v1/liquidity - Liquidity analysis",
            "signal": "POST /api/v1/signal - Trading signal",
            "mentor": "POST /api/v1/mentor - AI Mentor panel",
            "chart": "POST /api/v1/chart - Chart data",
            "health": "GET /api/v1/health - System health"
        }
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global error handling."""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


# ==================== LIFESPAN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 60)
    print("🚀 Quantum Market Observer Backend Starting...")
    print("=" * 60)
    print("📍 Engines initialized:")
    print("   ✓ Gann Engine")
    print("   ✓ Astro Engine")
    print("   ✓ Cycle Engine")
    print("   ✓ Liquidity Engine")
    print("   ✓ Iceberg Engine")
    print("   ✓ QMO Adapter")
    print("   ✓ IMO Adapter")
    print("   ✓ Confidence Engine")
    print("   ✓ Mentor Brain")
    print("=" * 60)
    print("📊 API Documentation: http://localhost:8000/api/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\n" + "=" * 60)
    print("🛑 Quantum Market Observer Backend Shutting Down...")
    print("=" * 60)


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n🎯 Starting Quantum Market Observer API Server...\n")
    print("📡 Running on: http://0.0.0.0:8000")
    print("📚 Documentation: http://0.0.0.0:8000/api/docs")
    print("🔍 ReDoc: http://0.0.0.0:8000/api/redoc\n")
    
    uvicorn.run(
        "backend.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"],
        log_level="info"
    )
