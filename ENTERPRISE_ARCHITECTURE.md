# 🏗️ Enterprise Architecture - 25K Concurrent Users

## Overview

This document explains how to scale the Google Shopping scraper from a working prototype to an enterprise-grade system that can handle **25,000 concurrent users**.

**Current Status:** ✅ Working scraper that takes ~37 seconds for 10 items  
**Goal:** Handle 25K users efficiently using distributed workers and a job queue

---

## 🎯 The Problem

**Why we can't just run scrapers directly in the API:**
- Each scrape takes **~37 seconds**
- HTTP requests timeout after 30 seconds typically
- API server gets blocked waiting for scrapes
- Can't handle concurrent users efficiently

**The Solution: Job Queue Architecture**

---

## 🏛️ Architecture Diagram

```
┌─────────────┐
│   USERS     │ (25,000 concurrent)
│   Frontend  │
└──────┬──────┘
       │
       │ 1. POST /cart (items, zip)
       │ 2. Returns job_id instantly
       │ 3. Poll GET /results/{job_id}
       │
┌──────▼──────────────┐
│   API GATEWAY       │ (2 droplets)
│   FastAPI Backend   │
│   - Accept requests │
│   - Add to queue    │
│   - Return job_id   │
│   - Serve results   │
└──────┬──────────────┘
       │
       │ Push jobs / Pull results
       │
┌──────▼──────────────┐
│      REDIS          │ (1-2 droplets)
│   Message Queue     │
│   - Job queue       │
│   - Results cache   │
│   - Worker status   │
└──────┬──────────────┘
       │
       │ Workers pull jobs
       │
┌──────▼──────────────────────────────┐
│         WORKER POOL                  │
│   (100 droplets, 2-3 workers each)  │
│                                      │
│  Droplet 1:                          │
│   ├─ Worker 1 (UC browser)          │
│   ├─ Worker 2 (UC browser)          │
│   └─ Worker 3 (UC browser)          │
│                                      │
│  Droplet 2:                          │
│   ├─ Worker 1 (UC browser)          │
│   ├─ Worker 2 (UC browser)          │
│   └─ Worker 3 (UC browser)          │
│                                      │
│  ... (98 more droplets)              │
│                                      │
│  Total: 200-300 concurrent scrapers  │
└──────────────────────────────────────┘
```

---

## 📋 Components Explained

### 1. API Gateway (FastAPI Backend)

**Purpose:** Accept user requests, manage job queue, return results

**What it does:**
- Receives user cart requests (items + ZIP code)
- Generates unique `job_id` for each request
- Pushes job to Redis queue
- Returns `job_id` to user **instantly** (no waiting!)
- Provides endpoint to check job status and get results

**Endpoints:**
- `POST /cart` - Submit scraping job
- `GET /results/{job_id}` - Check status and get results
- `GET /health` - System health check

### 2. Redis Queue

**Purpose:** Central message queue and results storage

**What it stores:**
1. **Job Queue** (`scrape_queue`): Pending jobs waiting to be processed
2. **Results Cache** (`result:{job_id}`): Completed scraping results
3. **Worker Status** (optional): Which workers are alive/busy

**Why Redis?**
- Fast (in-memory)
- Built-in queue operations (LPUSH, BRPOP)
- Atomic operations (thread-safe)
- Can persist to disk (optional)

### 3. Worker Pool (100 Droplets)

**Purpose:** Do the actual scraping work

**What each worker does:**
1. Pulls a job from Redis queue (blocking operation)
2. Scrapes Google Shopping using UC (`backend/uc_scraper.py`)
3. Stores results back in Redis
4. Repeats forever

**Each droplet runs:**
- 2-3 worker processes (each with its own UC browser)
- Xvfb (virtual display for headless UC)
- All workers independently pull from the same queue

---

## 🔄 User Flow Example

### Step-by-Step:

**1. User submits cart:**
```
POST /cart
{
  "items": ["milk", "eggs", "bread"],
  "zipcode": "10001"
}
```

**2. API Gateway response (instant - 0.1s):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "queued",
  "estimated_time": 37
}
```

**3. Frontend starts polling (every 2 seconds):**
```
GET /results/abc-123-def-456

Response (while working):
{
  "status": "processing",
  "progress": "2/3 items completed"
}

Response (after 37 seconds):
{
  "status": "complete",
  "results": {
    "milk": [{...products...}],
    "eggs": [{...products...}],
    "bread": [{...products...}]
  }
}
```

**4. User sees results!**

---

## 💻 Implementation Guide

### Part 1: Update API Gateway

**File: `backend/api.py`**

```python
import redis
import uuid
import json
from datetime import datetime

# Connect to Redis
redis_client = redis.Redis(host='redis-droplet-ip', port=6379, decode_responses=True)

@app.post("/cart")
async def submit_cart(request: CartRequest):
    """Submit scraping job to queue - returns immediately"""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job data
    job_data = {
        'job_id': job_id,
        'items': request.items,
        'zip_code': request.zipcode,
        'submitted_at': datetime.now().isoformat(),
        'max_products_per_item': 20
    }
    
    # Push to Redis queue
    redis_client.lpush('scrape_queue', json.dumps(job_data))
    
    # Set initial status
    redis_client.setex(
        f'status:{job_id}',
        3600,  # 1 hour expiry
        json.dumps({'status': 'queued'})
    )
    
    return {
        'job_id': job_id,
        'status': 'queued',
        'estimated_time': len(request.items) * 3.7  # ~3.7s per item
    }

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Check job status and get results"""
    
    # Check for results first
    result = redis_client.get(f'result:{job_id}')
    if result:
        return {
            'status': 'complete',
            'results': json.loads(result)
        }
    
    # Check status
    status = redis_client.get(f'status:{job_id}')
    if status:
        return json.loads(status)
    
    # Not found
    return {
        'status': 'not_found',
        'message': 'Job ID not found or expired'
    }
```

### Part 2: Create Worker Script

**File: `backend/worker.py`**

```python
#!/usr/bin/env python3
"""
Worker process that pulls jobs from Redis and scrapes products
Run multiple instances of this on each droplet
"""

import redis
import json
import time
import logging
from uc_scraper import search_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Redis
redis_client = redis.Redis(
    host='redis-droplet-ip',
    port=6379,
    decode_responses=True
)

def process_job(job_data):
    """Process a single scraping job"""
    job_id = job_data['job_id']
    items = job_data['items']
    zip_code = job_data['zip_code']
    max_products = job_data.get('max_products_per_item', 20)
    
    logger.info(f"[{job_id}] Starting scrape: {len(items)} items in ZIP {zip_code}")
    
    try:
        # Update status to processing
        redis_client.setex(
            f'status:{job_id}',
            3600,
            json.dumps({
                'status': 'processing',
                'started_at': time.time()
            })
        )
        
        # DO THE SCRAPING (using our proven UC scraper!)
        results = search_products(
            search_terms=items,
            zip_code=zip_code,
            max_products_per_item=max_products,
            use_parallel=False  # Sequential with persistent browser
        )
        
        # Store results in Redis
        redis_client.setex(
            f'result:{job_id}',
            3600,  # Keep results for 1 hour
            json.dumps(results)
        )
        
        logger.info(f"[{job_id}] ✅ Complete! Found products for {len(results)} items")
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Error: {e}")
        
        # Store error in Redis
        redis_client.setex(
            f'result:{job_id}',
            3600,
            json.dumps({
                'error': str(e),
                'status': 'failed'
            })
        )

def main():
    """Main worker loop - runs forever"""
    logger.info("🚀 Worker started, waiting for jobs...")
    
    while True:
        try:
            # Block and wait for a job (timeout after 5 seconds)
            job = redis_client.brpop('scrape_queue', timeout=5)
            
            if job:
                # job is a tuple: (queue_name, job_data)
                job_data = json.loads(job[1])
                process_job(job_data)
            else:
                # No jobs available, just loop
                logger.debug("No jobs in queue, waiting...")
                
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main()
```

### Part 3: Frontend Polling

**File: `frontend/src/api.js`**

```javascript
// Submit cart for scraping
async function submitCart(items, zipcode) {
  const response = await fetch('/cart', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ items, zipcode })
  });
  
  const data = await response.json();
  // Returns: { job_id: "...", status: "queued", estimated_time: 37 }
  
  return data.job_id;
}

// Poll for results
async function pollResults(jobId, onUpdate) {
  const poll = async () => {
    const response = await fetch(`/results/${jobId}`);
    const data = await response.json();
    
    if (data.status === 'complete') {
      // Done! Show results
      onUpdate({ status: 'complete', results: data.results });
      return; // Stop polling
    } else if (data.status === 'failed') {
      // Error
      onUpdate({ status: 'error', error: data.error });
      return;
    } else {
      // Still processing, keep polling
      onUpdate({ status: 'processing' });
      setTimeout(poll, 2000); // Check again in 2 seconds
    }
  };
  
  poll(); // Start polling
}

// Usage:
const jobId = await submitCart(['milk', 'eggs'], '10001');
pollResults(jobId, (status) => {
  if (status.status === 'complete') {
    console.log('Results:', status.results);
  } else {
    console.log('Still working...');
  }
});
```

---

## 🚀 Deployment Steps

### 1. Setup Redis Server (1 droplet)

```bash
# On Redis droplet:
apt-get update
apt-get install -y redis-server

# Edit config to allow remote connections
nano /etc/redis/redis.conf
# Change: bind 127.0.0.1 -> bind 0.0.0.0

# Restart Redis
systemctl restart redis
```

### 2. Setup API Gateway (2 droplets for redundancy)

```bash
# On API droplets:
apt-get update
apt-get install -y python3 python3-pip

# Install dependencies
pip3 install fastapi uvicorn redis

# Copy files
scp backend/api.py root@api-droplet:/root/

# Run API (with load balancer in front)
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 3. Setup Worker Droplets (100 droplets)

```bash
# On each worker droplet:
apt-get update
apt-get install -y python3 python3-pip xvfb chromium-browser redis-tools

# Install Python packages
pip3 install undetected-chromedriver beautifulsoup4 redis

# Copy scraper and worker
scp backend/uc_scraper.py root@worker:/root/
scp backend/worker.py root@worker:/root/

# Start 3 workers (run in background with systemd or supervisor)
xvfb-run -a python3 worker.py &
xvfb-run -a python3 worker.py &
xvfb-run -a python3 worker.py &
```

### 4. Create Systemd Service (for auto-restart)

**File: `/etc/systemd/system/scraper-worker@.service`**

```ini
[Unit]
Description=Google Shopping Scraper Worker %i
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac &
ExecStart=/usr/bin/python3 /root/worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable 3 workers
systemctl enable scraper-worker@1
systemctl enable scraper-worker@2
systemctl enable scraper-worker@3

# Start them
systemctl start scraper-worker@1
systemctl start scraper-worker@2
systemctl start scraper-worker@3
```

---

## 📊 Performance Calculations

### Current Performance:
- **1 scrape**: ~37 seconds for 10 items
- **1 worker**: Can complete ~97 jobs/hour (3600s / 37s)

### With 100 Droplets:
- **300 workers** (100 droplets × 3 workers each)
- **Throughput**: 300 workers × 97 jobs/hour = **29,100 jobs/hour**
- **Users/minute**: ~485 users/minute
- **Concurrent capacity**: Can handle queue of 25K users in ~51 minutes

### Peak Load Handling:
If 25,000 users submit at once:
- All enter queue instantly (< 1 second)
- First 300 start immediately (0s wait)
- User #1000 waits: ~2 minutes
- User #10000 waits: ~20 minutes
- User #25000 waits: ~51 minutes

**This is acceptable!** Users get instant feedback (job_id) and can see their position in queue.

---

## 🔧 Optimizations & Advanced Features


---

## 🎯 What the Next Agent Needs to Do

### Immediate Tasks:

1. ✅ **Scraper is ready** (`backend/uc_scraper.py`)
2. ⏳ **Update API** to use job queue pattern
3. ⏳ **Create worker.py** script
4. ⏳ **Setup Redis** on a droplet
5. ⏳ **Deploy workers** to 100 droplets
6. ⏳ **Update frontend** to poll for results
7. ⏳ **Add monitoring** (queue length, worker health)

### Testing Checklist:

- [ ] Single job processes correctly
- [ ] Multiple jobs process in parallel
- [ ] Queue handles 1000+ jobs without issues
- [ ] Workers restart if they crash
- [ ] Results expire after 1 hour
- [ ] Frontend polling works smoothly

---

## 📚 Key Files Reference

**Current (Working):**
- `backend/uc_scraper.py` - Production scraper (✅ READY)
- `backend/api.py` - Basic API (needs queue integration)

**Need to Create:**
- `backend/worker.py` - Worker process (template provided above)
- `frontend/polling.js` - Frontend polling logic
- `/etc/systemd/system/scraper-worker@.service` - Systemd service

**Need to Install:**
- Redis server (on 1 droplet)
- Python redis package on all droplets: `pip3 install redis`

---

## 🚨 Common Pitfalls to Avoid

1. **Don't** run scrapers in the API process (blocks server)
2. **Don't** forget to set Redis TTL (results will fill memory)
3. **Don't** use polling intervals < 1 second (unnecessary load)
4. **Don't** forget Xvfb on workers (UC needs display)
5. **Don't** use too many workers per droplet (3 max recommended)

---

## 💡 Summary

**The Big Idea:**
- Users → API → Redis Queue → Workers → Results → Users
- Workers pull jobs independently (self-distributing)
- No complex orchestration needed
- Scales horizontally (add more workers = more capacity)

**Current State:**
- ✅ Scraper works perfectly (37s for 10 items)
- ✅ Locality proven (different stores per ZIP)
- ✅ Fast (0.5-1s wait times)

**Next State:**
- Add Redis queue
- Deploy 100 worker droplets
- Update API for async pattern
- **Ready for 25K users!**

---

**Questions?** Everything you need is in this document. The scraper is done and working. Now it's just about wrapping it in a queue architecture! 🚀

