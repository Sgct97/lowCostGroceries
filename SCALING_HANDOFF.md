# SCALING HANDOFF DOCUMENT
**Project:** Low Cost Groceries - AI-Powered Price Comparison
**Date:** November 21, 2025
**Target Scale:** 25,000 users, 2,500 concurrent (10%)

---

## TABLE OF CONTENTS
1. [Current System Overview](#current-system-overview)
2. [What's Working Now](#whats-working-now)
3. [Parallelization History - What Failed](#parallelization-history---what-failed)
4. [Technical Constraints](#technical-constraints)
5. [Scaling Requirements](#scaling-requirements)
6. [Proposed Solutions](#proposed-solutions)
7. [Implementation Roadmap](#implementation-roadmap)

---

## CURRENT SYSTEM OVERVIEW

### Architecture
```
┌─────────────────┐
│  Frontend       │ (HTML/CSS/JS)
│  localhost:8080 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Droplet    │ (146.190.129.92)
│  - FastAPI      │
│  - Redis        │
│  - AI Service   │
└────────┬────────┘
         │
         ▼ (Redis Queue)
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Worker│  │Worker│
│Drop 2│  │Drop 3│
└──────┘  └──────┘
 2 workers  2 workers
```

### Droplet Configuration
- **Droplet 1** (API): 2GB RAM, 1 vCPU, Ubuntu 22.04
  - Redis (1 instance)
  - FastAPI (1 instance)
  - AI Service (OpenAI GPT-5-mini)
  
- **Droplet 2** (Worker): 2GB RAM, 2 vCPU, Ubuntu 22.04
  - 2x grocery-worker@{1,2} systemd services
  - Each worker: 1 persistent Chrome browser
  
- **Droplet 3** (Worker): 2GB RAM, 2 vCPU, Ubuntu 22.04
  - 2x grocery-worker@{1,2} systemd services
  - Each worker: 1 persistent Chrome browser

**Total Current Capacity:** 4 workers across 2 droplets

---

## WHAT'S WORKING NOW

### ✅ Successfully Implemented

1. **AI Layer (GPT-5-mini Integration)**
   - User types "milk" → AI suggests "Whole Milk, 1 Gallon"
   - Contextual suggestions based on cart
   - 1200ms debounce for multi-word inputs
   - ~$0.001 per clarification

2. **Hybrid Toggle Feature**
   - "Prioritize nearby stores" ON: Only "In stores nearby" section (10 products, $2.34 lowest)
   - "Prioritize nearby stores" OFF: All products (50+ products, $1.29 lowest)
   - User choice: Accuracy vs Best Price

3. **Accurate Price Extraction**
   - Fixed regex: `r'\$(\d+\.\d+|\d+)'`
   - Extract price BEFORE splitting aria-label
   - Lazy loading: Scroll to load all products

4. **Persistent Browser Workers**
   - Each worker keeps Chrome open for ~50 jobs or 30 minutes
   - 4s faster per job vs cold start
   - Reliable undetected-chromedriver stealth

5. **Enterprise UI**
   - Modern gradient design
   - Professional shadows & typography
   - Responsive, accessible

### Performance Metrics (Single Worker)
- **Search Time:** 6-8 seconds per item
- **10-item cart:** ~60 seconds total
- **Worker restart:** Every 50 jobs or 30 minutes
- **Success Rate:** 95%+ (Google Shopping stability)

---

## PARALLELIZATION HISTORY - WHAT FAILED

### Attempt 1: 5 Parallel Workers per Droplet
**Date:** Mid-project
**Configuration:** 5x workers on each 2GB/2vCPU droplet

**What Happened:**
- Chrome browsers crashed randomly
- Workers hung indefinitely
- Memory exhaustion (OOM killer)
- Xvfb display conflicts

**Why It Failed:**
- **Memory:** Each Chrome instance uses ~500-800MB RAM
- **5 workers × 800MB = 4GB needed** (droplet only has 2GB)
- **CPU contention:** 2 vCPUs shared across 5 Chrome instances
- **Xvfb:** Display server overhead for each headless browser

**Test Output:**
```
parallel_uc_test_results.txt:
- 2 workers: ✓ Success (both complete)
- 3 workers: ⚠️ Partial (2 complete, 1 hung)
- 4 workers: ⚠️ Partial (2 complete, 2 hung)
- 5 workers: ✗ Failure (1 complete, 4 crashed/hung)
```

### Attempt 2: Multiprocessing Parallel
**File:** `test_multiprocess_parallel.py`

**What Happened:**
- Workers started but didn't complete
- Process deadlocks
- Redis connection pool exhaustion

**Why It Failed:**
- **undetected-chromedriver** doesn't play well with multiprocessing
- Selenium WebDriver isn't multiprocess-safe
- Chrome profiles conflict when forked

### Attempt 3: Playwright Parallel
**Files:** `test_playwright_parallel.py`, `test_playwright_stealth_parallel.py`

**What Happened:**
- Faster startup than Selenium
- But: Google Shopping detected Playwright
- CAPTCHA rate: ~40%

**Why It Failed:**
- **Detection:** Google Shopping's bot detection is aggressive
- **Stealth plugins:** Not as effective as undetected-chromedriver
- **Reliability:** 40% CAPTCHA rate is unacceptable

### Attempt 4: Threading
**Result:** Not attempted (Selenium is not thread-safe)

---

## TECHNICAL CONSTRAINTS

### 1. Chrome Memory Usage
**Per Browser Instance:**
- Base Chrome: ~200-300MB
- With extensions (stealth): ~300-400MB
- With loaded page: ~500-800MB
- **Peak usage:** Up to 1GB per instance

### 2. CPU Bottlenecks
**Chrome is CPU-intensive:**
- JavaScript execution (Google Shopping is heavy JS)
- Rendering (even headless)
- Image decoding
- Network stack

**2 vCPU droplet:**
- Can comfortably handle **2 Chrome instances**
- 3rd instance causes CPU thrashing
- 4+ instances: severe performance degradation

### 3. Xvfb Overhead
- Display server for headless Chrome
- ~50-100MB per display
- I/O overhead for virtual framebuffer

### 4. undetected-chromedriver Limitations
- **Must use Selenium** (not Playwright, Puppeteer)
- **Not multiprocess-safe** (uses process patching)
- **One browser per process** is safest

### 5. Network Bandwidth
- Each search: ~2-5MB HTML + images
- 10 concurrent searches: 20-50MB/s
- Droplet bandwidth: 2TB/month = ~6Mbps sustained
- **Not a bottleneck yet** but could be at 50+ workers

---

## SCALING REQUIREMENTS

### Target: 2,500 Concurrent Users (10% of 25k)

**Assumptions:**
- Average cart: 5 items
- Search time: 7 seconds per item
- Total job time: 35 seconds per user
- **Worker capacity:** 35 seconds / user

**Calculation:**
- 2,500 users × 35 seconds = 87,500 worker-seconds needed
- If jobs arrive evenly over 1 hour: 87,500s / 3600s = **24 workers minimum**
- **With safety margin (2x):** 50 workers recommended

### Current Capacity vs Required
| Metric | Current | Required | Gap |
|--------|---------|----------|-----|
| Workers | 4 | 50 | 46 |
| Droplets | 2 | 13 | 11 |
| RAM (total) | 4GB | 100GB | 96GB |
| vCPUs (total) | 4 | 100 | 96 |

---

## PROPOSED SOLUTIONS

### Option 1: Horizontal Scaling (More Droplets) ⭐ RECOMMENDED
**Strategy:** 2 workers per 2GB/2vCPU droplet (proven stable)

**Math:**
- 50 workers needed
- 2 workers per droplet
- **25 droplets required**

**Costs:**
- Droplet: $12/month (2GB/2vCPU)
- 25 droplets × $12 = **$300/month**
- API droplet: $12/month
- **Total: $312/month**

**Pros:**
✅ Proven stable (already works with 2 workers/droplet)
✅ Simple deployment (copy systemd config)
✅ Fault tolerant (one droplet dies = 2% capacity loss)
✅ Easy to scale up/down dynamically

**Cons:**
❌ More management overhead (25 servers)
❌ More expensive than single large server
❌ Network latency between Redis and workers

**Implementation:**
1. Create Terraform/Ansible config for automatic droplet provisioning
2. Deploy worker code to all droplets
3. Configure systemd services (grocery-worker@{1,2})
4. Load balancer for Redis queue consumption

### Option 2: Vertical Scaling (Bigger Droplets)
**Strategy:** Larger droplets with more RAM/CPU

**Configuration:**
- Use 8GB / 4vCPU droplets ($48/month)
- Run 6 workers per droplet (800MB × 6 = 4.8GB)
- 50 workers / 6 = **9 droplets**

**Costs:**
- 9 droplets × $48 = **$432/month**

**Pros:**
✅ Fewer servers to manage
✅ Better resource utilization

**Cons:**
❌ **NOT TESTED** - unknown if 6 workers will be stable
❌ Higher blast radius (one droplet dies = 12% capacity loss)
❌ More expensive per month
❌ Risk of same memory/CPU contention issues

**Testing Required:**
- Spin up 8GB droplet
- Test 4, 5, 6 workers in parallel
- Monitor memory, CPU, success rate

### Option 3: Hybrid Cloud + Queue-Based Autoscaling
**Strategy:** Use Kubernetes + autoscaling based on Redis queue depth

**Architecture:**
```
Redis Queue (depth monitoring)
     ↓
Kubernetes HPA (Horizontal Pod Autoscaler)
     ↓
Scale 1-100 worker pods dynamically
```

**Costs:**
- DigitalOcean Kubernetes: $12/month (cluster)
- Worker pods: ~$0.01/hour per worker
- At full scale (50 workers): $12 + (50 × 730 × 0.01) = **$377/month**
- At low scale (10 workers): $12 + (10 × 730 × 0.01) = **$85/month**

**Pros:**
✅ Auto-scales based on demand
✅ Only pay for workers you use
✅ Professional infrastructure
✅ Easy to scale beyond 50 workers

**Cons:**
❌ Complex setup (Kubernetes learning curve)
❌ Requires container images (Docker)
❌ More moving parts

### Option 4: Serverless (AWS Lambda / Google Cloud Functions)
**Strategy:** Each scrape job = one Lambda invocation

**Why This WON'T Work:**
❌ Lambda timeout: 15 minutes max (we need 35+ seconds per job)
❌ Chrome in Lambda: Requires large Docker image (200MB+)
❌ Cold start penalty: 5-10 seconds per invocation
❌ Memory limits: 10GB max (Chrome needs reliable RAM)
❌ **Cost:** $0.20 per 1GB-second × 35 seconds × 2,500 jobs = $17,500/month 💀

**Verdict:** Not viable

---

## RECOMMENDED SOLUTION: OPTION 1 (HORIZONTAL SCALING)

### Why This is Best
1. **Proven Stable:** Already running 2 workers per 2GB droplet successfully
2. **Low Risk:** No unknowns, just replicate what works
3. **Cost Effective:** $312/month for 2,500 concurrent users = $0.12 per user
4. **Fault Tolerant:** Distributed across 25 servers
5. **Easy Implementation:** Automation scripts deploy workers in minutes

### Implementation Plan

#### Phase 1: Automation (Week 1)
**Goal:** One-command droplet provisioning

1. Create Terraform config:
```hcl
# terraform/workers.tf
resource "digitalocean_droplet" "worker" {
  count  = 25
  image  = "ubuntu-22-04-x64"
  name   = "grocery-worker-${count.index}"
  region = "sfo3"
  size   = "s-1vcpu-2gb"
  
  ssh_keys = [var.ssh_key_id]
  
  user_data = file("cloud-init.sh")
}
```

2. Cloud-init script:
```bash
#!/bin/bash
# Install dependencies
apt-get update
apt-get install -y python3-pip chromium-chromedriver xvfb redis-tools

# Clone repo
cd /root
git clone https://github.com/Sgct97/lowCostGroceries.git
cd lowCostGroceries

# Install Python deps
pip3 install -r requirements.txt

# Configure systemd services
cp systemd/grocery-worker@.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now grocery-worker@{1,2}
```

3. Deploy:
```bash
cd terraform
terraform init
terraform apply
# Creates 25 droplets in ~5 minutes
```

#### Phase 2: Monitoring (Week 2)
**Goal:** Visibility into worker health

1. Add Prometheus metrics to workers:
```python
# backend/worker.py
from prometheus_client import Counter, Histogram, Gauge

jobs_completed = Counter('worker_jobs_completed_total', 'Total jobs completed')
job_duration = Histogram('worker_job_duration_seconds', 'Job duration')
active_jobs = Gauge('worker_active_jobs', 'Currently processing jobs')
```

2. Centralized Grafana dashboard:
   - Jobs/second across all workers
   - Success rate
   - Average job duration
   - Queue depth

3. Alerts:
   - Worker down
   - Success rate < 90%
   - Queue depth > 100

#### Phase 3: Load Testing (Week 3)
**Goal:** Verify 2,500 concurrent capacity

1. Load test script:
```python
# test_load.py
import asyncio
import aiohttp

async def submit_job():
    async with aiohttp.ClientSession() as session:
        await session.post('http://146.190.129.92:8000/api/cart', json={
            'items': ['milk', 'eggs', 'bread', 'chicken', 'rice'],
            'zipcode': '33773',
            'prioritize_nearby': True
        })

async def main():
    # Simulate 2,500 concurrent users
    tasks = [submit_job() for _ in range(2500)]
    await asyncio.gather(*tasks)

asyncio.run(main())
```

2. Monitor:
   - Time to process all 2,500 jobs
   - Success rate
   - Memory usage per worker
   - CPU usage per worker

3. Target metrics:
   - **Time to complete:** < 5 minutes (2,500 jobs / 50 workers × 7s = 350s)
   - **Success rate:** > 95%
   - **Memory per worker:** < 1.5GB
   - **CPU per worker:** < 80%

#### Phase 4: Auto-Scaling (Week 4)
**Goal:** Dynamic worker scaling based on demand

1. Monitor Redis queue depth:
```python
# backend/autoscaler.py
import redis
import requests

r = redis.Redis(host='localhost', port=6379)

while True:
    queue_depth = r.llen('scrape_queue')
    
    if queue_depth > 100:
        # Scale up: Add 5 more droplets
        requests.post('https://api.digitalocean.com/v2/droplets', ...)
    elif queue_depth < 10 and num_workers > 10:
        # Scale down: Remove 5 droplets
        requests.delete('https://api.digitalocean.com/v2/droplets/...')
    
    time.sleep(60)
```

2. Scaling rules:
   - Queue depth > 100: Add 10 workers (5 droplets)
   - Queue depth < 10: Remove 10 workers (5 droplets)
   - Min workers: 10 (always on)
   - Max workers: 100 (hard limit)

---

## COST ANALYSIS

### Monthly Costs at Scale

| Configuration | Workers | Droplets | Cost/Month |
|---------------|---------|----------|------------|
| **Current** | 4 | 3 | $36 |
| **Target (Option 1)** | 50 | 26 | $312 |
| **With Autoscaling** | 10-100 | 6-51 | $72-$612 |

### Cost Per User
- $312/month / 25,000 users = **$0.0125 per user**
- If 10% concurrent (2,500): $312/month / 2,500 = **$0.12 per concurrent user**

### Revenue Requirements (Break-Even)
- At $0.50/search: 624 searches/month needed
- At $1/month subscription: 312 subscribers needed
- At $5/month subscription: 63 subscribers needed

---

## PERFORMANCE OPTIMIZATIONS (Future)

### 1. Cache Popular Searches (Redis)
```python
# Cache search results for 5 minutes
cached = redis.get(f'search:{item}:{zipcode}')
if cached:
    return json.loads(cached)

# Scrape and cache
results = scraper.search(item, zipcode)
redis.setex(f'search:{item}:{zipcode}', 300, json.dumps(results))
```

**Impact:** 50% reduction in scraping for common items (milk, eggs, bread)

### 2. Batch Similar Searches
- If 10 users search "milk" in same ZIP within 1 minute
- Batch into single scrape, share results
- **Reduction:** 10x fewer scrapes for popular items

### 3. Smarter Worker Allocation
- Route jobs by ZIP code to specific workers
- Workers cache location-specific results
- **Benefit:** Faster subsequent searches in same area

### 4. Preemptive Scraping
- Scrape top 100 items × top 100 ZIP codes overnight
- Cache results for daytime traffic
- **Benefit:** Instant responses for 80% of searches

---

## CRITICAL RISKS & MITIGATION

### Risk 1: Google Shopping Bot Detection
**Probability:** Medium
**Impact:** High (entire system fails)

**Mitigation:**
- Rotate IP addresses (use DigitalOcean's different regions)
- Randomize search timing (add 1-3s random delay)
- Rotate user agents
- Monitor CAPTCHA rate (alert if > 5%)
- Have fallback to different scraping source (Instacart, Walmart API)

### Risk 2: Worker Droplet Failures
**Probability:** Medium
**Impact:** Low (fault tolerant)

**Mitigation:**
- Health checks every 30 seconds
- Auto-restart failed workers
- Remove unhealthy droplets from rotation
- Provision 10% extra capacity

### Risk 3: Redis Queue Overflow
**Probability:** Low
**Impact:** High (jobs lost)

**Mitigation:**
- Monitor queue depth (alert at 1,000)
- Set max queue size (10,000)
- Persist queue to disk (Redis AOF)
- Scale workers when queue > 100

### Risk 4: Cost Overrun
**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Set hard limit: 51 droplets max
- Monitor spend daily
- Auto-scale down aggressively
- Alert if monthly cost > $500

---

## CONCLUSION

### What You Need to Do Next

1. **Decide on scaling strategy:**
   - **Recommended:** Option 1 (Horizontal Scaling)
   - 25 droplets × 2 workers = 50 workers
   - $312/month for 2,500 concurrent users

2. **Implement automation:**
   - Terraform for droplet provisioning
   - Ansible for worker configuration
   - One-command deployment

3. **Add monitoring:**
   - Prometheus + Grafana
   - Track jobs/second, success rate, queue depth

4. **Load test:**
   - Simulate 2,500 concurrent users
   - Verify < 5 minute completion time

5. **Implement auto-scaling:**
   - Queue-based triggers
   - Scale 10-100 workers dynamically

### Timeline
- **Week 1:** Automation scripts
- **Week 2:** Monitoring setup
- **Week 3:** Load testing
- **Week 4:** Auto-scaling
- **Week 5:** Production rollout

### Final Recommendation
**Go with Option 1 (Horizontal Scaling).** It's proven, low-risk, and cost-effective. You can always optimize later with caching, batching, and preemptive scraping.

The current 2-worker-per-droplet configuration is **stable and reliable**. Don't try to squeeze 5+ workers onto one machine—you'll hit the same memory/CPU issues we saw before. Scale horizontally with more droplets instead.

**Target:** 25 droplets, 50 workers, $312/month, 2,500 concurrent users ✅

