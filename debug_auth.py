#!/usr/bin/env python3

import os
import sys
sys.path.append('/app')

# Test authentication setup
def test_auth():
    print("=== Authentication Debug ===")
    
    # Check environment variables
    print(f"API_KEY from env: {os.getenv('API_KEY', 'NOT SET')}")
    
    try:
        from config import API_KEY as CONFIG_API_KEY
        print(f"API_KEY from config: {CONFIG_API_KEY}")
    except Exception as e:
        print(f"Error loading config API_KEY: {e}")
    
    # Test API key manager
    try:
        from models.api_keys import APIKeyManager
        api_manager = APIKeyManager()
        print(f"API Key Manager initialized successfully")
        
        # Check if database exists
        import sqlite3
        conn = sqlite3.connect('/tmp/api_keys.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(api_keys)")
        columns = cursor.fetchall()
        print("Database columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        cursor.execute("SELECT COUNT(*) FROM api_keys")
        count = cursor.fetchone()[0]
        print(f"Number of API keys in database: {count}")
        
        if count > 0:
            # Get first few rows with all columns
            cursor.execute("SELECT * FROM api_keys LIMIT 3")
            keys = cursor.fetchall()
            for row in keys:
                print(f"  Row: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error with API key manager: {e}")

if __name__ == "__main__":
    test_auth()