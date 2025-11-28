#!/usr/bin/env python3
"""
Production Monitoring Script for Low Cost Groceries
Checks health of all services and alerts on failures
"""

import requests
import redis
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
API_URL = 'http://localhost:8000'
ALERT_EMAIL = None  # Set to your email for alerts
SLACK_WEBHOOK = None  # Set to Slack webhook URL for alerts

class SystemMonitor:
    def __init__(self):
        self.redis_client = None
        self.issues = []
        
    def check_redis(self) -> Dict:
        """Check Redis health"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            
            # Get queue size
            queue_size = self.redis_client.llen('scrape_queue')
            
            return {
                'status': 'healthy',
                'queue_size': queue_size,
                'connected': True
            }
        except Exception as e:
            self.issues.append(f"❌ Redis DOWN: {e}")
            return {
                'status': 'down',
                'error': str(e),
                'connected': False
            }
    
    def check_api(self) -> Dict:
        """Check API health"""
        try:
            start = time.time()
            response = requests.get(f'{API_URL}/health', timeout=10)
            response_time = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'data': response.json()
                }
            else:
                self.issues.append(f"❌ API unhealthy: HTTP {response.status_code}")
                return {
                    'status': 'unhealthy',
                    'http_code': response.status_code,
                    'response_time_ms': round(response_time, 2)
                }
        except requests.exceptions.RequestException as e:
            self.issues.append(f"❌ API DOWN: {e}")
            return {
                'status': 'down',
                'error': str(e)
            }
    
    def check_systemd_service(self, service_name: str) -> Dict:
        """Check if systemd service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_active = result.stdout.strip() == 'active'
            
            if not is_active:
                self.issues.append(f"❌ Service '{service_name}' is NOT running")
            
            return {
                'name': service_name,
                'status': 'running' if is_active else 'stopped',
                'active': is_active
            }
        except Exception as e:
            self.issues.append(f"❌ Failed to check service '{service_name}': {e}")
            return {
                'name': service_name,
                'status': 'error',
                'error': str(e),
                'active': False
            }
    
    def get_system_resources(self) -> Dict:
        """Get CPU, memory, disk usage"""
        try:
            # CPU load average
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[:3]
            
            # Memory usage
            mem_info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line or 'MemAvailable' in line:
                        key, value = line.split(':')
                        mem_info[key.strip()] = int(value.strip().split()[0])
            
            mem_used_percent = round(
                (1 - mem_info['MemAvailable'] / mem_info['MemTotal']) * 100, 2
            )
            
            # Disk usage
            disk_result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                timeout=5
            )
            disk_lines = disk_result.stdout.strip().split('\n')
            if len(disk_lines) > 1:
                disk_parts = disk_lines[1].split()
                disk_used_percent = disk_parts[4].rstrip('%')
            else:
                disk_used_percent = 'unknown'
            
            return {
                'cpu_load_avg': [float(x) for x in load_avg],
                'memory_used_percent': mem_used_percent,
                'disk_used_percent': disk_used_percent
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def check_recent_errors(self) -> Dict:
        """Check recent error logs"""
        error_count = 0
        recent_errors = []
        
        log_files = [
            '/var/log/grocery-api.log',
            '/var/log/grocery-worker.log',
            '/var/log/grocery-worker-error.log'
        ]
        
        for log_file in log_files:
            try:
                # Get last 50 lines
                result = subprocess.run(
                    ['tail', '-n', '50', log_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'ERROR' in line or 'CRITICAL' in line or '❌' in line:
                        error_count += 1
                        recent_errors.append({
                            'file': log_file,
                            'message': line[:200]  # Truncate long lines
                        })
            except Exception:
                pass
        
        return {
            'error_count': error_count,
            'recent_errors': recent_errors[-10:]  # Last 10 errors
        }
    
    def run_full_check(self) -> Dict:
        """Run all health checks"""
        print(f"\n{'='*60}")
        print(f"🔍 SYSTEM HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'redis': self.check_redis(),
            'api': self.check_api(),
            'services': {
                'api': self.check_systemd_service('grocery-api.service'),
                'worker': self.check_systemd_service('grocery-worker.service'),
                'redis': self.check_systemd_service('redis-server.service')
            },
            'system': self.get_system_resources(),
            'errors': self.check_recent_errors(),
            'issues': self.issues
        }
        
        # Print summary
        print("📊 SERVICE STATUS:")
        for service_name, service_data in report['services'].items():
            status_icon = "✅" if service_data.get('active') else "❌"
            print(f"  {status_icon} {service_name}: {service_data['status']}")
        
        print(f"\n📊 REDIS:")
        redis_icon = "✅" if report['redis']['status'] == 'healthy' else "❌"
        print(f"  {redis_icon} Status: {report['redis']['status']}")
        if report['redis'].get('queue_size') is not None:
            print(f"  📦 Queue size: {report['redis']['queue_size']} jobs")
        
        print(f"\n📊 API:")
        api_icon = "✅" if report['api']['status'] == 'healthy' else "❌"
        print(f"  {api_icon} Status: {report['api']['status']}")
        if report['api'].get('response_time_ms'):
            print(f"  ⏱️  Response time: {report['api']['response_time_ms']}ms")
        
        print(f"\n📊 SYSTEM RESOURCES:")
        sys_data = report['system']
        if 'cpu_load_avg' in sys_data:
            print(f"  💻 CPU Load: {sys_data['cpu_load_avg']}")
            print(f"  🧠 Memory Used: {sys_data['memory_used_percent']}%")
            print(f"  💾 Disk Used: {sys_data['disk_used_percent']}%")
        
        print(f"\n📊 RECENT ERRORS:")
        error_data = report['errors']
        print(f"  🚨 Error count (last 50 lines): {error_data['error_count']}")
        
        if self.issues:
            print(f"\n{'='*60}")
            print("⚠️  ISSUES DETECTED:")
            print(f"{'='*60}")
            for issue in self.issues:
                print(f"  {issue}")
            print()
        else:
            print(f"\n✅ All systems operational!\n")
        
        return report

def main():
    """Run monitoring check"""
    monitor = SystemMonitor()
    report = monitor.run_full_check()
    
    # Save report to file
    report_file = '/var/log/grocery-health-report.json'
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {report_file}\n")
    except Exception as e:
        print(f"⚠️  Failed to save report: {e}\n")
    
    # Exit with error code if issues detected
    if monitor.issues:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()

