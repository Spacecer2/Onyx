"""
JARVIS Memory Manager - Persistent conversation history and user preferences
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages conversation history and user preferences for JARVIS"""
    
    def __init__(self, db_path: str = "jarvis/memory/conversations.db"):
        self.db_path = db_path
        self._ensure_memory_directory()
        self.init_database()
        logger.info(f"Memory manager initialized with database: {self.db_path}")
    
    def _ensure_memory_directory(self):
        """Ensure the memory directory exists"""
        memory_dir = Path(self.db_path).parent
        memory_dir.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database for conversation memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                jarvis_response TEXT NOT NULL,
                context TEXT,
                session_id TEXT,
                command_type TEXT,
                confidence REAL DEFAULT 1.0,
                processing_time REAL,
                success BOOLEAN DEFAULT 1
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        # System events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                event_data TEXT,
                severity TEXT DEFAULT 'info'
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(command_type)')
        
        conn.commit()
        conn.close()
        logger.info("Database tables initialized successfully")
    
    def store_conversation(self, user_input: str, jarvis_response: str, 
                          context: Optional[Dict] = None, session_id: str = None,
                          command_type: str = None, confidence: float = 1.0,
                          processing_time: float = None, success: bool = True):
        """Store a conversation exchange"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations 
                (user_input, jarvis_response, context, session_id, command_type, 
                 confidence, processing_time, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_input, jarvis_response, json.dumps(context) if context else None, 
                  session_id, command_type, confidence, processing_time, success))
            
            conn.commit()
            conn.close()
            logger.debug(f"Stored conversation: {user_input[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False
    
    def get_recent_conversations(self, limit: int = 10, session_id: str = None) -> List[Dict]:
        """Get recent conversations for context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if session_id:
                cursor.execute('''
                    SELECT user_input, jarvis_response, context, timestamp, command_type
                    FROM conversations 
                    WHERE session_id = ? AND success = 1
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (session_id, limit))
            else:
                cursor.execute('''
                    SELECT user_input, jarvis_response, context, timestamp, command_type
                    FROM conversations 
                    WHERE success = 1
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'user_input': row[0],
                    'jarvis_response': row[1],
                    'context': json.loads(row[2]) if row[2] else None,
                    'timestamp': row[3],
                    'command_type': row[4]
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    def get_conversation_context(self, session_id: str = None, limit: int = 5) -> str:
        """Get conversation context as formatted string for AI prompts"""
        conversations = self.get_recent_conversations(limit, session_id)
        
        if not conversations:
            return ""
        
        context_parts = []
        for conv in conversations:
            context_parts.append(f"User: {conv['user_input']}")
            context_parts.append(f"JARVIS: {conv['jarvis_response']}")
        
        return "\n".join(context_parts)
    
    def get_user_preferences(self) -> Dict[str, str]:
        """Get user preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT preference_key, preference_value FROM user_preferences')
            results = cursor.fetchall()
            conn.close()
            
            return {row[0]: row[1] for row in results}
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    def update_preference(self, key: str, value: str, description: str = None):
        """Update user preference"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (preference_key, preference_value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, description))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated preference: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update preference: {e}")
            return False
    
    def get_preference(self, key: str, default: str = None) -> str:
        """Get a specific user preference"""
        preferences = self.get_user_preferences()
        return preferences.get(key, default)
    
    def log_system_event(self, event_type: str, event_data: Dict = None, severity: str = "info"):
        """Log system events for debugging and monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_events (event_type, event_data, severity)
                VALUES (?, ?, ?)
            ''', (event_type, json.dumps(event_data) if event_data else None, severity))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
    
    def get_conversation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE timestamp >= datetime('now', '-{} days')
            '''.format(days))
            total_conversations = cursor.fetchone()[0]
            
            # Successful conversations
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE success = 1 AND timestamp >= datetime('now', '-{} days')
            '''.format(days))
            successful_conversations = cursor.fetchone()[0]
            
            # Most common command types
            cursor.execute('''
                SELECT command_type, COUNT(*) as count 
                FROM conversations 
                WHERE command_type IS NOT NULL 
                AND timestamp >= datetime('now', '-{} days')
                GROUP BY command_type 
                ORDER BY count DESC 
                LIMIT 5
            '''.format(days))
            command_types = cursor.fetchall()
            
            # Average processing time
            cursor.execute('''
                SELECT AVG(processing_time) FROM conversations 
                WHERE processing_time IS NOT NULL 
                AND timestamp >= datetime('now', '-{} days')
            '''.format(days))
            avg_processing_time = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_conversations': total_conversations,
                'successful_conversations': successful_conversations,
                'success_rate': (successful_conversations / total_conversations * 100) if total_conversations > 0 else 0,
                'top_command_types': [{'type': row[0], 'count': row[1]} for row in command_types],
                'avg_processing_time': avg_processing_time,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {}
    
    def clear_old_conversations(self, days: int = 90):
        """Clear conversations older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM conversations 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared {deleted_count} old conversations")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to clear old conversations: {e}")
            return 0
    
    def export_conversations(self, file_path: str, format: str = "json"):
        """Export conversations to file"""
        try:
            conversations = self.get_recent_conversations(limit=1000)
            
            if format.lower() == "json":
                with open(file_path, 'w') as f:
                    json.dump(conversations, f, indent=2, default=str)
            elif format.lower() == "csv":
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'user_input', 'jarvis_response', 'command_type'])
                    writer.writeheader()
                    for conv in conversations:
                        writer.writerow(conv)
            
            logger.info(f"Exported {len(conversations)} conversations to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export conversations: {e}")
            return False

# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
