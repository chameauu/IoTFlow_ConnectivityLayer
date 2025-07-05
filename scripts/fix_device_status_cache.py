#!/usr/bin/env python3
"""
Script to fix incorrect device status in Redis cache
Sets devices to offline if they haven't been seen in more than 5 minutes
"""

import sys
import os
import json
import requests
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# API Configuration
API_URL = "http://localhost:5000"

def log(message, color=RESET):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{color}[{timestamp}] {message}{RESET}")

def get_all_devices():
    """Get all devices from admin API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/admin/devices")
        if response.status_code == 200:
            return response.json().get("devices", [])
        else:
            log(f"Failed to get devices: {response.status_code}", RED)
            return []
    except Exception as e:
        log(f"Error getting devices: {e}", RED)
        return []

def get_device_status_from_redis(device_id):
    """Get device status directly from Redis"""
    import subprocess
    try:
        # Get status from Redis
        status_cmd = ['docker', 'exec', 'iotflow_redis', 'redis-cli', 'get', f"device:status:{device_id}"]
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        status = result.stdout.strip().strip('"') if result.returncode == 0 else None
        
        # Get last seen from Redis
        lastseen_cmd = ['docker', 'exec', 'iotflow_redis', 'redis-cli', 'get', f"device:lastseen:{device_id}"]
        result = subprocess.run(lastseen_cmd, capture_output=True, text=True)
        last_seen_str = result.stdout.strip().strip('"') if result.returncode == 0 else None
        
        return status, last_seen_str
    except Exception as e:
        log(f"Error getting Redis status: {e}", RED)
        return None, None

def set_device_status_in_redis(device_id, status):
    """Set device status directly in Redis"""
    import subprocess
    try:
        cmd = ['docker', 'exec', 'iotflow_redis', 'redis-cli', 'set', 
               f"device:status:{device_id}", status]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        log(f"Error setting Redis status: {e}", RED)
        return False

def check_device_last_seen(last_seen_str):
    """Check if device is online based on last seen timestamp"""
    if not last_seen_str:
        return False
        
    try:
        # Parse the timestamp
        last_seen = datetime.fromisoformat(last_seen_str)
        
        # Make sure it has timezone info
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
            
        # Get current time
        now = datetime.now(timezone.utc)
        
        # Calculate time difference
        time_diff = now - last_seen
        
        # Check if device has been seen in the last 5 minutes
        return time_diff.total_seconds() < 300
    except Exception as e:
        log(f"Error parsing timestamp: {e}", RED)
        return False

def main():
    log("Device Status Cleanup Script", GREEN)
    log("---------------------------", GREEN)
    
    # Get all devices
    log("Getting all devices from API...", BLUE)
    devices = get_all_devices()
    log(f"Found {len(devices)} devices", GREEN)
    
    fixed_count = 0
    for device in devices:
        device_id = device["id"]
        name = device["name"]
        
        # Get current status from Redis
        redis_status, last_seen_str = get_device_status_from_redis(device_id)
        
        if not redis_status:
            log(f"Device {device_id} ({name}) has no Redis status entry", YELLOW)
            continue
            
        # Check if device is online based on last seen timestamp
        should_be_online = check_device_last_seen(last_seen_str)
        
        # Status doesn't match what it should be
        if (should_be_online and redis_status != "online") or (not should_be_online and redis_status != "offline"):
            correct_status = "online" if should_be_online else "offline"
            log(f"Fixing device {device_id} ({name}): {redis_status} -> {correct_status}", YELLOW)
            
            # Set correct status in Redis
            if set_device_status_in_redis(device_id, correct_status):
                log(f"Successfully updated device {device_id} status to {correct_status}", GREEN)
                fixed_count += 1
            else:
                log(f"Failed to update device {device_id} status", RED)
        else:
            log(f"Device {device_id} ({name}) status is correct: {redis_status}", GREEN)
    
    log(f"\nCleanup complete. Fixed {fixed_count} device status entries", GREEN)

if __name__ == "__main__":
    main()
