#!/usr/bin/env python3
"""
Simple RQ worker starter script to avoid CLI parameter conflicts.
"""
import sys
import os
import time
import logging
from redis import Redis
from rq import Worker

def create_redis_connection(max_retries=5, retry_delay=2):
    """Create Redis connection with retry logic"""
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    
    for attempt in range(max_retries):
        try:
            redis_conn = Redis.from_url(
                redis_url,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test the connection
            redis_conn.ping()
            logging.info(f"Worker successfully connected to Redis at {redis_url}")
            return redis_conn
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Worker could not connect to Redis instance: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logging.error(f"Worker failed to connect to Redis after {max_retries} attempts: {str(e)}")
                raise

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Set up Redis connection with retry logic
    redis_conn = create_redis_connection()
    
    # Create worker
    worker = Worker(['tasks'], connection=redis_conn)
    
    # Start worker
    logging.info("Starting RQ worker...")
    worker.work()

if __name__ == '__main__':
    main()
