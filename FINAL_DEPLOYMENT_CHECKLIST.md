# STEP 18 — FINAL LIVE-DEPLOYMENT CHECKLIST
## Institutional Launch Discipline (Before You Go Live)

---

## 🎯 CORE PRINCIPLE

**Accuracy > Stability > Speed > Features**

Most retail systems fail because they reverse this.
You will NOT.

---

## ✅ SECTION 1 — INFRASTRUCTURE SETUP

### 1.1 Server Selection

**[ ] Option A (Recommended): Managed Platform**
- [ ] Backend: Render.com or Railway.app (PostgreSQL addon)
- [ ] Frontend: Vercel or Netlify
- [ ] Auto-restart enabled
- [ ] Health check endpoint configured
- Estimated cost: $20-50/month

**[ ] Option B: AWS (Scale Later)**
- [ ] EC2 instance (t3.small minimum: 2vCPU, 2GB RAM)
- [ ] RDS PostgreSQL (db.t3.micro)
- [ ] CloudWatch monitoring
- [ ] Auto-scaling rules
- Only switch here after 100+ paying users

**[ ] Server Specs Verified**
- [ ] 2+ vCPU
- [ ] 4+ GB RAM
- [ ] SSD storage (not spinning disk)
- [ ] Auto-restart enabled
- [ ] Backup configured (daily snapshots)
- [ ] 99.5%+ uptime SLA

### 1.2 Database Setup

**[ ] Production Database Ready**
- [ ] PostgreSQL 13+ (SQLite → Postgres upgrade)
- [ ] Daily automated backups
- [ ] Backup tested (can restore in < 5 min)
- [ ] Connection pooling enabled
- [ ] Read replicas configured (optional, scale later)

**[ ] Database Tables Created**
```sql
CREATE TABLE signals (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP,
  direction VARCHAR(10),
  entry FLOAT,
  stop FLOAT,
  target FLOAT,
  confidence FLOAT,
  phase VARCHAR(50),
  result VARCHAR(50),
  created_at TIMESTAMP
);

CREATE TABLE trader_activity (
  id SERIAL PRIMARY KEY,
  trader_id VARCHAR(100),
  event_type VARCHAR(50),
  details JSONB,
  created_at TIMESTAMP
);

CREATE TABLE health_checks (
  id SERIAL PRIMARY KEY,
  check_type VARCHAR(50),
  status VARCHAR(50),
  message TEXT,
  created_at TIMESTAMP
);
```

### 1.3 Environment Variables

**[ ] Production secrets configured**
- [ ] `.env` file created (NOT in git)
- [ ] CME API key stored securely (Render secrets / AWS Secrets Manager)
- [ ] News API key stored securely
- [ ] JWT secret for authentication
- [ ] Database connection string
- [ ] Frontend URL whitelist configured
- [ ] CORS configured correctly

### 1.4 Monitoring & Logging

**[ ] Logging configured**
- [ ] Log aggregation enabled (e.g., Sentry, LogRocket)
- [ ] Error logging captures: timestamp, user, action, error message
- [ ] Access logs retained 30 days
- [ ] Alert on ERROR level events

**[ ] Uptime monitoring**
- [ ] UptimeRobot or equivalent checking health endpoint every 5 min
- [ ] Alerting on downtime (email + SMS)
- [ ] Dashboard visible to team

---

## ✅ SECTION 2 — DATA FEEDS

### 2.1 Price Feed Setup

**[ ] CME COMEX Gold (GC) Connected**
- [ ] Live tick data flowing
- [ ] Latency < 500ms acceptable (institutional is <100ms)
- [ ] Data quality check: no gaps, no spikes > 5% move
- [ ] Backup feed configured (if available)

**[ ] Data Caching Strategy**
- [ ] Redis cache for latest price
- [ ] Cache key: `gold_price_latest`
- [ ] TTL: 30 seconds
- [ ] Fallback: use previous 5-min close if real-time unavailable

**[ ] Data Validation Rules**
```python
# Reject data if:
if price == 0:
    reject()  # Invalid
if abs(price - last_price) / last_price > 0.05:
    log_spike()  # Log but accept
if time_since_last_tick > 300:  # 5 minutes
    alert_stale_data()
```

### 2.2 News Calendar

**[ ] News source configured**
- [ ] ForexFactory calendar scraper (cached)
- [ ] Update interval: 5 minutes
- [ ] High & Medium impact only
- [ ] Store in database with impact + time

**[ ] News Lockout Logic**
```python
if news_event_within_last_15_minutes:
    disable_trading()  # Hard stop
    show_message("High-impact news active")
```

### 2.3 Data Feed Failover

**[ ] Primary feed down → Secondary feed**
- [ ] Primary: CME API
- [ ] Secondary: Historical data (graceful degrade)
- [ ] Automatic failover < 10 seconds
- [ ] Alert when failover triggered

---

## ✅ SECTION 3 — RATE LIMITING & COST CONTROL

### 3.1 Engine Scan Frequencies (CRITICAL)

**[ ] QMO Engine: Every 20 minutes**
- [ ] Not on every tick
- [ ] Not on every bar
- [ ] Exactly 3 times per trading hour

**[ ] Gann Engine: Per session**
- [ ] Once at market open (9:30 AM ET)
- [ ] Not recalculated mid-session
- [ ] Updates on next market open only

**[ ] Astro Engine: Daily at startup**
- [ ] Pre-calculated once per day
- [ ] No live scanning
- [ ] Zero runtime cost

**[ ] Cycles: Per candle close**
- [ ] Once per 5-minute candle
- [ ] Not on every tick update
- [ ] Cost: $0.00 (local calculation)

**[ ] Iceberg: Event-driven**
- [ ] Only when large volume detected (>200 contracts)
- [ ] Not continuous scanning
- [ ] Estimated: 5-10 checks per session

**[ ] News: Every 5 minutes**
- [ ] Cached fetch only
- [ ] Not per-tick polling
- [ ] Cost: ~$0.001 per call

### 3.2 API Call Budget

**[ ] Monthly budget: < $100**
- [ ] QMO: 60 calls/day × 20 days = 1,200 calls = FREE
- [ ] Gann: 1 call/day × 20 days = 20 calls = FREE
- [ ] Astro: 1 call/day × 20 days = 20 calls = FREE
- [ ] Iceberg: 10 calls/day × 20 days = 200 calls = ~$2.00
- [ ] News: 288 calls/day × 20 days = 5,760 calls = ~$5.76
- [ ] **Total: ~$7.76/month**

**[ ] Cost alerts configured**
- [ ] Alert if exceeds $50/month
- [ ] Alert if exceeds $1/day
- [ ] Automatic degrade on overage

### 3.3 Request Rate Limiting

**[ ] Global rate limit: 10 API calls/minute**
- [ ] Backend enforces limit
- [ ] Returns 429 on excess
- [ ] User sees: "System busy, try again in 60 seconds"

**[ ] Per-user rate limit: 5 signals/day**
- [ ] Hard-coded in failsafe
- [ ] Resets at market open
- [ ] Prevents abuse/overtrading

---

## ✅ SECTION 4 — FAILSAFE RULES

### 4.1 Rule 1: NO DATA = NO SIGNAL

```python
if price_feed_status != "OK":
    disable_all_signals()
    show("Data feed down. Signals disabled.")
```

**[ ] Implemented**
- [ ] Health check runs every 30 seconds
- [ ] If no price update in 5 minutes: DISABLE signals
- [ ] Auto-recovery when data restored

### 4.2 Rule 2: NEWS LOCKOUT

```python
if news_event_high_impact:
    if time_since_event < 15_minutes:
        force_observe_mode()
```

**[ ] Implemented**
- [ ] Hard stop for 15 minutes post-news
- [ ] All tiers affected equally
- [ ] User sees countdown timer

### 4.3 Rule 3: CONFIDENCE FLOOR

```python
if confidence < 0.70:
    skip_signal()
```

**[ ] Implemented**
- [ ] Cannot generate signals < 70% confidence
- [ ] Failsafe rejects in backend
- [ ] Frontend never sees low-confidence signals

### 4.4 Rule 4: MAX SIGNALS PER SESSION

```python
if signals_today >= 3:
    reject_new_signal()
```

**[ ] Implemented**
- [ ] Counter resets at 9:30 AM ET
- [ ] Hard limit: 3 signals/day
- [ ] Prevents overtrading

### 4.5 Rule 5: HOURLY THROTTLE

```python
if signals_last_hour >= 1:
    wait_until_next_hour()
```

**[ ] Implemented**
- [ ] Max 1 signal per hour
- [ ] Spacing prevents revenge trading
- [ ] Counter resets hourly

### 4.6 Rule 6: LOSS PROTECTION

```python
if consecutive_losses >= 3:
    enter_observer_mode()
```

**[ ] Implemented**
- [ ] Psychology protection
- [ ] Forces break after 3 losses
- [ ] Trader must explicitly restart

### 4.7 Rule 7: MANUAL OVERRIDE AUDIT

```python
if tier == ELITE and manual_override_used:
    log_decision(timestamp, reasoning, result)
```

**[ ] Implemented**
- [ ] Every override logged
- [ ] Available for review
- [ ] Helps improve edge

---

## ✅ SECTION 5 — MEMORY SAFETY

### 5.1 Signal Logging

**[ ] Every signal stored**
- [ ] Timestamp generated
- [ ] Full context captured (QMO phase, IMO zones, Gann levels, confidence)
- [ ] Stored in `signals` table immediately

**[ ] Sample signal log entry**
```json
{
  "timestamp": "2026-01-18T14:35:00Z",
  "trader_phase": "BEGINNER",
  "direction": "SELL",
  "entry": "3361-3365",
  "stop": "3374",
  "targets": ["3342", "3318"],
  "confidence": 0.87,
  "qmo_phase": "DISTRIBUTION",
  "imo_zones": ["3370", "3380"],
  "gann_levels": ["3360", "3375"],
  "reason": "Institutions liquidating long positions",
  "result": null  // filled in when trade closes
}
```

### 5.2 Trade Journal

**[ ] Automatic journaling enabled**
- [ ] Entry timestamp + exit timestamp
- [ ] Win/loss/BE recorded
- [ ] Daily summary generated
- [ ] Edge analysis running

### 5.3 Edge Decay Detection

**[ ] Win rate monitoring**
- [ ] Compare first 10 trades vs last 10 trades
- [ ] Alert if win rate drops > 10%
- [ ] Suggests recalibration

---

## ✅ SECTION 6 — UI STABILITY

### 6.1 Chart Sync

**[ ] Chart updates smoothly**
- [ ] No flickering on signal change
- [ ] Previous signals locked in place
- [ ] New signals display without redrawing chart
- [ ] Tested at 5s, 30s, and 1-min refresh rates

### 6.2 AI Panel Stability

**[ ] Panel never repaints past signals**
- [ ] Signal stays on screen until trader closes it
- [ ] Confidence score never changes retroactively
- [ ] Bias (Bullish/Bearish/Range) doesn't flip without explanation

**[ ] If system uncertain:**
```
Show: "OBSERVE – CONTEXT FORMING"
Don't show: Uncertain signals
```

### 6.3 Latency Testing

**[ ] Chart → Backend → Chart latency < 2 seconds**
- [ ] Tested with network throttle
- [ ] Tested on 4G
- [ ] Tested with 500ms latency simulation

### 6.4 Mobile Responsiveness

**[ ] Frontend responsive on mobile**
- [ ] Charts readable on phone
- [ ] Buttons accessible on mobile
- [ ] Orientation changes handled
- [ ] Touch events work smoothly

---

## ✅ SECTION 7 — SOFT LAUNCH STRATEGY

### Week 1: Private Testing (NO USERS)
- [ ] Manual signal generation + validation
- [ ] Failsafes tested (force data loss, force news event, etc.)
- [ ] Memory logging verified
- [ ] Database backups tested

### Week 2: Trusted User Cohort (5–10 people)
- [ ] Create test accounts
- [ ] Give FREE tier access
- [ ] Daily feedback calls
- [ ] Watch for any crashes/errors
- [ ] Monitor latency
- [ ] No marketing, no announcements

### Week 3: Limited Public (50–100 users)
- [ ] Open BASIC tier ($99/month)
- [ ] Close after 50 users (intentional scarcity)
- [ ] Collect testimonials
- [ ] Monitor support tickets
- [ ] Test payment processing

### Week 4+: Gradual Scale
- [ ] Increase cap by 50 users/week
- [ ] Monitor server load
- [ ] Monitor API costs
- [ ] Monitor support response time
- [ ] Only scale if all metrics green

---

## ✅ SECTION 8 — DAILY TESTING CHECKLIST

**Run EVERY morning before market open:**

- [ ] Price feed connected (check latest timestamp)
- [ ] Database responding (query last signal)
- [ ] News calendar updated (check for today's events)
- [ ] Chart rendering without errors
- [ ] AI panel loads
- [ ] Health check passes (all 10 items green)
- [ ] Generate test signal at 70% confidence (should pass)
- [ ] Generate test signal at 60% confidence (should fail)
- [ ] Test news lockout (manually trigger, verify block)
- [ ] Verify failsafes armed (check code)

**If ANY test fails: DO NOT ALLOW TRADING**

---

## ✅ SECTION 9 — BEFORE ACCEPTING FIRST PAYING USER

### Pre-Flight Checklist (30 minutes before launch)

- [ ] All 10 daily tests passing
- [ ] Database backup verified
- [ ] Monitoring alerts configured
- [ ] Support process ready (email + form)
- [ ] Pricing page live
- [ ] Payment processing tested (test transaction completed)
- [ ] Terms of Service page live
- [ ] Privacy policy page live
- [ ] Risk disclaimer visible
- [ ] Health dashboard public (if desired)

### Launch Checklist (Go/No-Go Decision)

**GO IF:**
- ✅ All 10 daily tests passing
- ✅ Zero crashes in private testing
- ✅ Failsafes verified
- ✅ Data backup working
- ✅ Team ready for support
- ✅ Monitoring alerts configured

**NO-GO IF:**
- ❌ Any unresolved errors
- ❌ Latency > 2 seconds
- ❌ Data feed unstable
- ❌ Failsafes untested
- ❌ No backup recovery plan
- ❌ Team not ready

---

## ✅ SECTION 10 — POST-LAUNCH MONITORING (Week 1)

### Daily Actions (9:00 AM - 4:00 PM ET)
- [ ] Check health dashboard
- [ ] Review error logs
- [ ] Count API calls (must stay < budget)
- [ ] Verify signal accuracy (spot-check)
- [ ] Check user feedback
- [ ] Monitor server CPU/memory
- [ ] Verify backups running

### Daily Handoff (End of Day)
- [ ] Generate daily report
- [ ] Any issues? Escalate immediately
- [ ] Any feedback? Log and prioritize
- [ ] Plan next day

---

## 📋 DEPLOYMENT CHECKLIST SUMMARY

| Category | Items | Status |
|----------|-------|--------|
| Infrastructure | 4 items | [ ] |
| Database | 2 items | [ ] |
| Environment | 1 item | [ ] |
| Monitoring | 2 items | [ ] |
| Data Feeds | 3 items | [ ] |
| Rate Limiting | 3 items | [ ] |
| Failsafes | 7 items | [ ] |
| Memory | 3 items | [ ] |
| UI Stability | 4 items | [ ] |
| Soft Launch | 4 items | [ ] |
| Daily Tests | 10 items | [ ] |
| Pre-Flight | 10 items | [ ] |
| Launch | 6 items | [ ] |
| **TOTAL** | **64 items** | **[ ] [ ] [ ] [ ]** |

---

## 🎯 FINAL DECISION

**Once all 64 items are checked, you are ready to go live.**

This is not optional.
This is institutional discipline.

---

## 🔜 NEXT STEP

You have completed the deployment checklist.

Choose next:

**19️⃣ LEGAL / DISCLAIMER FRAMEWORK**  
Regulatory compliance + risk disclosures

**20️⃣ FINAL DELIVERY PACKAGE**  
"Copy-paste into VS Code" deployment
