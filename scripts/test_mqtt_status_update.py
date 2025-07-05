#!/usr/bin/env python3
"""
Script to test MQTT status updates and Redis caching
"""

import paho.mqtt.client as mqtt
import json
import time
import requests
import sys
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
DEVICE_ID = 1  # Change this to match a device in your system

# API Configuration
API_URL = "http://localhost:5000"

# ANSI Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log(message, color=RESET):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{color}[{timestamp}] {message}{RESET}")

def get_device_api_key(device_id):
    """Get device API key from the API"""
    try:
        # First try to get registered devices
        response = requests.get(f"{API_URL}/api/v1/devices/register", 
                               json={"name": "test_device", "device_type": "sensor"})
        if response.status_code == 200:
            api_key = response.json().get("device", {}).get("api_key")
            if api_key:
                log(f"Retrieved API key from registration response", GREEN)
                return api_key
        
        # Fallback to a hardcoded API key for testing
        log(f"Using hardcoded API key for testing", YELLOW)
        return "iotflow_test_api_key_12345"
    except Exception as e:
        log(f"Error getting device API key: {e}", RED)
        log(f"Using hardcoded API key for testing", YELLOW)
        return "iotflow_test_api_key_12345"

def get_device_status(device_id):
    """Get current device status from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/devices/{device_id}/status")
        if response.status_code == 200:
            device = response.json().get("device", {})
            status = "ONLINE" if device.get("is_online") else "OFFLINE"
            source = device.get("status_source", "unknown")
            log(f"Device status: {status} (Source: {source})", 
                GREEN if status == "ONLINE" else YELLOW)
            return device
        else:
            log(f"Failed to get device status: {response.status_code}", RED)
            return None
    except Exception as e:
        log(f"Error getting device status: {e}", RED)
        return None

def check_redis_status(device_id):
    """Check device status in Redis (via command line)"""
    import subprocess
    try:
        # Run Redis CLI command to get device status
        result = subprocess.run(
            ['docker', 'exec', 'iotflow_redis', 'redis-cli', 'get', f"device:status:{device_id}"],
            capture_output=True, text=True, check=True
        )
        status = result.stdout.strip().strip('"')
        log(f"Redis status for device {device_id}: {status}", 
            GREEN if status == "online" else YELLOW)
        return status
    except subprocess.CalledProcessError as e:
        log(f"Error checking Redis status: {e}", RED)
        return None
    except Exception as e:
        log(f"Exception checking Redis status: {e}", RED)
        return None

def main():
    if len(sys.argv) > 1:
        device_id = int(sys.argv[1])
    else:
        device_id = DEVICE_ID
        
    log(f"MQTT Status Update Test for Device ID: {device_id}", GREEN)
    log("-----------------------------------------------", GREEN)
    
    # Get device API key
    api_key = get_device_api_key(device_id)
    if not api_key:
        log("Cannot continue without API key", RED)
        return
    
    # Check initial status
    log("Checking initial device status:", BLUE)
    initial_status = get_device_status(device_id)
    check_redis_status(device_id)
    
    # Connect to MQTT broker
    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        log(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}", GREEN)
    except Exception as e:
        log(f"Error connecting to MQTT broker: {e}", RED)
        return
    
    try:
        # Test 1: Set device to OFFLINE
        log("\nTest 1: Publishing OFFLINE status", BLUE)
        
        # Create payload with API key
        offline_payload = {
            "api_key": api_key,
            "status": "offline",
            "timestamp": datetime.now().isoformat(),
            "reason": "Test script"
        }
        
        # Publish to device status topic
        topic = f"iotflow/devices/{device_id}/status/connectivity"
        client.publish(topic, json.dumps(offline_payload))
        log(f"Published OFFLINE status to {topic}", BLUE)
        
        # Wait for status to propagate
        log("Waiting for status to propagate...", YELLOW)
        time.sleep(2)
        
        # Check status after change
        log("Checking status after publishing OFFLINE:", BLUE)
        get_device_status(device_id)
        check_redis_status(device_id)
        
        # Test 2: Set device to ONLINE
        log("\nTest 2: Publishing ONLINE status", BLUE)
        
        # Create payload with API key
        online_payload = {
            "api_key": api_key,
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "reason": "Test script"
        }
        
        # Publish to device status topic
        client.publish(topic, json.dumps(online_payload))
        log(f"Published ONLINE status to {topic}", BLUE)
        
        # Wait for status to propagate
        log("Waiting for status to propagate...", YELLOW)
        time.sleep(2)
        
        # Check status after change
        log("Checking status after publishing ONLINE:", BLUE)
        get_device_status(device_id)
        check_redis_status(device_id)
        
        log("\nTest complete!", GREEN)
        
    except Exception as e:
        log(f"Error during testing: {e}", RED)
    finally:
        # Clean up
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
