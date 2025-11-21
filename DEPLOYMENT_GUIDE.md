# 🚀 Production Deployment Guide

## Overview

This guide shows you how to deploy the queue-based scraper architecture with **2 droplets** to prove the system works.

**Architecture:**
```
Droplet 1: Redis + API (lightweight)
Droplet 2: Workers with persistent browsers (heavy lifting)
```

**Performance:**
- Each cart: ~16-20 seconds
- 2 workers: Handle 2 carts simultaneously
- Queue handles unlimited concurrent users

---

## 📋 Prerequisites

### Droplet 1 (Redis + API)
- **Specs:** 2 GB RAM / 1 CPU ($12/month)
- **OS:** Ubuntu 22.04
- **Ports:** 6379 (Redis), 8000 (API)

### Droplet 2 (Workers)
- **Specs:** 4 GB RAM / 2 CPU ($24/month)
- **OS:** Ubuntu 22.04
- **Ports:** None (workers connect to Redis)

---

## 🔧 Droplet 1 Setup (Redis + API)

### Step 1: Install Redis

```bash
# SSH into droplet 1
ssh root@YOUR_DROPLET_1_IP

# Update system
apt-get update
apt-get upgrade -y

# Install Redis
apt-get install -y redis-server

# Configure Redis to accept remote connections
nano /etc/redis/redis.conf
```

**Edit these lines:**
```
# Change this:
bind 127.0.0.1

# To this (allows connections from worker droplet):
bind 0.0.0.0

# Also set a password for security:
requirepass YOUR_SECURE_PASSWORD_HERE
```

**Restart Redis:**
```bash
systemctl restart redis
systemctl enable redis

# Test Redis is running
redis-cli ping
# Should return: PONG
```

### Step 2: Install Python & Dependencies

```bash
# Install Python 3
apt-get install -y python3 python3-pip

# Create app directory
mkdir -p /root/app
cd /root/app

# Install Python packages
pip3 install fastapi uvicorn redis pydantic
```

### Step 3: Upload Files

From your **local machine**:
```bash
# Upload API file
scp backend/api.py root@YOUR_DROPLET_1_IP:/root/app/

# Upload UC scraper (needed for direct mode fallback)
scp backend/uc_scraper.py root@YOUR_DROPLET_1_IP:/root/app/
```

### Step 4: Run API

Back on **Droplet 1**:
```bash
cd /root/app

# Set Redis connection (use localhost since Redis is on same droplet)
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run API
python3 api.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
✅ Connected to Redis at localhost:6379
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it works:**
```bash
# In another terminal
curl http://YOUR_DROPLET_1_IP:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","cache_size":0}
```

---

## 🔧 Droplet 2 Setup (Workers)

### Step 1: Install Dependencies

```bash
# SSH into droplet 2
ssh root@YOUR_DROPLET_2_IP

# Update system
apt-get update
apt-get upgrade -y

# Install Python, Chrome, and Xvfb (virtual display for UC)
apt-get install -y \
    python3 \
    python3-pip \
    chromium-browser \
    chromium-chromedriver \
    xvfb \
    redis-tools

# Install Python packages
pip3 install \
    redis \
    undetected-chromedriver \
    beautifulsoup4 \
    selenium
```

### Step 2: Upload Files

From your **local machine**:
```bash
# Upload worker script
scp backend/worker.py root@YOUR_DROPLET_2_IP:/root/

# Upload UC scraper
scp backend/uc_scraper.py root@YOUR_DROPLET_2_IP:/root/
```

### Step 3: Test Redis Connection

On **Droplet 2**:
```bash
# Test can reach Redis on Droplet 1
redis-cli -h YOUR_DROPLET_1_IP ping

# Should return: PONG
```

If this fails, check firewall rules allow port 6379 between droplets.

### Step 4: Run Workers

```bash
cd /root

# Set Redis connection (point to Droplet 1)
export REDIS_HOST=YOUR_DROPLET_1_IP
export REDIS_PORT=6379
export XVFB=1  # Enable virtual display

# Start Worker 1 (in background with xvfb)
xvfb-run -a python3 worker.py > worker1.log 2>&1 &

# Start Worker 2 (in background with xvfb)
xvfb-run -a python3 worker.py > worker2.log 2>&1 &

# Check workers are running
ps aux | grep worker.py

# View logs
tail -f worker1.log
```

**Expected output:**
```
2024-11-20 [INFO] ================================================================================
2024-11-20 [INFO] 🏭 GOOGLE SHOPPING SCRAPER WORKER
2024-11-20 [INFO] ================================================================================
2024-11-20 [INFO] 🚀 worker-12345 initialized
2024-11-20 [INFO]    Redis: YOUR_DROPLET_1_IP:6379
2024-11-20 [INFO] 🌐 Starting new UC browser...
2024-11-20 [INFO] ✅ Browser ready in 4.2s (xvfb=True)
2024-11-20 [INFO] 🎯 worker-12345 ready, waiting for jobs from Redis...
```

---

## ✅ Test End-to-End

### On Your Local Machine:

```bash
# Edit test script to point to your API
nano test_production_queue.py

# Change this line:
API_BASE_URL = "http://YOUR_DROPLET_1_IP:8000"

# Run test
python3 test_production_queue.py
```

**What the test does:**
1. Submits 3 carts with different ZIP codes (NYC, Miami, Tampa)
2. Polls for results every 2 seconds
3. Verifies results are location-specific
4. Shows timing and success rate

**Expected output:**
```
================================================================================
END-TO-END PRODUCTION QUEUE TEST
================================================================================

📡 Checking API health...
   ✅ API online
   Cache size: 0

================================================================================
PHASE 1: SUBMIT CARTS
================================================================================

📤 Submitting cart: ['milk', 'eggs', 'bread'] in ZIP 10001
   ✅ Job ID: abc123...
   Status: queued
   Queue position: 1

📤 Submitting cart: ['milk', 'eggs'] in ZIP 33101
   ✅ Job ID: def456...
   Status: queued
   Queue position: 2

✅ Submitted 3 jobs

================================================================================
PHASE 2: POLL FOR RESULTS
================================================================================

🔄 Polling for job abc123...
   ⏳ Processing by worker-12345...
   ✅ Complete! (18.2s)

🔄 Polling for job def456...
   ✅ Complete! (14.5s)

================================================================================
FINAL RESULTS
================================================================================

📊 Summary:
   • Submitted: 3 carts
   • Completed: 3 carts
   • Verified: 3 carts

🎉🎉🎉 ALL TESTS PASSED! 🎉🎉🎉

✅ Queue system works
✅ Workers process jobs
✅ Location-specific scraping verified
✅ Ready for production!
```

---

## 🔍 Monitoring & Troubleshooting

### Check Queue Length

```bash
# On Droplet 1 or local machine
redis-cli -h YOUR_DROPLET_1_IP llen scrape_queue

# Returns number of jobs waiting
```

### View Worker Logs

```bash
# On Droplet 2
tail -f /root/worker1.log
tail -f /root/worker2.log

# Look for:
# ✅ = Success
# ❌ = Error
# 📍 ZIP CODE = Verifies location is correct
```

### Check Worker Health

```bash
# On Droplet 2
ps aux | grep worker.py

# Should show 2 processes
```

### Restart Workers

```bash
# On Droplet 2

# Kill old workers
pkill -f worker.py

# Start fresh
xvfb-run -a python3 worker.py > worker1.log 2>&1 &
xvfb-run -a python3 worker.py > worker2.log 2>&1 &
```

### Common Issues

**Issue: Workers can't connect to Redis**
```bash
# Check firewall allows port 6379
ufw allow 6379

# Or use DigitalOcean firewall rules
```

**Issue: UC browser fails to start**
```bash
# Check Xvfb is installed
which Xvfb

# Check Chrome is installed
which chromium-browser

# Try manual test
xvfb-run -a python3 -c "import undetected_chromedriver as uc; uc.Chrome()"
```

**Issue: "No products found"**
```bash
# Check worker logs for CAPTCHA detection
grep -i captcha /root/worker1.log

# If CAPTCHA detected, may need to:
# 1. Reduce browser reuse (restart more frequently)
# 2. Add random delays
# 3. Use residential proxies
```

---

## 📈 Scaling Up

Once you've proven it works with 2 workers, scale horizontally:

### Add More Worker Droplets

1. Clone Droplet 2 to create Droplet 3, 4, 5...
2. Each new droplet automatically connects to same Redis queue
3. No code changes needed!

**Math:**
- 2 workers = ~450 carts/hour
- 10 workers = ~2,250 carts/hour
- 50 workers = ~11,250 carts/hour

### Auto-scale Workers

Use DigitalOcean's API to add/remove worker droplets based on queue length:

```python
queue_length = redis_client.llen('scrape_queue')

if queue_length > 100:
    # Spin up 5 more worker droplets
    create_worker_droplets(5)
elif queue_length < 10:
    # Scale down to save money
    destroy_idle_worker_droplets()
```

---

## 💰 Cost Breakdown

**Minimum test (2 droplets):**
- Droplet 1 (Redis + API): $12/month
- Droplet 2 (2 workers): $24/month
- **Total: $36/month**

**Production (50 workers):**
- Droplet 1 (Redis + API): $12/month
- 25 worker droplets @ $24/month: $600/month
- **Total: $612/month** for 11,000+ carts/hour

Compare to original plan: $5,000/month for similar capacity.

---

## 🎯 Success Criteria

Your system is working correctly when:

- [ ] API returns `job_id` instantly (< 100ms)
- [ ] Workers pick up jobs from queue
- [ ] Carts complete in 16-20 seconds
- [ ] Different ZIP codes return different stores (location verification)
- [ ] Multiple carts process simultaneously
- [ ] System handles queue of 10+ carts without failing

---

## 📞 Next Steps

1. Run `test_production_queue.py` to verify everything works
2. Monitor for 24 hours to check stability
3. Scale to 5-10 workers based on traffic
4. Add monitoring dashboard (Grafana + Prometheus)
5. Implement auto-scaling based on queue length

**FAILURE IS NOT AN OPTION** - and with this architecture, it won't be! 🚀

