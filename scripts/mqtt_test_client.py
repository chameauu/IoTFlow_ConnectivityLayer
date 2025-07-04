#!/usr/bin/env python3
"""
MQTT Test Client
Test MQTT broker connectivity and simulate device messages
"""

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# MQTT settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        # Subscribe to all device topics for monitoring
        client.subscribe("iotflow/devices/+/+/+")
        print("📡 Subscribed to all device topics")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    print(f"\n📨 Received message:")
    print(f"   Topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"   Payload: {json.dumps(payload, indent=4)}")
    except:
        print(f"   Payload: {msg.payload.decode()}")

def send_test_data(client, device_id, api_key):
    """Send test telemetry data"""
    
    # Create test payload matching your ESP32 format
    payload = {
        "api_key": api_key,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "temperature": round(20 + random.uniform(-5, 10), 2),
            "humidity": round(50 + random.uniform(-10, 20), 2),
            "wifi_rssi": random.randint(-80, -30),
            "free_heap": random.randint(200000, 300000),
            "uptime": int(time.time())
        },
        "metadata": {
            "device_type": "esp32",
            "firmware_version": "1.0.0",
            "location": "test"
        }
    }
    
    # Send to telemetry topic
    topic = f"iotflow/devices/{device_id}/telemetry/sensors"
    
    message = json.dumps(payload)
    result = client.publish(topic, message)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Test data sent to {topic}")
        print(f"   Data: {json.dumps(payload['data'], indent=2)}")
    else:
        print(f"❌ Failed to send test data, error code: {result.rc}")

def main():
    print("🚀 MQTT Test Client for IoTFlow")
    print("=" * 50)
    
    # Get device info
    device_id = input("Enter device ID (e.g., 1): ").strip()
    api_key = input("Enter device API key: ").strip()
    
    if not device_id or not api_key:
        print("❌ Device ID and API key are required")
        return
    
    # Create MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print(f"🔌 Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        
        # Start the loop
        client.loop_start()
        
        print("👂 Listening for messages... Press Enter to send test data, 'q' to quit")
        
        while True:
            user_input = input().strip()
            
            if user_input.lower() == 'q':
                break
            else:
                send_test_data(client, device_id, api_key)
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
