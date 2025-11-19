"""
Callback Session Manager

Manages the pool of callback sessions, provides health tracking,
and triggers refreshes when needed.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from callback_session import CallbackSession
from session_db import get_db


logger = logging.getLogger(__name__)


class CallbackSessionManager:
    """
    Manages callback session pool with health tracking and auto-refresh.
    
    This is the interface between the scraper and the session database.
    It handles:
    - Pulling valid sessions from the pool
    - Marking session health (success/failure)
    - Triggering token service when running low
    - Automatic session invalidation
    """
    
    def __init__(self, min_sessions_per_region: int = 2):
        """
        Initialize session manager.
        
        Args:
            min_sessions_per_region: Minimum healthy sessions to maintain per region
        """
        self.db = get_db()
        self.min_sessions_per_region = min_sessions_per_region
        self._refresh_callbacks = []  # Callbacks to trigger when refresh needed
    
    def register_refresh_callback(self, callback):
        """
        Register a callback to be called when refresh is needed.
        
        The callback should be a function that triggers the TokenService
        to create new sessions.
        
        Args:
            callback: Function to call when refresh needed
        """
        self._refresh_callbacks.append(callback)
    
    def get_valid_session(self, region: Optional[str] = None) -> Optional[CallbackSession]:
        """
        Get a valid session from the pool.
        
        Args:
            region: Optional region to filter by
            
        Returns:
            A healthy CallbackSession, or None if none available
        """
        sessions = self.db.get_valid_sessions(region=region, limit=10)
        
        if not sessions:
            logger.warning(f"No valid sessions available for region={region}")
            self._trigger_refresh(region)
            return None
        
        # Check if we're running low
        if len(sessions) < self.min_sessions_per_region:
            logger.info(f"Low on sessions for region={region} ({len(sessions)} remaining), triggering refresh")
            self._trigger_refresh(region)
        
        # Return the least recently used (to distribute load)
        sessions.sort(key=lambda s: s.last_used or datetime.min)
        return sessions[0]
    
    def mark_success(self, session: CallbackSession):
        """
        Mark a session as successfully used.
        
        Args:
            session: The session that was used successfully
        """
        session.mark_success()
        self.db.update_session(session)
        
        logger.debug(f"Session {session.id} marked success (total={session.success_count})")
    
    def mark_failure(self, session: CallbackSession, error: Optional[str] = None):
        """
        Mark a session as failed.
        
        If a session has too many failures, it will be automatically invalidated.
        
        Args:
            session: The session that failed
            error: Optional error message
        """
        session.mark_failure()
        self.db.update_session(session)
        
        logger.warning(
            f"Session {session.id} marked failure (total={session.failure_count}), "
            f"valid={session.is_valid}, error={error}"
        )
        
        # If invalidated, trigger refresh
        if not session.is_valid:
            logger.error(f"Session {session.id} invalidated after {session.failure_count} failures")
            self._trigger_refresh(session.region)
    
    def get_healthy_sessions_count(self, region: Optional[str] = None) -> int:
        """
        Get count of healthy sessions.
        
        Args:
            region: Optional region filter
            
        Returns:
            Number of healthy sessions
        """
        sessions = self.db.get_valid_sessions(region=region, limit=100)
        return len([s for s in sessions if s.is_healthy()])
    
    def is_pool_healthy(self, region: Optional[str] = None) -> bool:
        """
        Check if the session pool is healthy.
        
        Args:
            region: Optional region to check
            
        Returns:
            True if we have enough healthy sessions
        """
        count = self.get_healthy_sessions_count(region=region)
        return count >= self.min_sessions_per_region
    
    def cleanup_expired_sessions(self):
        """
        Mark expired sessions as invalid.
        
        This should be run periodically to clean up old sessions.
        """
        all_sessions = self.db.get_all_sessions()
        invalidated = 0
        
        for session in all_sessions:
            if session.is_valid and not session.is_healthy():
                logger.info(f"Marking expired session {session.id} as invalid")
                self.db.mark_session_invalid(session.id)
                invalidated += 1
        
        if invalidated > 0:
            logger.info(f"Cleaned up {invalidated} expired sessions")
        
        return invalidated
    
    def get_pool_status(self) -> dict:
        """
        Get current status of the session pool.
        
        Returns:
            Dictionary with pool statistics
        """
        stats = self.db.get_stats()
        
        # Get per-region health
        regions_health = {}
        for region in stats.get('regions', {}).keys():
            healthy_count = self.get_healthy_sessions_count(region=region)
            is_healthy = healthy_count >= self.min_sessions_per_region
            
            regions_health[region] = {
                'healthy_count': healthy_count,
                'is_healthy': is_healthy,
                'needs_refresh': not is_healthy
            }
        
        return {
            'total_sessions': stats['total_sessions'],
            'valid_sessions': stats['valid_sessions'],
            'success_rate': stats['success_rate'],
            'regions': regions_health,
            'pool_healthy': all(r['is_healthy'] for r in regions_health.values())
        }
    
    def _trigger_refresh(self, region: Optional[str] = None):
        """
        Trigger refresh callbacks to create new sessions.
        
        Args:
            region: Optional region to refresh
        """
        for callback in self._refresh_callbacks:
            try:
                callback(region=region)
            except Exception as e:
                logger.error(f"Error triggering refresh callback: {e}")


# Singleton instance
_manager = None

def get_session_manager() -> CallbackSessionManager:
    """Get or create the session manager singleton."""
    global _manager
    if _manager is None:
        _manager = CallbackSessionManager()
    return _manager

