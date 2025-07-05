#!/usr/bin/env python3
"""
Test script for device status caching functionality
This script tests the interaction between MQTT, IoTFlow, and Redis for device status caching
"""

import sys
import os
import time
import json
import random
import requests
import paho.mqtt.client as mqtt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_URL = "http://localhost:5000"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = None  # Set if needed
MQTT_PASSWORD = None  # Set if needed

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log(message, color=RESET):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{color}[{timestamp}] {message}{RESET}")

def get_device_info(device_id):
    """Get device information from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/devices/{device_id}")
        if response.status_code == 200:
            return response.json().get("device")
        else:
            log(f"Failed to get device info: {response.status_code} {response.text}", RED)
            return None
    except Exception as e:
        log(f"Error getting device info: {e}", RED)
        return None

def get_device_status(device_id):
    """Get device status from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/devices/{device_id}/status")
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Failed to get device status: {response.status_code} {response.text}", RED)
            return None
    except Exception as e:
        log(f"Error getting device status: {e}", RED)
        return None

def get_all_device_statuses():
    """Get all device statuses from API"""
    try:
        response = requests.get(f"{API_URL}/api/v1/devices/statuses")
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Failed to get all device statuses: {response.status_code} {response.text}", RED)
            return None
    except Exception as e:
        log(f"Error getting all device statuses: {e}", RED)
        return None

def publish_status(client, device_id, status):
    """Publish device status to MQTT"""
    topic = f"iotflow/devices/{device_id}/status/connectivity"
    payload = {
        "api_key": get_device_info(device_id).get("api_key"),
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "reason": "Test script status update"
    }
    log(f"Publishing {status} status for device {device_id}", BLUE)
    client.publish(topic, json.dumps(payload))

def publish_telemetry(client, device_id):
    """Publish telemetry data to MQTT"""
    topic = f"iotflow/devices/{device_id}/telemetry"
    payload = {
        "api_key": get_device_info(device_id).get("api_key"),
        "temperature": round(random.uniform(20, 30), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "timestamp": datetime.now().isoformat()
    }
    log(f"Publishing telemetry for device {device_id}", BLUE)
    client.publish(topic, json.dumps(payload))

def main():
    # Welcome message
    log("Device Status Cache Test Script", GREEN)
    log("-------------------------------", GREEN)
    
    # Check API connection
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            log(f"Successfully connected to IoTFlow API at {API_URL}", GREEN)
        else:
            log(f"API check failed: {response.status_code}", RED)
            return
    except Exception as e:
        log(f"Error connecting to API: {e}", RED)
        return
    
    # List available devices
    try:
        response = requests.get(f"{API_URL}/api/v1/admin/devices")
        if response.status_code == 200:
            devices = response.json().get("devices", [])
            log(f"Found {len(devices)} devices", GREEN)
            
            if not devices:
                log("No devices available for testing", YELLOW)
                return
                
            # Select first device for testing
            test_device = devices[0]
            device_id = test_device['id']
            log(f"Using device '{test_device['name']}' (ID: {device_id}) for testing", GREEN)
        else:
            log(f"Failed to get devices: {response.status_code}", RED)
            return
    except Exception as e:
        log(f"Error getting devices: {e}", RED)
        return
    
    # Connect to MQTT broker
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        log(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}", GREEN)
    except Exception as e:
        log(f"Error connecting to MQTT broker: {e}", RED)
        return
    
    try:
        # Test 1: Check current device status
        log("\nTest 1: Checking current device status", GREEN)
        status_before = get_device_status(device_id)
        if status_before:
            is_online = status_before.get("device", {}).get("is_online", False)
            log(f"Current status: {'ONLINE' if is_online else 'OFFLINE'}", 
                GREEN if is_online else YELLOW)
        
        # Test 2: Publish online status
        log("\nTest 2: Publishing ONLINE status", GREEN)
        publish_status(client, device_id, "online")
        time.sleep(2)  # Wait for message processing
        
        status_after = get_device_status(device_id)
        if status_after:
            is_online = status_after.get("device", {}).get("is_online", False)
            log(f"Status after publishing ONLINE: {'ONLINE' if is_online else 'OFFLINE'}", 
                GREEN if is_online else RED)
        
        # Test 3: Publish telemetry (should update last_seen)
        log("\nTest 3: Publishing telemetry data", GREEN)
        publish_telemetry(client, device_id)
        time.sleep(2)  # Wait for message processing
        
        status_after_telemetry = get_device_status(device_id)
        if status_after_telemetry:
            is_online = status_after_telemetry.get("device", {}).get("is_online", False)
            log(f"Status after publishing telemetry: {'ONLINE' if is_online else 'OFFLINE'}", 
                GREEN if is_online else RED)
        
        # Test 4: Get all device statuses
        log("\nTest 4: Getting all device statuses", GREEN)
        all_statuses = get_all_device_statuses()
        if all_statuses:
            cache_used = all_statuses.get("meta", {}).get("cache_used", False)
            log(f"Redis cache used: {cache_used}", GREEN if cache_used else YELLOW)
            log(f"Found {len(all_statuses.get('devices', []))} device statuses", GREEN)
            
            # Check if our test device is in the results
            device_found = False
            for device in all_statuses.get("devices", []):
                if device.get("id") == device_id:
                    device_found = True
                    is_online = device.get("is_online", False)
                    log(f"Test device status in bulk query: {'ONLINE' if is_online else 'OFFLINE'}", 
                        GREEN if is_online else RED)
                    break
                    
            if not device_found:
                log("Test device not found in bulk status query", RED)
        
        # Test 5: Publish offline status
        log("\nTest 5: Publishing OFFLINE status", GREEN)
        publish_status(client, device_id, "offline")
        time.sleep(2)  # Wait for message processing
        
        final_status = get_device_status(device_id)
        if final_status:
            is_online = final_status.get("device", {}).get("is_online", False)
            log(f"Final status after publishing OFFLINE: {'ONLINE' if is_online else 'OFFLINE'}", 
                RED if is_online else GREEN)
        
        log("\nDevice status cache test completed", GREEN)
        
    except Exception as e:
        log(f"Error during testing: {e}", RED)
    finally:
        # Clean up
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
