#!/usr/bin/env python3
"""
Fixes telemetry data format and sends test messages to verify data flow
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime
import sys
import requests

# MQTT settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def check_api_data(device_id):
    """Check if data appears in the API"""
    try:
        response = requests.get(f"http://localhost:5000/api/v1/telemetry/{device_id}/latest")
        print(f"API Response ({response.status_code}):")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"Error checking API: {str(e)}")
        return None

def send_test_data(client, device_id, api_key):
    """Send test telemetry data in the proper format"""
    
    # Current timestamp
    timestamp = datetime.now().isoformat()
    
    # Method 1: Format data as expected by IoTFlow (with data field)
    payload_proper = {
        "api_key": api_key,
        "timestamp": timestamp,
        "data": {
            "temperature": 28.5,
            "humidity": 65,
            "heat_index": 30,
            "cpu_temp": 52.8,
            "free_heap": 246000,
            "uptime": int(time.time()),
            "wifi_rssi": -68,
            "led_state": 1
        },
        "metadata": {
            "device_type": "esp32",
            "firmware_version": "1.0.0"
        }
    }
    
    # Method 2: Format data like your ESP32 is currently sending
    # (flat structure with all data at the root level)
    payload_flat = {
        "api_key": api_key,
        "ts": str(int(time.time())),
        "temperature": 28.5,
        "humidity": 65,
        "heat_index": 30,
        "cpu_temp": 52.8,
        "free_heap": 246000,
        "uptime": int(time.time()),
        "wifi_rssi": -68,
        "led_state": 1
    }
    
    print("\n=== Testing with proper structured format ===")
    # Send to main telemetry topic (without /sensors)
    topic_proper = f"iotflow/devices/{device_id}/telemetry"
    message_proper = json.dumps(payload_proper)
    result = client.publish(topic_proper, message_proper)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Sent properly formatted data to {topic_proper}")
        print(f"   Data: {json.dumps(payload_proper, indent=2)}")
    else:
        print(f"❌ Failed to send data, error code: {result.rc}")
    
    # Wait for data processing
    print("Waiting 3 seconds for data to be processed...")
    time.sleep(3)
    
    # Check if data appears in API
    print("\nChecking API for properly formatted data:")
    check_api_data(device_id)
    
    print("\n=== Testing with flat format to main topic ===")
    # Try flat format to main telemetry topic 
    topic_flat_main = f"iotflow/devices/{device_id}/telemetry"
    message_flat = json.dumps(payload_flat)
    result = client.publish(topic_flat_main, message_flat)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Sent flat formatted data to {topic_flat_main}")
        print(f"   Data: {message_flat}")
    else:
        print(f"❌ Failed to send data, error code: {result.rc}")
    
    # Wait for data processing
    print("Waiting 3 seconds for data to be processed...")
    time.sleep(3)
    
    # Check if data appears in API
    print("\nChecking API after sending flat data to main topic:")
    check_api_data(device_id)
    
    print("\n=== Testing with flat format to sensors topic ===")
    # Also try flat format to the sensors topic (what ESP32 is sending to)
    topic_flat_sensors = f"iotflow/devices/{device_id}/telemetry/sensors"
    result = client.publish(topic_flat_sensors, message_flat)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Sent flat formatted data to {topic_flat_sensors}")
        print(f"   Data: {message_flat}")
    else:
        print(f"❌ Failed to send data, error code: {result.rc}")
    
    # Wait for data processing
    print("Waiting 3 seconds for data to be processed...")
    time.sleep(3)
    
    # Check if data appears in API
    print("\nChecking API after sending flat data to sensors topic:")
    check_api_data(device_id)

def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_telemetry.py <device_id> <api_key>")
        return
        
    device_id = sys.argv[1]
    api_key = sys.argv[2]
    
    print(f"🔍 Testing telemetry data flow for device {device_id}")
    print("=" * 50)
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        print(f"🔌 Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        
        # Start the loop
        client.loop_start()
        time.sleep(1)  # Wait for connection
        
        # Send test data
        send_test_data(client, device_id, api_key)
        
        # Clean up
        client.loop_stop()
        client.disconnect()
        
    except KeyboardInterrupt:
        print("\n⚠️ User interrupted")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
