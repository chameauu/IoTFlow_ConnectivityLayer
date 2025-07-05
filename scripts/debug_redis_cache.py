#!/usr/bin/env python3
"""
Debug script for Redis cache operations
"""

import redis
import sys

# Redis Configuration
REDIS_URL = "redis://localhost:6379/0"

# Key prefixes
DEVICE_STATUS_PREFIX = "device:status:"
DEVICE_LASTSEEN_PREFIX = "device:lastseen:"

def main():
    device_id = 1
    if len(sys.argv) > 1:
        device_id = int(sys.argv[1])
    
    print(f"Debugging Redis cache operations for device {device_id}")
    print("-" * 60)
    
    try:
        # Connect to Redis
        r = redis.from_url(REDIS_URL, decode_responses=True)
        print(f"Connected to Redis server: {r.info('server')['redis_version']}")
        
        # Check if keys exist
        status_key = f"{DEVICE_STATUS_PREFIX}{device_id}"
        lastseen_key = f"{DEVICE_LASTSEEN_PREFIX}{device_id}"
        
        print(f"\nChecking keys before deletion:")
        status_exists = r.exists(status_key)
        lastseen_exists = r.exists(lastseen_key)
        
        print(f"Status key '{status_key}' exists: {status_exists}")
        if status_exists:
            print(f"  Value: {r.get(status_key)}")
            print(f"  TTL: {r.ttl(status_key)} seconds")
        
        print(f"Last seen key '{lastseen_key}' exists: {lastseen_exists}")
        if lastseen_exists:
            print(f"  Value: {r.get(lastseen_key)}")
            print(f"  TTL: {r.ttl(lastseen_key)} seconds")
        
        # Delete keys
        print("\nDeleting keys...")
        pipeline = r.pipeline()
        pipeline.delete(status_key)
        pipeline.delete(lastseen_key)
        result = pipeline.execute()
        print(f"Pipeline execution result: {result}")
        
        # Check if keys exist after deletion
        print(f"\nChecking keys after deletion:")
        status_exists = r.exists(status_key)
        lastseen_exists = r.exists(lastseen_key)
        
        print(f"Status key '{status_key}' exists: {status_exists}")
        print(f"Last seen key '{lastseen_key}' exists: {lastseen_exists}")
        
        # List all device-related keys
        print("\nAll device-related keys in Redis:")
        status_keys = r.keys(f"{DEVICE_STATUS_PREFIX}*")
        lastseen_keys = r.keys(f"{DEVICE_LASTSEEN_PREFIX}*")
        
        print(f"Status keys: {status_keys}")
        print(f"Last seen keys: {lastseen_keys}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
