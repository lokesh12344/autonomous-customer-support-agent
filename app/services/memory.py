"""Conversation memory service for maintaining chat history."""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

from app.services.database import get_db_connection


class ConversationMemory:
    """Manages conversation history storage and retrieval."""
    
    def __init__(self, session_id: str):
        """
        Initialize conversation memory for a session.
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        self.session_id = session_id
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversation_history (session_id, role, content)
            VALUES (?, ?, ?)
        """, (self.session_id, role, content))
        
        conn.commit()
        conn.close()
    
    def get_history(self, limit: Optional[int] = 10) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for the session.
        
        Args:
            limit: Maximum number of messages to retrieve (most recent)
            
        Returns:
            List of message dictionaries with role, content, timestamp
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT role, content, timestamp
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (self.session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        # Return in chronological order (oldest first)
        messages = [
            {
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"]
            }
            for row in reversed(rows)
        ]
        
        return messages
    
    def get_context_string(self, limit: Optional[int] = 5) -> str:
        """
        Get conversation history as a formatted string for LLM context.
        
        Args:
            limit: Number of recent messages to include
            
        Returns:
            Formatted conversation history string
        """
        history = self.get_history(limit=limit)
        
        if not history:
            return "No previous conversation."
        
        context_lines = ["Previous conversation:"]
        for msg in history:
            role_label = "Customer" if msg["role"] == "user" else "Agent"
            context_lines.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def clear_history(self) -> None:
        """Clear conversation history for the session."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM conversation_history
            WHERE session_id = ?
        """, (self.session_id,))
        
        conn.commit()
        conn.close()


def get_all_sessions() -> List[Dict[str, any]]:
    """
    Get all conversation sessions with message counts.
    
    Returns:
        List of session information dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            session_id,
            COUNT(*) as message_count,
            MIN(timestamp) as started_at,
            MAX(timestamp) as last_activity
        FROM conversation_history
        GROUP BY session_id
        ORDER BY last_activity DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    sessions = [
        {
            "session_id": row["session_id"],
            "message_count": row["message_count"],
            "started_at": row["started_at"],
            "last_activity": row["last_activity"]
        }
        for row in rows
    ]
    
    return sessions
