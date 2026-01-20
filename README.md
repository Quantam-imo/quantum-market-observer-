# Quantum Market Observer + OIS

## Overview
A comprehensive institutional-grade market analysis system combining multiple analytical frameworks:

- **QMO** = Market State (Accumulation, Distribution, Expansion phases)
- **IMO** = Liquidity Analysis (Institutional order flow, sweeps, icebergs)
- **OIS** = Execution Engine (Order sizing, timing, management)
- **Gann** = Price Levels (Harmonic ratios, multiplication factors)
- **Astro** = Time Cycles (Planetary aspects, harmonic angles)
- **AI Mentor** = Decision System (Confidence weighting, signal generation)

## Project Structure

```
quantum-market-observer/
├── backend/
│   ├── core/              # Core analytical engines
│   ├── intelligence/      # QMO/IMO adapters & liquidity detection
│   ├── mentor/           # AI decision system
│   ├── memory/           # Historical tracking & performance
│   └── main.py
├── frontend/             # AI Mentor live panel
├── chart/                # Charting & visualization
├── data/                 # Market data sources
└── README.md
```

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
python backend/main.py
```

3. Open frontend in browser:
```bash
open frontend/index.html
```

## Core Components

### Gann Engine
- Calculates harmonic price levels using multipliers
- Supports resistance/support derived from range extensions

### Astro Engine
- Analyzes major planetary aspects (0°, 60°, 90°, 120°, 180°)
- Determines harmonic strength of time windows

### Cycle Engine
- Identifies Fibonacci/harmonic time cycles
- Detects 7, 14, 21, 30, 45, 90, 144, 180, 360 bar cycles

### Confidence Engine
Weighted scoring system:
- QMO: 30% (Market structure)
- IMO: 25% (Liquidity conditions)
- Gann: 20% (Price harmonics)
- Astro: 15% (Time harmonics)
- Cycle: 10% (Cycle alignment)

## Status
✅ Complete project structure  
✅ All core engines implemented  
✅ Ready for market data integration  
✅ Scales to CME real-time feeds