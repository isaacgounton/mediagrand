#!/usr/bin/env python3
"""
Simple RQ worker starter script to avoid CLI parameter conflicts.
"""
import sys
import os
import time
import logging
import signal
from redis import Redis
from redis.exceptions import ConnectionError, ReadOnlyError, ResponseError
from rq import Worker
from rq.exceptions import WorkerException

def create_redis_connection(max_retries=5, retry_delay=2):
    """Create Redis connection with retry logic and master detection"""
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
            # Test the connection and check if it's a master
            redis_conn.ping()
            
            # Check if Redis instance is master (can write)
            try:
                info = redis_conn.info('replication')
                if info.get('role') != 'master':
                    raise ReadOnlyError("Connected to Redis replica, need master for RQ operations")
            except Exception as role_check_error:
                logging.warning(f"Could not verify Redis role: {role_check_error}")
            
            logging.info(f"Worker successfully connected to Redis master at {redis_url}")
            return redis_conn
        except (ConnectionError, ReadOnlyError, ResponseError) as e:
            if attempt < max_retries - 1:
                logging.warning(f"Worker could not connect to Redis master: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logging.error(f"Worker failed to connect to Redis master after {max_retries} attempts: {str(e)}")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Worker connection error: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logging.error(f"Worker failed to connect after {max_retries} attempts: {str(e)}")
                raise

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_requested = True
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    while not shutdown_requested:
        try:
            # Set up Redis connection with retry logic
            redis_conn = create_redis_connection()
            
            # Create worker
            worker = Worker(['tasks'], connection=redis_conn)
            
            # Start worker with connection monitoring
            logging.info("Starting RQ worker...")
            worker.work(with_scheduler=False)
            
        except (ConnectionError, ReadOnlyError, ResponseError) as e:
            logging.error(f"Redis connection error in worker: {str(e)}")
            if "master -> replica" in str(e) or "read only replica" in str(e).lower():
                logging.info("Redis failover detected, attempting to reconnect to new master...")
                time.sleep(5)  # Wait before attempting reconnection
            else:
                logging.info("Retrying connection in 10 seconds...")
                time.sleep(10)
                
        except WorkerException as e:
            logging.error(f"Worker error: {str(e)}")
            if not shutdown_requested:
                logging.info("Restarting worker in 5 seconds...")
                time.sleep(5)
            
        except KeyboardInterrupt:
            logging.info("Worker interrupted by user")
            break
            
        except Exception as e:
            logging.error(f"Unexpected error in worker: {str(e)}")
            if not shutdown_requested:
                logging.info("Restarting worker in 10 seconds...")
                time.sleep(10)
    
    logging.info("Worker shutdown complete")

if __name__ == '__main__':
    main()
