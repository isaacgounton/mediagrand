#!/usr/bin/env python3
"""
Redis health check script for monitoring connection status
"""
import os
import sys
import time
import logging
from redis import Redis

def check_redis_connection():
    """Check Redis connection and return status"""
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    
    try:
        redis_conn = Redis.from_url(
            redis_url,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test the connection
        result = redis_conn.ping()
        if result:
            logging.info(f"✅ Redis connection successful at {redis_url}")
            
            # Get Redis info
            info = redis_conn.info()
            logging.info(f"📊 Redis version: {info.get('redis_version', 'unknown')}")
            logging.info(f"📊 Connected clients: {info.get('connected_clients', 'unknown')}")
            logging.info(f"📊 Used memory: {info.get('used_memory_human', 'unknown')}")
            
            return True
        else:
            logging.error(f"❌ Redis ping failed at {redis_url}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Redis connection failed: {str(e)}")
        return False

def monitor_redis(interval=30):
    """Monitor Redis connection continuously"""
    logging.info(f"🔍 Starting Redis monitoring (checking every {interval} seconds)")
    
    while True:
        status = check_redis_connection()
        if not status:
            logging.warning("⚠️  Redis connection lost - checking again in 5 seconds...")
            time.sleep(5)
        else:
            time.sleep(interval)

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        monitor_redis()
    else:
        check_redis_connection()

if __name__ == '__main__':
    main()
