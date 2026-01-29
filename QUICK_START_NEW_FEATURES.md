# 🚀 QUICK START GUIDE

## Access Your Application

### **Frontend (Chart Interface)**
```
http://localhost:3000
```
Or if using Codespaces:
```
https://<your-codespace>-3000.app.github.dev
```

### **Backend API**
```
http://localhost:8000/api/v1/status
```

---

## 🎨 NEW FEATURES - HOW TO USE

### 1. **Crosshair Tooltip** 📊
**How to activate:**
- Simply hover your mouse over the chart
- Crosshair lines (vertical + horizontal) appear automatically
- Tooltip shows:
  - Date & Time
  - Open, High, Low, Close prices
  - Volume
- Move mouse around to see different candles
- Tooltip auto-positions to stay visible

**Keyboard shortcut:** None needed - always active when hovering

---

### 2. **Theme Toggle** 🌓
**How to activate:**
- Look for the 🌓 button in the top-right toolbar
- Click once to switch between Dark ↔ Light theme
- Changes apply instantly to:
  - Chart background
  - Grid lines
  - Candle colors
  - Volume bars
  - Text and labels
  - Tooltip
  - Mentor panel

**Default:** Dark theme

---

### 3. **Iceberg Memory** 🧊
**Automatic tracking in backend:**
- System automatically learns from iceberg zones
- Historical win/loss records stored
- Success rates calculated per zone
- Memory persists between sessions

**Access memory data:**
```python
# In backend code or API
from backend.iceberg_engine import IcebergEngine

engine = IcebergEngine()
best_zones = engine.get_best_zones(top_n=5)
# Returns top 5 zones by win rate
```

**Memory file:** `iceberg_memory.json` in project root

---

### 4. **Advanced Gann Analysis** 📐
**Use via API or backend code:**
```python
from backend.core.gann_engine import GannEngine

gann = GannEngine()

# Get Gann levels
levels = gann.levels(high=2700, low=2600)

# Square of 9 projections
sq9 = gann.square_of_nine(price=2650, rotations=4)

# Gann angles
angles = gann.calculate_angles(
    price=2650, 
    range_size=100, 
    time_units=10
)

# Find price clusters (confluence zones)
clusters = gann.price_clusters(
    current_price=2650,
    high=2700,
    low=2600
)
```

---

## 🛠️ Existing Features Quick Reference

### **Timeframe Selection**
- Click buttons: 1m, 5m, 15m, 1H, 4H, 1D
- Chart updates automatically

### **Volume Toggle**
- Click 📊 button in toolbar
- Shows/hides left-side volume bars

### **Pan Chart**
- Click and drag on chart to pan
- Horizontal panning: Move through time
- Vertical panning: Adjust price range

### **Live Updates**
- Chart refreshes every 5 seconds
- Live price badge on right side
- Green = price up, Red = price down

### **Iceberg Zones**
- Orange/yellow bands show detected zones
- Display on chart automatically
- Click top panel to expand orderflow table

---

## 🔧 Troubleshooting

### **Chart Not Updating?**
1. Hard refresh: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
2. Check browser console (F12) for errors
3. Verify backend is running: `curl http://localhost:8000/api/v1/status`

### **Theme Not Changing?**
- Click the 🌓 button again
- Check if browser has JavaScript enabled
- Try hard refresh

### **Crosshair Not Showing?**
- Ensure mouse is inside chart canvas area
- Check browser console for JavaScript errors
- Try hard refresh

### **Servers Not Running?**
```bash
# Check processes
lsof -i:8000  # Backend
lsof -i:3000  # Frontend

# Restart if needed
./start.sh
```

---

## 📍 Server Management

### **Start Servers**
```bash
cd /workspaces/quantum-market-observer-

# Backend (from root)
python -m uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
python -m http.server 3000
```

### **Stop Servers**
```bash
lsof -ti:8000 | xargs kill -9  # Stop backend
lsof -ti:3000 | xargs kill -9  # Stop frontend
```

### **Check Server Status**
```bash
curl http://localhost:8000/api/v1/status  # Backend
curl http://localhost:3000/                # Frontend
```

---

## 🎯 What's Next?

### **Immediate Testing**
1. ✅ Open frontend in browser
2. ✅ Hard refresh (`Ctrl + Shift + R`)
3. ✅ Hover mouse over chart → See crosshair
4. ✅ Click 🌓 button → Switch themes
5. ✅ Check iceberg zones display
6. ✅ Toggle volume with 📊 button

### **Future Enhancements**
- Mouse wheel zoom
- Drawing tools (trendlines, Fibonacci)
- More indicators (RSI, MACD, Bollinger)
- Export chart as image
- Price alerts
- Multiple symbols support

---

## 📚 Key Files Reference

### **Frontend**
- `frontend/index.html` - HTML structure
- `frontend/chart.v4.js` - Chart logic (1000+ lines)
- `frontend/style.css` - Styling

### **Backend**
- `backend/api/server.py` - FastAPI app
- `backend/api/routes.py` - API endpoints
- `backend/iceberg_engine.py` - Iceberg memory
- `backend/memory_engine.py` - Trade memory
- `backend/core/gann_engine.py` - Gann analysis

### **Data**
- `iceberg_memory.json` - Iceberg zone history
- `trade_memory.json` - Trade history

---

## 🚨 Important Commands

```bash
# Hard refresh browser
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)

# View backend logs
tail -f /tmp/backend.log

# View frontend logs
tail -f /tmp/frontend.log

# Test API
curl http://localhost:8000/api/v1/status

# API Documentation
http://localhost:8000/api/docs
http://localhost:8000/api/redoc
```

---

**Everything is ready! Start exploring the new features!** 🎉

**Need help?** Check `FEATURES_COMPLETE.md` for detailed technical documentation.
