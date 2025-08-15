#!/usr/bin/env python3
"""
Session state manager for persistent state across tool calls within a session.

This provides session-based state management as an alternative to fastmcp's
per-request Context.get_state()/set_state() methods.
"""

import threading
import time
from typing import Any, Dict, Set


class SessionStateManager:
    """Thread-safe in-memory session state manager with TTL cleanup."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """Initialize session manager.
        
        Args:
            ttl_seconds: Time-to-live for session data in seconds (default 1 hour)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._ttl = ttl_seconds
    
    def get_session_state(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a value from session state.
        
        Args:
            session_id: The session identifier
            key: The state key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The stored value or default
        """
        with self._lock:
            self._cleanup_expired()
            session_data = self._sessions.get(session_id, {})
            return session_data.get(key, default)
    
    def set_session_state(self, session_id: str, key: str, value: Any) -> None:
        """Set a value in session state.
        
        Args:
            session_id: The session identifier
            key: The state key to set
            value: The value to store
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {}
            self._sessions[session_id][key] = value
            self._timestamps[session_id] = time.time()
    
    def get_read_files(self, session_id: str) -> Set[str]:
        """Get the set of files read in this session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Set of file paths that have been read
        """
        return self.get_session_state(session_id, "read_files", set())
    
    def add_read_file(self, session_id: str, file_path: str) -> None:
        """Mark a file as read in this session.
        
        Args:
            session_id: The session identifier  
            file_path: The file path to mark as read
        """
        read_files = self.get_read_files(session_id)
        read_files.add(file_path)
        self.set_session_state(session_id, "read_files", read_files)
    
    def is_file_read(self, session_id: str, file_path: str) -> bool:
        """Check if a file has been read in this session.
        
        Args:
            session_id: The session identifier
            file_path: The file path to check
            
        Returns:
            True if the file has been read in this session
        """
        read_files = self.get_read_files(session_id)
        return file_path in read_files
    
    def clear_session(self, session_id: str) -> None:
        """Clear all state for a session.
        
        Args:
            session_id: The session identifier to clear
        """
        with self._lock:
            self._sessions.pop(session_id, None)
            self._timestamps.pop(session_id, None)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions.
        
        Returns:
            Dictionary with session statistics
        """
        with self._lock:
            self._cleanup_expired()
            return {
                "active_sessions": len(self._sessions),
                "total_memory_mb": self._estimate_memory_usage() / (1024 * 1024),
                "oldest_session_age": self._get_oldest_session_age()
            }
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, timestamp in self._timestamps.items()
            if current_time - timestamp > self._ttl
        ]
        for session_id in expired_sessions:
            self._sessions.pop(session_id, None)
            self._timestamps.pop(session_id, None)
    
    def _estimate_memory_usage(self) -> int:
        """Rough estimate of memory usage in bytes."""
        total_size = 0
        for session_data in self._sessions.values():
            for key, value in session_data.items():
                # Rough estimation - not precise but gives an idea
                total_size += len(str(key)) + len(str(value))
        return total_size
    
    def _get_oldest_session_age(self) -> float:
        """Get age of oldest session in seconds."""
        if not self._timestamps:
            return 0
        current_time = time.time()
        oldest_timestamp = min(self._timestamps.values())
        return current_time - oldest_timestamp


# Global session manager instance
session_manager = SessionStateManager()