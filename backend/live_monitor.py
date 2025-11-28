#!/usr/bin/env python3
"""
Live Monitoring Dashboard
Real-time updates of API requests, queue size, and system health
"""

import requests
import redis
import time
import os
import subprocess
from datetime import datetime
from collections import deque

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
API_URL = 'http://localhost:8000'
REFRESH_INTERVAL = 2  # seconds

# Request tracking
request_history = deque(maxlen=30)  # Last 30 data points (1 minute at 2s intervals)

def clear_screen():
    """Clear terminal screen"""
    # Check if we have a terminal
    if os.environ.get('TERM'):
        os.system('clear' if os.name != 'nt' else 'cls')
    else:
        # No terminal, just print newlines
        print('\n' * 50)

def get_api_stats():
    """Get API request stats from Redis"""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        # Get queue size
        queue_size = r.llen('scrape_queue')
        
        # Count jobs by status
        processing = 0
        completed = 0
        failed = 0
        
        # First, get all jobs with results (these are NOT processing)
        result_job_ids = set()
        for key in r.scan_iter(match='result:*', count=100):
            job_id = key.replace('result:', '')
            result_job_ids.add(job_id)
            
            result_data = r.get(key)
            if result_data:
                try:
                    import json
                    data = json.loads(result_data)
                    if data.get('status') == 'complete':
                        completed += 1
                    elif data.get('status') == 'failed':
                        failed += 1
                except:
                    pass
        
        # Now scan status keys, but SKIP any that have a result (they're done)
        for key in r.scan_iter(match='status:*', count=100):
            job_id = key.replace('status:', '')
            
            # Skip if this job has a result (it's already done)
            if job_id in result_job_ids:
                continue
            
            status_data = r.get(key)
            if status_data:
                try:
                    import json
                    data = json.loads(status_data)
                    status = data.get('status', '')
                    if status == 'processing':
                        processing += 1
                except:
                    pass
        
        return {
            'queue_size': queue_size,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'connected': True
        }
    except Exception as e:
        return {
            'queue_size': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'connected': False,
            'error': str(e)
        }

def get_system_resources():
    """Get CPU, memory, disk usage"""
    try:
        # CPU load average
        with open('/proc/loadavg', 'r') as f:
            load_avg = f.read().split()[0]
        
        # Memory usage
        result = subprocess.run(
            ['free', '-h'],
            capture_output=True,
            text=True,
            timeout=2
        )
        mem_lines = result.stdout.strip().split('\n')
        if len(mem_lines) > 1:
            mem_parts = mem_lines[1].split()
            mem_used = mem_parts[2] if len(mem_parts) > 2 else 'N/A'
            mem_total = mem_parts[1] if len(mem_parts) > 1 else 'N/A'
        else:
            mem_used = mem_total = 'N/A'
        
        # Disk usage
        disk_result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True,
            timeout=2
        )
        disk_lines = disk_result.stdout.strip().split('\n')
        if len(disk_lines) > 1:
            disk_parts = disk_lines[1].split()
            disk_used = disk_parts[2] if len(disk_parts) > 2 else 'N/A'
            disk_percent = disk_parts[4] if len(disk_parts) > 4 else 'N/A'
        else:
            disk_used = disk_percent = 'N/A'
        
        return {
            'cpu_load': load_avg,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'disk_used': disk_used,
            'disk_percent': disk_percent
        }
    except:
        return {
            'cpu_load': 'N/A',
            'mem_used': 'N/A',
            'mem_total': 'N/A',
            'disk_used': 'N/A',
            'disk_percent': 'N/A'
        }

def check_services():
    """Check if systemd services are running"""
    services = {}
    for service in ['grocery-api.service', 'grocery-worker.service', 'redis-server.service']:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True,
                timeout=2
            )
            services[service] = result.stdout.strip() == 'active'
        except:
            services[service] = False
    
    return services

def display_dashboard(stats, system, services):
    """Display the live dashboard"""
    clear_screen()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("=" * 80)
    print(f"🔴 LIVE MONITORING DASHBOARD".center(80))
    print(f"Updated: {now}".center(80))
    print("=" * 80)
    print()
    
    # Services Status
    print("📊 SERVICES STATUS:")
    print("-" * 80)
    api_icon = "🟢" if services.get('grocery-api.service') else "🔴"
    worker_icon = "🟢" if services.get('grocery-worker.service') else "🔴"
    redis_icon = "🟢" if services.get('redis-server.service') else "🔴"
    
    print(f"  {api_icon} API Service       : {'RUNNING' if services.get('grocery-api.service') else 'STOPPED'}")
    print(f"  {worker_icon} Worker Service   : {'RUNNING' if services.get('grocery-worker.service') else 'STOPPED'}")
    print(f"  {redis_icon} Redis Service    : {'RUNNING' if services.get('redis-server.service') else 'STOPPED'}")
    print()
    
    # Redis / Job Queue Stats
    print("📦 JOB QUEUE & REQUESTS:")
    print("-" * 80)
    redis_status = "🟢 CONNECTED" if stats['connected'] else "🔴 DISCONNECTED"
    print(f"  Redis Status      : {redis_status}")
    print(f"  Jobs in Queue     : {stats['queue_size']}")
    print(f"  Currently Processing : {stats['processing']}")
    print(f"  Completed (cached)   : {stats['completed']}")
    print(f"  Failed (cached)      : {stats['failed']}")
    print()
    
    # Request Rate (if we track it)
    if len(request_history) > 1:
        recent_queue_sizes = [r['queue_size'] for r in request_history]
        avg_queue = sum(recent_queue_sizes) / len(recent_queue_sizes)
        print(f"  Avg Queue (1 min) : {avg_queue:.1f} jobs")
    print()
    
    # System Resources
    print("💻 SYSTEM RESOURCES:")
    print("-" * 80)
    print(f"  CPU Load (1 min)  : {system['cpu_load']}")
    print(f"  Memory Used       : {system['mem_used']} / {system['mem_total']}")
    print(f"  Disk Used         : {system['disk_used']} ({system['disk_percent']})")
    print()
    
    # Visual Queue Graph
    if stats['queue_size'] > 0:
        bar_length = min(stats['queue_size'], 60)
        bar = '█' * bar_length
        print("📈 QUEUE SIZE:")
        print("-" * 80)
        print(f"  {bar} {stats['queue_size']} jobs")
        print()
    
    # Instructions
    print("=" * 80)
    print("  Press Ctrl+C to exit".center(80))
    print("  Refreshing every 2 seconds...".center(80))
    print("=" * 80)

def main():
    """Run live monitoring dashboard"""
    print("\n🚀 Starting Live Monitoring Dashboard...")
    print("⏳ Initializing...\n")
    time.sleep(1)
    
    try:
        while True:
            # Collect stats
            stats = get_api_stats()
            system = get_system_resources()
            services = check_services()
            
            # Track history
            request_history.append({
                'timestamp': time.time(),
                'queue_size': stats['queue_size'],
                'processing': stats['processing']
            })
            
            # Display dashboard
            display_dashboard(stats, system, services)
            
            # Wait before next refresh
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
        print("📄 For detailed logs, run:")
        print("   journalctl -u grocery-api.service -f")
        print("   journalctl -u grocery-worker.service -f\n")

if __name__ == '__main__':
    main()

