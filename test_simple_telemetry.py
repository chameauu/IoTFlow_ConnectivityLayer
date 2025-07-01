#!/usr/bin/env python3
"""
Simple telemetry test to verify HTTP API and InfluxDB integration.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "your-api-key-here"  # We'll get a real one from device registration

def test_device_registration_and_telemetry():
    """Test device registration and telemetry submission"""
    print("🧪 Testing Device Registration and Telemetry Flow")
    print("=" * 60)
    
    # Step 1: Register a test device
    print("1. Registering test device...")
    device_data = {
        "name": "Test ESP32 Sensor",
        "device_type": "environmental",
        "description": "Test device for InfluxDB integration",
        "location": "test_lab"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/devices/register", 
                               headers=headers, json=device_data)
        
        if response.status_code == 201:
            device_info = response.json()
            device_api_key = device_info["device"]["api_key"]
            device_id = device_info["device"]["id"]
            print(f"   ✅ Device registered successfully (ID: {device_id})")
            print(f"   🔑 API Key: {device_api_key}")
        elif response.status_code == 409:
            print("   ℹ️ Device already exists, continuing with test...")
            # Try to get existing device info by querying status
            device_api_key = "cLqrHXbPJDvO1fblPiSsSwpL1LwYxrQX"  # From previous registration
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False
    
    # Step 2: Send telemetry data
    print("2. Sending telemetry data...")
    telemetry_headers = {
        "Content-Type": "application/json",
        "X-API-Key": device_api_key
    }
    
    for i in range(5):
        telemetry_data = {
            "data": {
                "temperature": 20 + i * 2.5,
                "humidity": 50 + i * 5,
                "pressure": 1013 + i * 2,
                "battery_level": 95 - i
            },
            "type": "sensor_reading",
            "metadata": {
                "location": "test_lab",
                "test_sequence": i + 1
            }
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/devices/telemetry",
                                   headers=telemetry_headers, json=telemetry_data)
            
            if response.status_code == 201:
                result = response.json()
                print(f"   ✅ Telemetry {i+1}/5 sent successfully (ID: {result.get('telemetry_id')})")
            else:
                print(f"   ❌ Telemetry {i+1}/5 failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Telemetry error: {e}")
        
        time.sleep(1)  # Small delay between submissions
    
    # Step 3: Check InfluxDB health
    print("3. Checking InfluxDB status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/influxdb/health",
                              headers={"X-API-Key": device_api_key})
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ InfluxDB status: {health_data['influxdb']['status']}")
        else:
            print(f"   ⚠️ InfluxDB health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ InfluxDB health check error: {e}")
    
    # Step 4: Query data from InfluxDB (if endpoint exists)
    print("4. Querying telemetry data...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/devices/telemetry",
                              headers={"X-API-Key": device_api_key})
        
        if response.status_code == 200:
            telemetry_result = response.json()
            count = telemetry_result.get('count', 0)
            print(f"   ✅ Retrieved {count} telemetry records from PostgreSQL")
        else:
            print(f"   ⚠️ Telemetry query failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Telemetry query error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Test completed!")
    print("\nNext steps:")
    print("1. Check InfluxDB UI at http://localhost:8086")
    print("2. Check Grafana at http://localhost:3000")
    print("3. Verify data appears in the 'telemetry' bucket")
    print("4. Run the full integration test for MQTT simulation")
    
    return True

if __name__ == "__main__":
    test_device_registration_and_telemetry()
