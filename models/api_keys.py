# Copyright (c) 2025 Isaac Gounton

import sqlite3
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import LOCAL_STORAGE_PATH

class APIKeyManager:
    def __init__(self):
        self.db_path = os.path.join(LOCAL_STORAGE_PATH, 'api_keys.db')
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_name TEXT NOT NULL,
                    key_hash TEXT UNIQUE NOT NULL,
                    key_prefix TEXT NOT NULL,
                    permissions TEXT DEFAULT 'read,write',
                    rate_limit INTEGER DEFAULT 1000,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_status INTEGER,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE CASCADE
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON api_usage(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_api_key ON api_usage(api_key_id)")
            
            conn.commit()
    
    def generate_api_key(self) -> Tuple[str, str]:
        """Generate a new API key and return (full_key, hash)"""
        prefix = "dahopevi"
        key_body = secrets.token_urlsafe(32)
        full_key = f"{prefix}_{key_body}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, key_hash
    
    def create_user(self, username: str, email: str) -> int:
        """Create a new user and return user_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (username, email)
            )
            user_id = cursor.lastrowid
            if user_id is None:
                raise ValueError("Failed to create user")
            return user_id
    
    def create_api_key(self, user_id: int, key_name: str, permissions: str = "read,write", 
                      rate_limit: int = 1000, expires_days: Optional[int] = None) -> str:
        """Create a new API key for a user"""
        full_key, key_hash = self.generate_api_key()
        key_prefix = full_key[:12] + "..."
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_keys (user_id, key_name, key_hash, key_prefix, permissions, 
                                    rate_limit, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, key_name, key_hash, key_prefix, permissions, rate_limit, expires_at))
            conn.commit()
        
        return full_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return key info if valid"""
        if not api_key:
            return None
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT ak.*, u.username, u.email, u.is_active as user_active
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.key_hash = ? AND ak.is_active = 1 AND u.is_active = 1
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            key_info = dict(row)
            
            if key_info['expires_at']:
                expires_at = datetime.fromisoformat(key_info['expires_at'])
                if expires_at < datetime.now():
                    return None
            
            conn.execute(
                "UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE id = ?",
                (key_info['id'],)
            )
            conn.commit()
            
            return key_info
    
    def log_api_usage(self, api_key_id: int, endpoint: str, method: str, status: int):
        """Log API usage for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_usage (api_key_id, endpoint, method, response_status)
                VALUES (?, ?, ?, ?)
            """, (api_key_id, endpoint, method, status))
            conn.commit()
    
    def get_user_api_keys(self, user_id: int) -> List[Dict]:
        """Get all API keys for a user (including revoked ones)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, key_name, key_prefix, permissions, rate_limit, 
                       expires_at, created_at, last_used, is_active
                FROM api_keys
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT u.*, COUNT(ak.id) as api_key_count
                FROM users u
                LEFT JOIN api_keys ak ON u.id = ak.user_id AND ak.is_active = 1
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """Revoke an API key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?",
                (key_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their API keys"""
        with sqlite3.connect(self.db_path) as conn:
            # First delete all API keys for this user (CASCADE should handle this, but being explicit)
            conn.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            
            # Then delete the user
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    
    def get_usage_stats(self, api_key_id: int, days: int = 30) -> Dict:
        """Get usage statistics for an API key"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor = conn.execute("""
                SELECT COUNT(*) as total_requests,
                       COUNT(CASE WHEN response_status < 400 THEN 1 END) as successful_requests,
                       COUNT(CASE WHEN response_status >= 400 THEN 1 END) as failed_requests,
                       MIN(timestamp) as first_request,
                       MAX(timestamp) as last_request
                FROM api_usage
                WHERE api_key_id = ? AND timestamp >= ?
            """, (api_key_id, since_date))
            
            stats = dict(cursor.fetchone())
            
            cursor = conn.execute("""
                SELECT endpoint, COUNT(*) as count
                FROM api_usage
                WHERE api_key_id = ? AND timestamp >= ?
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 10
            """, (api_key_id, since_date))
            
            stats['top_endpoints'] = [dict(row) for row in cursor.fetchall()]
            
            return stats