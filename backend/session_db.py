"""
Session Database

SQLite database for storing CallbackSession records.
Provides CRUD operations and querying for session management.
"""

import sqlite3
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from callback_session import CallbackSession


class SessionDatabase:
    """Database manager for CallbackSession storage."""
    
    def __init__(self, db_path: str = "sessions.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS callback_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    region TEXT NOT NULL,
                    proxy_bucket TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    is_valid INTEGER DEFAULT 1
                )
            """)
            
            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_region_valid 
                ON callback_sessions(region, is_valid)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON callback_sessions(created_at DESC)
            """)
            
            conn.commit()
    
    def create_session(self, session: CallbackSession) -> CallbackSession:
        """
        Create a new session in the database.
        
        Args:
            session: CallbackSession to create
            
        Returns:
            The session with id populated
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO callback_sessions (
                    url, region, proxy_bucket, created_at, last_used,
                    success_count, failure_count, is_valid
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.url,
                session.region,
                session.proxy_bucket,
                session.created_at.isoformat(),
                session.last_used.isoformat() if session.last_used else None,
                session.success_count,
                session.failure_count,
                1 if session.is_valid else 0
            ))
            
            session.id = cursor.lastrowid
            conn.commit()
        
        return session
    
    def get_session(self, session_id: int) -> Optional[CallbackSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID to fetch
            
        Returns:
            CallbackSession if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM callback_sessions WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return CallbackSession.from_dict(dict(row))
        
        return None
    
    def update_session(self, session: CallbackSession):
        """
        Update an existing session.
        
        Args:
            session: CallbackSession to update
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE callback_sessions
                SET url = ?, region = ?, proxy_bucket = ?,
                    last_used = ?, success_count = ?, failure_count = ?,
                    is_valid = ?
                WHERE id = ?
            """, (
                session.url,
                session.region,
                session.proxy_bucket,
                session.last_used.isoformat() if session.last_used else None,
                session.success_count,
                session.failure_count,
                1 if session.is_valid else 0,
                session.id
            ))
            conn.commit()
    
    def get_valid_sessions(
        self, 
        region: Optional[str] = None,
        limit: int = 10
    ) -> List[CallbackSession]:
        """
        Get valid (healthy) sessions.
        
        Args:
            region: Optional region filter
            limit: Maximum number of sessions to return
            
        Returns:
            List of valid CallbackSession objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if region:
                cursor = conn.execute("""
                    SELECT * FROM callback_sessions
                    WHERE is_valid = 1 AND region = ?
                    ORDER BY last_used DESC, created_at DESC
                    LIMIT ?
                """, (region, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM callback_sessions
                    WHERE is_valid = 1
                    ORDER BY last_used DESC, created_at DESC
                    LIMIT ?
                """, (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                session = CallbackSession.from_dict(dict(row))
                # Only return if actually healthy (checks expiration)
                if session.is_healthy():
                    sessions.append(session)
            
            return sessions
    
    def get_all_sessions(self) -> List[CallbackSession]:
        """Get all sessions (for admin/monitoring)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM callback_sessions
                ORDER BY created_at DESC
            """)
            
            return [CallbackSession.from_dict(dict(row)) for row in cursor.fetchall()]
    
    def mark_session_invalid(self, session_id: int):
        """Mark a session as invalid."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE callback_sessions
                SET is_valid = 0
                WHERE id = ?
            """, (session_id,))
            conn.commit()
    
    def delete_old_sessions(self, days: int = 7):
        """
        Delete sessions older than specified days.
        
        Args:
            days: Delete sessions older than this many days
            
        Returns:
            Number of sessions deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM callback_sessions
                WHERE created_at < ?
            """, (cutoff.isoformat(),))
            
            deleted = cursor.rowcount
            conn.commit()
        
        return deleted
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total sessions
            total = conn.execute("SELECT COUNT(*) FROM callback_sessions").fetchone()[0]
            
            # Valid sessions
            valid = conn.execute("SELECT COUNT(*) FROM callback_sessions WHERE is_valid = 1").fetchone()[0]
            
            # Per-region breakdown
            cursor = conn.execute("""
                SELECT region, COUNT(*) as count, SUM(is_valid) as valid_count
                FROM callback_sessions
                GROUP BY region
            """)
            
            regions = {}
            for row in cursor.fetchall():
                regions[row[0]] = {
                    'total': row[1],
                    'valid': row[2]
                }
            
            # Success rate
            cursor = conn.execute("""
                SELECT 
                    SUM(success_count) as total_success,
                    SUM(failure_count) as total_failure
                FROM callback_sessions
            """)
            
            row = cursor.fetchone()
            total_success = row[0] or 0
            total_failure = row[1] or 0
            total_requests = total_success + total_failure
            
            success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_sessions': total,
                'valid_sessions': valid,
                'invalid_sessions': total - valid,
                'regions': regions,
                'total_requests': total_requests,
                'success_rate': round(success_rate, 2)
            }


# Singleton instance
_db = None

def get_db() -> SessionDatabase:
    """Get or create the database singleton."""
    global _db
    if _db is None:
        db_path = Path(__file__).parent.parent / "data" / "sessions.db"
        db_path.parent.mkdir(exist_ok=True)
        _db = SessionDatabase(str(db_path))
    return _db

