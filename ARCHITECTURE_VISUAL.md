# 🏗️ System Architecture - Visual Guide

## Complete Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER (Frontend)                          │
│                                                                  │
│  1. User enters: ["milk", "eggs", "bread"] + ZIP 10001         │
│  2. Submit to API                                               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ POST /cart
                             │ {"items": [...], "zipcode": "10001"}
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DROPLET 1: API + REDIS                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              FastAPI (api.py)                          │    │
│  │                                                        │    │
│  │  1. Generate job_id: "abc-123"                        │    │
│  │  2. Create job_data with ZIP CODE                     │    │
│  │  3. Push to Redis queue                               │    │
│  │  4. Return job_id instantly                           │    │
│  └────────────────┬───────────────────────────────────────┘    │
│                   │                                             │
│                   ▼                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Redis Server                              │    │
│  │                                                        │    │
│  │  Queue: scrape_queue                                  │    │
│  │    [job1, job2, job3, ...]                           │    │
│  │                                                        │    │
│  │  Status: status:abc-123                              │    │
│  │    {"status": "queued", "zip_code": "10001"}        │    │
│  │                                                        │    │
│  │  Results: result:abc-123                             │    │
│  │    (stored after completion)                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ Workers connect via Redis protocol
                             │ (port 6379)
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DROPLET 2: WORKERS                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Worker 1 (worker.py)                                  │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐     │    │
│  │  │  Persistent UC Browser (warm)                │     │    │
│  │  │  - Started once at boot                      │     │    │
│  │  │  - Reused for multiple jobs                  │     │    │
│  │  │  - Auto-restarts every 50 jobs               │     │    │
│  │  └──────────────────────────────────────────────┘     │    │
│  │                                                        │    │
│  │  Loop forever:                                        │    │
│  │    1. Pull job from Redis (blocking)                 │    │
│  │    2. Extract: items + ZIP CODE                      │    │
│  │    3. For each item:                                 │    │
│  │       - search("milk", zip_code="10001")           │    │
│  │       - search("eggs", zip_code="10001")           │    │
│  │       - search("bread", zip_code="10001")          │    │
│  │    4. Store results in Redis                         │    │
│  │    5. Repeat                                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Worker 2 (worker.py)                                  │    │
│  │  [Same structure as Worker 1]                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                             │
                             │ Results stored in Redis
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         USER (Frontend)                          │
│                                                                  │
│  3. Poll: GET /results/abc-123 (every 2 seconds)               │
│                                                                  │
│  Response while processing:                                     │
│    {"status": "processing"}                                     │
│                                                                  │
│  Response when done:                                            │
│    {                                                            │
│      "status": "complete",                                      │
│      "results": {                                               │
│        "milk": [{price: 3.69, merchant: "Walmart"}, ...],     │
│        "eggs": [{price: 2.99, merchant: "Target"}, ...],      │
│        "bread": [{price: 2.49, merchant: "Kroger"}, ...]      │
│      },                                                         │
│      "zip_code": "10001"                                        │
│    }                                                            │
│                                                                  │
│  4. Display cheapest options to user                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Location-Specific Flow (CRITICAL)

```
User in NYC (ZIP 10001)
  │
  ├─> API: job_data = {"zip_code": "10001", ...}
  │
  ├─> Redis: Stores job with ZIP
  │
  ├─> Worker pulls job
  │   │
  │   └─> Logs: 📍 ZIP CODE: 10001 (LOCATION-SPECIFIC)
  │   │
  │   └─> search("milk", zip_code="10001")
  │       │
  │       └─> URL: "milk near zip 10001 nearby"
  │           │
  │           └─> Google returns: NYC stores
  │
  └─> Results: NYC products stored in Redis


User in Miami (ZIP 33101)  
  │
  ├─> API: job_data = {"zip_code": "33101", ...}
  │
  ├─> Redis: Stores job with ZIP
  │
  ├─> Worker pulls job
  │   │
  │   └─> Logs: 📍 ZIP CODE: 33101 (LOCATION-SPECIFIC)
  │   │
  │   └─> search("milk", zip_code="33101")
  │       │
  │       └─> URL: "milk near zip 33101 nearby"
  │           │
  │           └─> Google returns: Miami stores
  │
  └─> Results: Miami products stored in Redis
```

**Key Points:**
1. ZIP code is in the job data (from API)
2. Worker logs ZIP for verification
3. ZIP goes into search URL
4. Google returns location-specific results
5. **Same worker can handle different locations** because ZIP is in URL, not browser state

---

## Timing Breakdown (Per Cart with 10 Items)

```
Sequential Scraping (1 persistent browser):

Item 1 (milk):
  ├─ Navigate to URL: 1.0s
  ├─ Page load: 1.0s  
  ├─ Extract products: 0.5s
  └─ Subtotal: 2.5s

Items 2-10 (eggs, bread, etc.):
  ├─ Navigate to URL: 0.5s (browser already warm)
  ├─ Page load: 0.8s
  ├─ Extract products: 0.3s
  └─ Subtotal per item: 1.6s × 9 = 14.4s

Browser overhead: 1.0s (initialization if cold start)

TOTAL: 2.5 + 14.4 + 1.0 = ~17-18 seconds
```

Compare to:
- **Original plan (fresh browser per cart):** ~37 seconds
- **Our optimization:** ~18 seconds
- **Savings:** 19 seconds (50% faster!)

---

## Scalability Model

```
2 Workers (Minimum Test):
  ├─ Concurrent capacity: 2 carts
  ├─ Time per cart: 18s
  ├─ Throughput: 2 × (3600s / 18s) = 400 carts/hour
  └─ Queue: Others wait in line

10 Workers:
  ├─ Concurrent capacity: 10 carts
  ├─ Time per cart: 18s
  ├─ Throughput: 10 × 200 = 2,000 carts/hour
  └─ Cost: ~5 droplets @ $24 = $120/month

50 Workers:
  ├─ Concurrent capacity: 50 carts
  ├─ Time per cart: 18s
  ├─ Throughput: 50 × 200 = 10,000 carts/hour
  └─ Cost: ~25 droplets @ $24 = $600/month

100 Workers:
  ├─ Concurrent capacity: 100 carts
  ├─ Time per cart: 18s
  ├─ Throughput: 100 × 200 = 20,000 carts/hour
  └─ Cost: ~50 droplets @ $24 = $1,200/month
```

**Linear scaling:** Double workers = Double capacity

---

## Error Handling & Recovery

```
┌─────────────────────────────────────────────────────────┐
│  Error Scenario: Browser Crashes                       │
│                                                         │
│  Worker detects crash                                  │
│    ├─> Log error                                       │
│    ├─> Store failure in Redis                         │
│    ├─> Start new browser                              │
│    └─> Continue with next job                         │
│                                                         │
│  Job marked as "failed"                                │
│    └─> User gets: {"status": "failed", "error": "..."} │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Error Scenario: CAPTCHA Detected                      │
│                                                         │
│  Worker detects CAPTCHA in HTML                        │
│    ├─> Log: "CAPTCHA detected"                        │
│    ├─> Restart browser (fresh session)                │
│    └─> Job fails, but next job gets fresh browser     │
│                                                         │
│  Prevention:                                           │
│    ├─> Auto-restart every 50 jobs                     │
│    ├─> Auto-restart every 30 minutes                  │
│    └─> Use real Chrome (not headless)                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Error Scenario: Redis Connection Lost                 │
│                                                         │
│  API detects Redis is down                             │
│    ├─> Log warning                                     │
│    ├─> Switch to DIRECT mode                          │
│    └─> Scrape synchronously (slow but works)          │
│                                                         │
│  Worker detects Redis is down                          │
│    ├─> Log error                                       │
│    ├─> Wait 10 seconds                                 │
│    └─> Retry connection                                │
└─────────────────────────────────────────────────────────┘
```

---

## Key Files Map

```
lowCostGroceries/
├── backend/
│   ├── api.py                 ← API server (runs on Droplet 1)
│   ├── worker.py              ← Worker script (runs on Droplet 2)
│   └── uc_scraper.py          ← UC scraper (imported by worker)
│
├── test_production_queue.py  ← End-to-end test
│
├── DEPLOYMENT_GUIDE.md        ← Step-by-step setup instructions
├── PRODUCTION_READY_SUMMARY.md ← What was built & why
└── ARCHITECTURE_VISUAL.md     ← This file (visual reference)
```

---

## Quick Reference Commands

### Start API (Droplet 1):
```bash
cd /root/app
export REDIS_HOST=localhost
python3 api.py
```

### Start Workers (Droplet 2):
```bash
cd /root
export REDIS_HOST=YOUR_DROPLET_1_IP
xvfb-run -a python3 worker.py > worker1.log 2>&1 &
xvfb-run -a python3 worker.py > worker2.log 2>&1 &
```

### Monitor Queue:
```bash
redis-cli -h YOUR_DROPLET_1_IP llen scrape_queue
```

### Monitor Workers:
```bash
tail -f /root/worker1.log | grep "ZIP CODE"
```

### Run Test:
```bash
python3 test_production_queue.py
```

---

## Summary

This architecture gives you:

✅ **Fast** - 18s per cart (50% faster than before)  
✅ **Scalable** - Add workers = more capacity  
✅ **Reliable** - Queue handles any load  
✅ **Location-accurate** - ZIP code preserved and verified  
✅ **Cost-effective** - $36/month to test, $600/month for production  

**Ready to deploy!** 🚀

