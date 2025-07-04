#!/usr/bin/env python3
"""
ESP32 Device Registration Test Script
Test the device registration process for ESP32 devices
"""

import requests
import json
import sys
from datetime import datetime

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 5000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api/v1"

def register_device(device_name, device_type="esp32", location="test_lab"):
    """Register a new ESP32 device"""
    
    registration_data = {
        "name": device_name,
        "device_type": device_type,
        "description": f"ESP32 IoT device: {device_name}",
        "location": location,
        "firmware_version": "1.0.0",
        "hardware_version": "ESP32-WROOM-32",
        "capabilities": [
            "temperature",
            "humidity", 
            "wifi_monitoring",
            "remote_control"
        ],
        "metadata": {
            "registration_method": "script",
            "test_device": True
        }
    }
    
    try:
        print(f"🚀 Registering device: {device_name}")
        print(f"📡 Endpoint: {BASE_URL}/devices/register")
        
        response = requests.post(
            f"{BASE_URL}/devices/register",
            json=registration_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 201:
            # Success
            result = response.json()
            device_info = result.get("device", {})
            
            print("✅ Device registered successfully!")
            print(f"📋 Device ID: {device_info.get('id')}")
            print(f"🔑 API Key: {device_info.get('api_key')}")
            print(f"📝 Device Name: {device_info.get('name')}")
            print(f"📅 Created: {device_info.get('created_at')}")
            
            # Save registration info to file
            reg_info = {
                "device_id": device_info.get('id'),
                "device_name": device_info.get('name'),
                "api_key": device_info.get('api_key'),
                "registration_time": datetime.now().isoformat(),
                "server_host": SERVER_HOST,
                "server_port": SERVER_PORT
            }
            
            filename = f"device_registration_{device_name}.json"
            with open(filename, 'w') as f:
                json.dump(reg_info, f, indent=2)
            
            print(f"💾 Registration info saved to: {filename}")
            
            return True, device_info
            
        elif response.status_code == 409:
            # Device already exists
            print("⚠️ Device already registered")
            result = response.json()
            print(f"Error: {result.get('error')}")
            print(f"Message: {result.get('message')}")
            return False, None
            
        else:
            # Other error
            print(f"❌ Registration failed")
            try:
                result = response.json()
                print(f"Error: {result.get('error')}")
                print(f"Message: {result.get('message')}")
            except:
                print(f"Response: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running: ./docker-manage.sh start")
        return False, None

def test_device_status(device_id, api_key):
    """Test device status endpoint"""
    try:
        print(f"\n🔍 Testing device status for ID: {device_id}")
        
        response = requests.get(
            f"{BASE_URL}/devices/status",
            headers={"X-API-Key": api_key},
            timeout=10
        )
        
        print(f"📡 Status check HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Device status check successful!")
            print(f"📊 Status: {result.get('status')}")
            print(f"📍 Last seen: {result.get('last_seen')}")
            return True
        else:
            print("❌ Status check failed")
            try:
                result = response.json()
                print(f"Error: {result.get('error')}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Status check error: {e}")
        return False

def send_test_telemetry(device_id, api_key):
    """Send test telemetry data"""
    try:
        print(f"\n📊 Sending test telemetry for device ID: {device_id}")
        
        telemetry_data = {
            "api_key": api_key,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "temperature": 23.5,
                "humidity": 65.2,
                "wifi_rssi": -45,
                "free_heap": 250000,
                "uptime": 3600
            },
            "metadata": {
                "device_type": "esp32",
                "firmware_version": "1.0.0",
                "location": "test_lab",
                "test_message": True
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/mqtt/telemetry/{device_id}",
            json=telemetry_data,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"📡 Telemetry HTTP Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Test telemetry sent successfully!")
            print(f"📨 Message: {result.get('message')}")
            print(f"📍 Topic: {result.get('topic')}")
            return True
        else:
            print("❌ Telemetry send failed")
            try:
                result = response.json()
                print(f"Error: {result.get('error')}")
                print(f"Message: {result.get('message')}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Telemetry send error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 esp32_registration_test.py <device_name>")
        print("Example: python3 esp32_registration_test.py my_esp32_001")
        sys.exit(1)
    
    device_name = sys.argv[1]
    
    print("🚀 ESP32 Device Registration Test")
    print("=" * 50)
    
    # Step 1: Register device
    success, device_info = register_device(device_name)
    
    if success and device_info:
        device_id = device_info.get('id')
        api_key = device_info.get('api_key')
        
        # Step 2: Test device status
        test_device_status(device_id, api_key)
        
        # Step 3: Send test telemetry
        send_test_telemetry(device_id, api_key)
        
        print("\n" + "=" * 50)
        print("🎯 ESP32 Configuration for Arduino IDE:")
        print("=" * 50)
        print(f'const int device_id = {device_id};')
        print(f'const char* device_api_key = "{api_key}";')
        print(f'String device_name = "{device_name}";')
        print(f'const char* server_host = "{SERVER_HOST}";')
        print(f'const int http_port = {SERVER_PORT};')
        print("=" * 50)
        print("💡 Copy these values to your ESP32 code!")
        
    else:
        print("\n❌ Registration failed - check server status and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
