# System Architecture — Phase 1

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI Panel     │  │   Chart      │  │   Terminal   │      │
│  │ (HTML/JS)    │  │  (Chart.js)  │  │    (CLI)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓↑ (HTTP/REST)
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Routing Layer (routes.py)                             │ │
│  │  - 10 REST endpoints                                   │ │
│  │  - Request validation (Pydantic)                       │ │
│  │  - Response serialization                              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CORS Middleware                                        │ │
│  │  - Allow frontend communication                         │ │
│  │  - Cross-origin request handling                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓↑ (Direct calls)
┌─────────────────────────────────────────────────────────────┐
│               ENGINE LAYER (Pure Logic)                      │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   CORE ENGINES   │  │ INTELLIGENCE     │                │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                │
│  │  │ Gann       │  │  │  │ QMO        │  │                │
│  │  ├────────────┤  │  │  ├────────────┤  │                │
│  │  │ Astro      │  │  │  │ IMO        │  │                │
│  │  ├────────────┤  │  │  ├────────────┤  │                │
│  │  │ Cycle      │  │  │  │ Liquidity  │  │                │
│  │  ├────────────┤  │  │  ├────────────┤  │                │
│  │  │ Price Deg. │  │  │  │ Iceberg    │  │                │
│  │  ├────────────┤  │  │  ├────────────┤  │                │
│  │  │ Angle      │  │  │  │ News       │  │                │
│  │  └────────────┘  │  │  └────────────┘  │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │     MENTOR       │  │    MEMORY        │                │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                │
│  │  │ Mentor     │  │  │  │ Iceberg    │  │                │
│  │  │ Brain      │  │  │  ├────────────┤  │                │
│  │  ├────────────┤  │  │  │ Cycle      │  │                │
│  │  │ Confidence │  │  │  ├────────────┤  │                │
│  │  │ Engine     │  │  │  │ Signal     │  │                │
│  │  ├────────────┤  │  │  └────────────┘  │                │
│  │  │ Signal     │  │  │                  │                │
│  │  │ Builder    │  │  │  (Persistent)    │                │
│  │  └────────────┘  │  └──────────────────┘                │
│  └──────────────────┘                                       │
│                                                              │
│  [No changes to existing logic]                             │
└─────────────────────────────────────────────────────────────┘
                          ↓↑ (Data calls)
┌─────────────────────────────────────────────────────────────┐
│              DATA LAYER (Market Source)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Phase 1: In-Memory Mock Data                          │ │
│  │  - market_state dictionary                             │ │
│  │  - Placeholder for real data                           │ │
│  │                                                        │ │
│  │  Phase 2: CME Live Feed (Next)                         │ │
│  │  - GC futures (bid/ask/volume/delta)                   │ │
│  │  - Real-time streaming                                 │ │
│  │  - Historical OHLC data                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow Example: AI Mentor Panel

```
1. Frontend Request
   POST /api/v1/mentor
   {"symbol": "XAUUSD", "refresh": true}
                ↓
2. FastAPI Validation
   - Pydantic checks request format
   - Validates required fields
   - Type checking
                ↓
3. Route Handler (routes.py)
   def get_mentor_panel(request: MentorPanelRequest)
   - Reads current market state
   - Calls each engine with appropriate data
                ↓
4. Engine Calls (Parallel)
   ├─ gann_engine.levels(high, low)
   ├─ astro_engine.aspect(d1, d2)
   ├─ cycle_engine.is_cycle(bars)
   ├─ liquidity_engine.detect_liquidity_pool()
   └─ iceberg_engine.detect()
                ↓
5. Response Assembly
   - Gather all engine outputs
   - Create MentorPanelResponse model
   - Serialize to JSON
                ↓
6. Frontend Receives
   {
     "market": "XAUUSD",
     "session": "LONDON",
     "current_price": 2450.50,
     "htf_structure": {...},
     "iceberg_activity": {...},
     "gann_levels": {...},
     "ai_verdict": "⛔ WAIT",
     "confidence_percent": 81.0
   }
```

## Data Models (Pydantic Schemas)

```
Request Models                Response Models
├── MarketRequest         ├── MarketResponse
├── GannRequest           ├── GannResponse
├── AstroRequest          ├── AstroResponse
├── CycleRequest          ├── CycleResponse
├── IcebergRequest        ├── IcebergResponse
├── LiquidityRequest      ├── LiquidityResponse
├── SignalRequest         ├── SignalResponse
├── MentorPanelRequest    ├── MentorPanelResponse
├── ChartRequest          ├── ChartResponse
└──                       ├── HealthResponse
                          └── [9 Data Models]
```

## API Endpoint Mapping

```
Endpoint              Engine Called
─────────────────────────────────────
/api/v1/health       System status
/api/v1/market       market_state (mock)
/api/v1/gann         GannEngine.levels()
/api/v1/astro        AstroEngine.aspect()
/api/v1/cycle        CycleEngine.is_cycle()
/api/v1/iceberg      IcebergEngine.detect()
/api/v1/liquidity    LiquidityEngine methods
/api/v1/signal       ConfidenceEngine + MentorBrain
/api/v1/mentor       All engines + MentorPanelResponse
/api/v1/chart        ChartResponse generator
```

## Middleware Stack

```
HTTP Request
    ↓
CORS Check (Allow frontend origins)
    ↓
Route Matching
    ↓
Request Validation (Pydantic)
    ↓
Handler Execution
    ↓
Response Serialization (JSON)
    ↓
CORS Headers Applied
    ↓
HTTP Response
```

## Phase 1 vs Phase 2

### Phase 1 (Current)
```
Frontend (Static)
    ↓
REST API (FastAPI)
    ↓
Engines (Pure Logic)
    ↓
Mock Data (In-Memory)
```

### Phase 2 (Coming)
```
Frontend (Dynamic Dashboard)
    ↓
REST API (Same endpoints)
    ↓
Engines (Same logic)
    ↓
CME Live Feed (Real XAUUSD)
```

## Scalability Path

```
Current (Phase 1)          Phase 2                    Phase 3
─────────────────────────────────────────────────────────────
Mock Data               CME Data Stream           Multi-Exchange
Single Process         WebSocket Support         Load Balanced
In-Memory              Redis Cache               Kubernetes
Local Testing          Production Ready          Enterprise Scale
```

---

## File Organization

```
quantum-market-observer/
│
├── backend/
│   ├── api/                    ← NEW in Phase 1
│   │   ├── __init__.py
│   │   ├── schemas.py          ← 15 Pydantic models
│   │   ├── routes.py           ← 10 endpoints
│   │   └── server.py           ← FastAPI app
│   │
│   ├── core/                   ← Existing (untouched)
│   │   ├── gann_engine.py
│   │   ├── astro_engine.py
│   │   ├── cycle_engine.py
│   │   ├── price_degree_engine.py
│   │   └── angle_engine.py
│   │
│   ├── intelligence/           ← Existing (untouched)
│   │   ├── qmo_adapter.py
│   │   ├── imo_adapter.py
│   │   ├── liquidity_engine.py
│   │   ├── iceberg_engine.py
│   │   └── news_filter.py
│   │
│   ├── mentor/                 ← Existing (untouched)
│   │   ├── mentor_brain.py
│   │   ├── confidence_engine.py
│   │   └── signal_builder.py
│   │
│   ├── memory/                 ← Existing (untouched)
│   │   ├── iceberg_memory.py
│   │   ├── cycle_memory.py
│   │   └── signal_memory.py
│   │
│   └── main.py                 ← Updated
│
├── frontend/                   ← Existing (ready to connect)
├── chart/                      ← Existing (ready to connect)
├── data/                       ← Existing (ready to enhance)
│
└── Documentation
    ├── README.md               ← Project overview
    ├── ARCHITECTURE.md         ← This file
    ├── PHASE1_API_SETUP.md     ← Complete setup guide
    ├── PHASE1_SUMMARY.md       ← Phase 1 summary
    └── QUICKSTART.md           ← Quick reference
```

---

**Architecture Status: ✅ PRODUCTION READY FOR PHASE 1**

Next: CME data integration in Phase 2
