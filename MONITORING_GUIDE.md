# Production Monitoring Guide
**Low Cost Groceries - System Health & Monitoring**

---

## **1. Check System Health (Manual)**

Run this anytime to see status of all services:

```bash
ssh root@146.190.129.92 "python3 /root/backend/monitor.py"
```

**You'll see:**
- ✅/❌ Service status (API, Worker, Redis)
- 📦 Job queue size
- ⏱️ API response time
- 💻 CPU/Memory/Disk usage
- 🚨 Recent errors

---

## **2. View Monitoring Logs**

Health checks run **every 5 minutes automatically**.

**View real-time monitoring log:**
```bash
ssh root@146.190.129.92 "tail -f /var/log/grocery-monitor-cron.log"
```

**View latest health report (JSON):**
```bash
ssh root@146.190.129.92 "cat /var/log/grocery-health-report.json"
```

---

## **3. Check Individual Service Logs**

### **API logs (real-time):**
```bash
ssh root@146.190.129.92 "journalctl -u grocery-api.service -f"
```

### **Worker logs (real-time):**
```bash
ssh root@146.190.129.92 "journalctl -u grocery-worker.service -f"
```

### **Redis logs (real-time):**
```bash
ssh root@146.190.129.92 "journalctl -u redis-server.service -f"
```

### **View last 100 lines:**
```bash
ssh root@146.190.129.92 "journalctl -u grocery-api.service -n 100"
ssh root@146.190.129.92 "journalctl -u grocery-worker.service -n 100"
```

---

## **4. Web Monitoring Endpoint**

Check health from anywhere (browser or curl):

**URL:** http://146.190.129.92:8000/api/monitor

**Returns JSON:**
```json
{
  "timestamp": "2025-11-23T17:28:23",
  "api": {
    "status": "online",
    "version": "1.0.0"
  },
  "redis": {
    "status": "connected",
    "queue_size": 0,
    "host": "localhost",
    "port": 6379
  },
  "cache": {
    "size": 0,
    "ttl_seconds": 3600
  }
}
```

**Test with curl:**
```bash
curl http://146.190.129.92:8000/api/monitor
```

---

## **5. Service Management**

### **Restart Services:**
```bash
# Restart API
ssh root@146.190.129.92 "systemctl restart grocery-api.service"

# Restart Worker
ssh root@146.190.129.92 "systemctl restart grocery-worker.service"

# Restart Redis
ssh root@146.190.129.92 "systemctl restart redis-server.service"
```

### **Check Service Status:**
```bash
ssh root@146.190.129.92 "systemctl status grocery-api.service"
ssh root@146.190.129.92 "systemctl status grocery-worker.service"
ssh root@146.190.129.92 "systemctl status redis-server.service"
```

### **Stop/Start Services:**
```bash
# Stop
ssh root@146.190.129.92 "systemctl stop grocery-worker.service"

# Start
ssh root@146.190.129.92 "systemctl start grocery-worker.service"
```

---

## **6. Auto-Restart Configuration**

All services are configured to **auto-restart on crash**:

✅ **API** - Restarts within 10 seconds if it crashes  
✅ **Worker** - Restarts within 10 seconds if it crashes  
✅ **Redis** - Restarts automatically (built-in systemd config)  
✅ **Health checks** - Run every 5 minutes via cron  

**Restart limits:**
- Max 5 restarts within 10 minutes
- After 5 failures, systemd will give up (manual intervention required)

---

## **7. Check If Services Are Running**

Quick status check:
```bash
ssh root@146.190.129.92 "systemctl list-units --type=service --state=running | grep -E '(api|worker|redis)'"
```

Expected output:
```
grocery-api.service            loaded active running Low Cost Groceries API
grocery-worker.service         loaded active running Low Cost Groceries Worker
redis-server.service           loaded active running Advanced key-value store
```

---

## **8. View System Resources**

**CPU, Memory, Disk usage:**
```bash
ssh root@146.190.129.92 "python3 /root/backend/monitor.py"
```

**Detailed system stats:**
```bash
# CPU usage
ssh root@146.190.129.92 "top -bn1 | head -20"

# Memory usage
ssh root@146.190.129.92 "free -h"

# Disk usage
ssh root@146.190.129.92 "df -h"
```

---

## **9. Troubleshooting**

### **Problem: API not responding**

1. Check if service is running:
   ```bash
   ssh root@146.190.129.92 "systemctl status grocery-api.service"
   ```

2. View recent logs:
   ```bash
   ssh root@146.190.129.92 "journalctl -u grocery-api.service -n 100"
   ```

3. Restart service:
   ```bash
   ssh root@146.190.129.92 "systemctl restart grocery-api.service"
   ```

### **Problem: Worker not processing jobs**

1. Check if worker is running:
   ```bash
   ssh root@146.190.129.92 "systemctl status grocery-worker.service"
   ```

2. Check queue size (should decrease over time):
   ```bash
   ssh root@146.190.129.92 "python3 -c 'import redis; r=redis.Redis(); print(f\"Queue: {r.llen(\"scrape_queue\")} jobs\")'"
   ```

3. View worker logs:
   ```bash
   ssh root@146.190.129.92 "journalctl -u grocery-worker.service -f"
   ```

### **Problem: Redis connection errors**

1. Check Redis status:
   ```bash
   ssh root@146.190.129.92 "systemctl status redis-server.service"
   ```

2. Test Redis connection:
   ```bash
   ssh root@146.190.129.92 "redis-cli ping"
   ```
   (Should return: `PONG`)

3. Restart Redis:
   ```bash
   ssh root@146.190.129.92 "systemctl restart redis-server.service"
   ```

---

## **10. Monitoring Best Practices**

✅ **Check health daily** using the web endpoint or manual script  
✅ **Review logs weekly** for patterns or recurring errors  
✅ **Monitor queue size** - if it's constantly growing, add more workers  
✅ **Watch disk usage** - logs can fill up disk space over time  
✅ **Set up alerts** - configure email/Slack notifications for critical errors  

---

## **Quick Reference Commands**

```bash
# Full health check
ssh root@146.190.129.92 "python3 /root/backend/monitor.py"

# Watch API logs live
ssh root@146.190.129.92 "journalctl -u grocery-api.service -f"

# Restart everything
ssh root@146.190.129.92 "systemctl restart grocery-api.service grocery-worker.service"

# Check queue size
curl http://146.190.129.92:8000/api/monitor | python3 -m json.tool

# Check cron is running
ssh root@146.190.129.92 "crontab -l"
```

---

## **Support & Escalation**

If all services are healthy but the system isn't working:
1. Check the Vercel frontend deployment status
2. Test the API directly: `curl http://146.190.129.92:8000/health`
3. Check firewall rules on DigitalOcean droplet
4. Verify SerpAPI key balance: https://serpapi.com/manage-api-key

---

**Last Updated:** November 23, 2025

