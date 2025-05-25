#!/usr/bin/env python3
"""
Simple RQ worker starter script to avoid CLI parameter conflicts.
"""
import sys
import os
from redis import Redis
from rq import Worker

def main():
    # Set up Redis connection
    redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    redis_conn = Redis.from_url(redis_url)
    
    # Create worker
    worker = Worker(['tasks'], connection=redis_conn)
    
    # Start worker
    worker.work()

if __name__ == '__main__':
    main()
