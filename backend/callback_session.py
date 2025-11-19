"""
CallbackSession Model

Represents a Google Shopping callback URL with health tracking.
Sessions are created by TokenService and used by the scraper.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CallbackSession:
    """
    Represents a callback URL session for Google Shopping scraping.
    
    Attributes:
        url: The full callback URL (e.g., /async/callback:6948?fc=...)
        region: Geographic region (e.g., "US-West", "US-East", "EU")
        proxy_bucket: Which proxy this session was created with (e.g., "oxylabs_8001")
        created_at: When this session was created
        last_used: Last time this session was successfully used
        success_count: Number of successful requests
        failure_count: Number of failed requests
        is_valid: Whether this session is currently valid
        id: Database ID (auto-assigned)
    """
    url: str
    region: str
    proxy_bucket: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    is_valid: bool = True
    id: Optional[int] = None
    
    def mark_success(self):
        """Mark a successful use of this session."""
        self.success_count += 1
        self.last_used = datetime.utcnow()
        # Reset failure count on success
        if self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)
    
    def mark_failure(self):
        """Mark a failed use of this session."""
        self.failure_count += 1
        # Invalidate if too many failures
        if self.failure_count >= 3:
            self.is_valid = False
    
    def is_expired(self, max_age_minutes: int = 60) -> bool:
        """
        Check if this session is expired based on age.
        
        Args:
            max_age_minutes: Maximum age in minutes before considering expired
            
        Returns:
            True if session is older than max_age_minutes
        """
        age = datetime.utcnow() - self.created_at
        return age > timedelta(minutes=max_age_minutes)
    
    def is_healthy(self) -> bool:
        """
        Check if this session is healthy.
        
        A session is healthy if:
        - It's marked as valid
        - It's not expired
        - Success rate > 50% (if used at least 5 times)
        """
        if not self.is_valid:
            return False
        
        if self.is_expired():
            return False
        
        # If used enough times, check success rate
        total_uses = self.success_count + self.failure_count
        if total_uses >= 5:
            success_rate = self.success_count / total_uses
            if success_rate < 0.5:
                return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'url': self.url,
            'region': self.region,
            'proxy_bucket': self.proxy_bucket,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'is_valid': self.is_valid,
            'is_healthy': self.is_healthy(),
            'age_minutes': (datetime.utcnow() - self.created_at).total_seconds() / 60
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CallbackSession':
        """Create from dictionary (database row)."""
        return cls(
            id=data.get('id'),
            url=data['url'],
            region=data['region'],
            proxy_bucket=data['proxy_bucket'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            is_valid=data.get('is_valid', True)
        )
    
    def __repr__(self) -> str:
        health = "✅" if self.is_healthy() else "❌"
        age_min = (datetime.utcnow() - self.created_at).total_seconds() / 60
        return f"<CallbackSession {health} {self.region} age={age_min:.0f}m success={self.success_count} fail={self.failure_count}>"

