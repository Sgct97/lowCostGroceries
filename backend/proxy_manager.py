"""
ISP Proxy Rotation Manager
Manages pool of $1 ISP proxies for Google Shopping scraping
"""

import random
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading


@dataclass
class Proxy:
    """Represents a single ISP proxy"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Tracking
    total_requests: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    is_blocked: bool = False
    blocked_until: Optional[datetime] = None
    
    @property
    def url(self) -> str:
        """Get proxy URL for requests library"""
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"
    
    @property
    def dict(self) -> Dict[str, str]:
        """Get proxy dict for requests library"""
        return {
            'http': self.url,
            'https': self.url
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 100.0
        return ((self.total_requests - self.failed_requests) / self.total_requests) * 100
    
    def mark_used(self):
        """Mark proxy as used"""
        self.total_requests += 1
        self.last_used = datetime.now()
    
    def mark_failed(self):
        """Mark request as failed"""
        self.failed_requests += 1
        
        # Block proxy if failure rate is too high
        if self.total_requests >= 10 and self.success_rate < 50:
            self.block_temporary(minutes=30)
    
    def mark_blocked(self):
        """Mark proxy as permanently blocked by Google"""
        self.is_blocked = True
        self.blocked_until = None  # Permanent
    
    def block_temporary(self, minutes: int = 30):
        """Temporarily block proxy"""
        self.is_blocked = True
        self.blocked_until = datetime.now() + timedelta(minutes=minutes)
    
    def check_unblock(self):
        """Check if temporary block has expired"""
        if self.is_blocked and self.blocked_until:
            if datetime.now() >= self.blocked_until:
                self.is_blocked = False
                self.blocked_until = None
                return True
        return False
    
    def __repr__(self):
        status = "BLOCKED" if self.is_blocked else "OK"
        return f"<Proxy {self.host}:{self.port} [{status}] {self.success_rate:.1f}% success>"


class ProxyPool:
    """
    Pool of ISP proxies with automatic rotation and health tracking
    
    Features:
    - Automatic rotation
    - Health tracking
    - Automatic blocking of dead proxies
    - Load balancing (least-recently-used)
    """
    
    def __init__(self, proxies: List[Proxy]):
        self.proxies = proxies
        self._lock = threading.Lock()
        self._last_rotation_index = 0
    
    @classmethod
    def from_list(cls, proxy_list: List[str]) -> 'ProxyPool':
        """
        Create pool from list of proxy strings
        
        Format: "host:port" or "host:port:username:password"
        
        Example:
            proxies = [
                "123.45.67.89:8080",
                "98.76.54.32:8080:user:pass"
            ]
            pool = ProxyPool.from_list(proxies)
        """
        parsed_proxies = []
        
        for proxy_str in proxy_list:
            parts = proxy_str.split(':')
            
            if len(parts) == 2:
                # host:port
                proxy = Proxy(host=parts[0], port=int(parts[1]))
            elif len(parts) == 4:
                # host:port:user:pass
                proxy = Proxy(
                    host=parts[0],
                    port=int(parts[1]),
                    username=parts[2],
                    password=parts[3]
                )
            else:
                print(f"⚠️  Invalid proxy format: {proxy_str}")
                continue
            
            parsed_proxies.append(proxy)
        
        return cls(parsed_proxies)
    
    def get_next_proxy(self) -> Optional[Proxy]:
        """
        Get next available proxy using round-robin + health check
        
        Returns:
            Proxy object or None if all proxies are blocked
        """
        with self._lock:
            # Check for unblocked proxies
            for proxy in self.proxies:
                proxy.check_unblock()
            
            # Get available proxies
            available = [p for p in self.proxies if not p.is_blocked]
            
            if not available:
                print("❌ All proxies are blocked!")
                return None
            
            # Sort by least recently used
            available.sort(key=lambda p: p.last_used or datetime.min)
            
            # Get the least recently used proxy
            proxy = available[0]
            proxy.mark_used()
            
            return proxy
    
    def get_random_proxy(self) -> Optional[Proxy]:
        """Get random available proxy"""
        with self._lock:
            available = [p for p in self.proxies if not p.is_blocked]
            
            if not available:
                return None
            
            proxy = random.choice(available)
            proxy.mark_used()
            
            return proxy
    
    def report_failure(self, proxy: Proxy, is_blocked: bool = False):
        """
        Report a failed request
        
        Args:
            proxy: The proxy that failed
            is_blocked: True if proxy is blocked by Google (permanent)
        """
        with self._lock:
            proxy.mark_failed()
            
            if is_blocked:
                proxy.mark_blocked()
                print(f"🚫 Proxy {proxy.host} is BLOCKED by Google")
    
    def get_stats(self) -> Dict:
        """Get pool statistics"""
        with self._lock:
            total = len(self.proxies)
            available = len([p for p in self.proxies if not p.is_blocked])
            blocked = total - available
            
            total_requests = sum(p.total_requests for p in self.proxies)
            total_failures = sum(p.failed_requests for p in self.proxies)
            
            avg_success_rate = sum(p.success_rate for p in self.proxies) / total if total > 0 else 0
            
            return {
                'total_proxies': total,
                'available': available,
                'blocked': blocked,
                'total_requests': total_requests,
                'total_failures': total_failures,
                'avg_success_rate': round(avg_success_rate, 2),
                'proxies': [
                    {
                        'host': p.host,
                        'status': 'blocked' if p.is_blocked else 'ok',
                        'requests': p.total_requests,
                        'success_rate': round(p.success_rate, 2)
                    }
                    for p in self.proxies
                ]
            }
    
    def __len__(self):
        return len(self.proxies)
    
    def __repr__(self):
        available = len([p for p in self.proxies if not p.is_blocked])
        return f"<ProxyPool: {available}/{len(self.proxies)} available>"


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example of how to use the proxy pool"""
    
    # Your ISP proxies (format: "host:port" or "host:port:user:pass")
    proxy_list = [
        "123.45.67.89:8080",
        "98.76.54.32:8080",
        "11.22.33.44:8080:myuser:mypass",
    ]
    
    # Create pool
    pool = ProxyPool.from_list(proxy_list)
    print(f"Created pool: {pool}")
    
    # Get a proxy
    proxy = pool.get_next_proxy()
    print(f"Got proxy: {proxy}")
    
    # Use with requests
    import requests
    try:
        response = requests.get(
            "https://www.google.com",
            proxies=proxy.dict,
            timeout=10
        )
        print(f"✅ Request successful: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        pool.report_failure(proxy)
    
    # Get stats
    stats = pool.get_stats()
    print(f"Pool stats: {stats}")


if __name__ == "__main__":
    example_usage()

