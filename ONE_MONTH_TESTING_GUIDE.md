# 📅 ONE-MONTH TESTING GUIDE
**Testing Period:** 30 Days Live Market Validation  
**Last Updated:** January 22, 2026  
**Project Status:** Ready for Extended Testing ✅

---

## 🎯 TESTING OBJECTIVES

### Primary Goals
1. **System Stability**: Verify 24/5 uptime with no critical failures
2. **Data Accuracy**: Validate all analytical signals against actual market moves
3. **Performance**: Monitor response times, memory usage, and API throughput
4. **User Experience**: Assess frontend usability and drawer functionality
5. **Signal Quality**: Track AI Mentor win rate and confidence accuracy

---

## 🚀 SETUP FOR TESTING

### 1. Start Backend Server
```bash
cd /workspaces/quantum-market-observer-/backend
python -m uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open Frontend
- Navigate to `http://localhost:8000` in browser
- Or use codespace URL: `https://<codespace>-8000.app.github.dev`

### 3. Verify All Systems
```bash
# Check health
curl http://localhost:8000/api/v1/health

# Check status
curl http://localhost:8000/api/v1/status

# Test mentor endpoint
curl -X POST http://localhost:8000/api/v1/mentor \
  -H "Content-Type: application/json" \
  -d '{"symbol": "XAUUSD", "refresh": true}'
```

---

## 📊 DAILY TESTING CHECKLIST

### Morning (Market Open)
- [ ] Check backend is running (`ps aux | grep uvicorn`)
- [ ] Verify frontend loads with live data
- [ ] Confirm all 5 drawers populate (Gann, Astro, Iceberg, News, Global)
- [ ] Check volume bars display correctly
- [ ] Verify VWAP overlay renders
- [ ] Test iceberg zones toggle
- [ ] Review AI Mentor verdict (WAIT/BUY/SELL)

### Mid-Day (Active Trading Hours)
- [ ] Monitor live price updates (every 5 seconds)
- [ ] Check Gann levels accuracy (do price reactions occur at predicted levels?)
- [ ] Validate Astro signals (do high-influence aspects correlate with volatility?)
- [ ] Track iceberg zones (do they catch institutional absorption?)
- [ ] Review news events vs actual market moves
- [ ] Test chart panning and theme toggle

### Evening (Market Close)
- [ ] Export today's chart data (screenshot)
- [ ] Log AI Mentor accuracy:
  - Verdict given: ______
  - Actual outcome: ______
  - Confidence: ______%
  - Win/Loss: ______
- [ ] Check for any console errors
- [ ] Review backend logs: `tail -100 /tmp/backend.log`
- [ ] Note any performance issues or crashes

---

## 📈 METRICS TO TRACK

### System Metrics
| Metric | Target | How to Check |
|--------|--------|--------------|
| Uptime | >99.5% | `uptime` command |
| API Response Time | <500ms | Browser DevTools Network tab |
| Memory Usage | <2GB | `htop` or `ps aux` |
| Chart FPS | 30+ | Browser DevTools Performance |
| Data Refresh Rate | 5 seconds | Console logs |

### Trading Metrics
| Metric | Target | Notes |
|--------|--------|-------|
| AI Verdict Accuracy | >65% | Track WAIT/BUY/SELL outcomes |
| Gann Level Hits | >70% | Price reactions at predicted levels |
| Astro Signal Correlation | >60% | Volatility during high-influence aspects |
| Iceberg Detection Rate | >80% | Zones that show institutional activity |
| False Signal Rate | <20% | Zones/levels that fail to produce reactions |

---

## 🔧 WEEKLY MAINTENANCE

### Every Monday
1. **Data Backup**
   ```bash
   cp backend/iceberg_memory.json backup/iceberg_memory_$(date +%Y%m%d).json
   cp iceberg_memory.json backup/iceberg_memory_frontend_$(date +%Y%m%d).json
   ```

2. **Log Rotation**
   ```bash
   mv /tmp/backend.log /tmp/backend_$(date +%Y%m%d).log
   ```

3. **Performance Review**
   - Check average API response times
   - Review memory usage trends
   - Identify any slow endpoints

### Every Friday
1. **Win/Loss Summary**
   - Calculate AI Mentor accuracy for the week
   - Document any pattern failures
   - Note correlation between confidence % and win rate

2. **Feature Testing**
   - Test all 5 drawers (Gann, Astro, Iceberg, News, Global)
   - Verify toggle buttons work
   - Check theme persistence
   - Test chart panning

---

## 🐛 KNOWN ISSUES TO MONITOR

### Frontend
- [ ] MA indicator button (stubbed, not implemented)
- [ ] RSI indicator button (stubbed, not implemented)
- [ ] Drawing tools (zoom, trendline, fib, h-line not functional)
- [ ] Theme persistence (resets to dark on reload)
- [ ] Timeframe persistence (doesn't save preference)

### Backend
- [ ] News events are sample data (not live feed yet)
- [ ] Global markets data is simulated (no real indices/FX yet)
- [ ] News memory state resets on server restart

---

## 📝 TESTING LOG TEMPLATE

### Date: ___________

**Market Conditions:**
- Session: ___________
- Volatility: High / Medium / Low
- Major News: ___________

**System Performance:**
- Uptime: ___________
- Crashes: ___________
- Errors: ___________

**AI Mentor Performance:**
- Verdict: ___________
- Confidence: _______%
- Outcome: Win / Loss / Pending
- Notes: ___________

**Feature Testing:**
- [ ] All drawers loaded
- [ ] Volume bars rendered
- [ ] VWAP overlay correct
- [ ] Iceberg zones detected
- [ ] Gann levels accurate
- [ ] Astro signals relevant
- [ ] News events displayed
- [ ] Global markets narrative

**Issues Found:**
1. ___________
2. ___________
3. ___________

**Action Items:**
1. ___________
2. ___________

---

## 🎯 END-OF-MONTH EVALUATION

### Success Criteria (After 30 Days)

**Must Have (Critical)**
- [ ] System ran for 30 days with <5 crashes
- [ ] AI Mentor accuracy >60%
- [ ] All 5 drawers populated every session
- [ ] No data corruption or memory leaks
- [ ] User can trade based on signals confidently

**Nice to Have (Bonus)**
- [ ] MA/RSI indicators implemented
- [ ] Drawing tools added
- [ ] Theme/timeframe persistence working
- [ ] Win rate >70%
- [ ] News feed integrated with live API

### Decision Points

**If Success Criteria Met:**
→ Proceed to Phase 5 (Advanced Features)  
→ Begin real money paper trading  
→ Start user onboarding (if applicable)

**If Issues Found:**
→ Document all bugs systematically  
→ Prioritize fixes based on severity  
→ Re-test for 2 more weeks  

---

## 🚨 EMERGENCY PROCEDURES

### Backend Crash
```bash
# Restart server
cd /workspaces/quantum-market-observer-/backend
pkill -f uvicorn
python -m uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

### Frontend Not Loading
```bash
# Check backend status
curl http://localhost:8000/api/v1/health

# Check for errors
tail -50 /tmp/backend.log

# Hard refresh browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

### Memory Issues
```bash
# Check memory usage
free -h

# Check which process is consuming memory
ps aux --sort=-%mem | head -10

# Restart backend if memory leak detected
```

---

## 📞 SUPPORT & DOCUMENTATION

### Helpful Commands
```bash
# Check if backend is running
lsof -i:8000

# View real-time logs
tail -f /tmp/backend.log

# Monitor system resources
htop

# Test API endpoints
curl http://localhost:8000/api/v1/status
```

### Key Files
- Frontend: `/workspaces/quantum-market-observer-/frontend/chart.v4.js`
- Backend: `/workspaces/quantum-market-observer-/backend/api/routes.py`
- Config: `/workspaces/quantum-market-observer-/backend/config.py`
- Logs: `/tmp/backend.log`

### Quick Reference
- API Base URL: `http://localhost:8000`
- Frontend URL: `http://localhost:8000/frontend/index.html`
- Health Check: `GET /api/v1/health`
- Status Check: `GET /api/v1/status`
- Chart Data: `POST /api/v1/chart`
- AI Mentor: `POST /api/v1/mentor`

---

## ✅ TESTING COMPLETION

At the end of 30 days, compile:
1. **Performance Report** (uptime, response times, errors)
2. **Accuracy Report** (AI Mentor win rate, signal quality)
3. **Feature Report** (what works, what needs improvement)
4. **Bug List** (prioritized by severity)
5. **Recommendation** (proceed to production or extend testing)

**Good luck with your month-long testing! 🚀**
