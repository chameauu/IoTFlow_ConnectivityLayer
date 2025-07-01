#!/usr/bin/env python3
"""
Test script for InfluxDB integration in IoTFlow Connectivity Layer.
Tests both direct InfluxDB operations and HTTP API endpoints.
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "your-api-key-here"  # Replace with actual API key
DEVICE_ID = "test-device-001"

def test_influxdb_health():
    """Test InfluxDB health endpoint"""
    print("🏥 Testing InfluxDB health...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/influxdb/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ InfluxDB Health: {health_data}")
            return True
        else:
            print(f"❌ InfluxDB health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking InfluxDB health: {e}")
        return False

def test_write_telemetry_direct():
    """Test writing telemetry data directly to InfluxDB API"""
    print("📊 Testing direct telemetry write to InfluxDB...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    telemetry_data = {
        "device_id": DEVICE_ID,
        "measurement": "temperature",
        "fields": {
            "value": 23.5,
            "humidity": 45.0,
            "pressure": 1013.25
        },
        "tags": {
            "location": "office",
            "sensor_type": "dht22"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/influxdb/telemetry",
            headers=headers,
            json=telemetry_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Direct telemetry write successful: {result}")
            return True
        else:
            print(f"❌ Direct telemetry write failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error writing telemetry directly: {e}")
        return False

def test_write_telemetry_batch():
    """Test writing batch telemetry data to InfluxDB"""
    print("📊 Testing batch telemetry write to InfluxDB...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    batch_data = {
        "points": [
            {
                "device_id": DEVICE_ID,
                "measurement": "temperature",
                "fields": {"value": 24.0},
                "tags": {"location": "kitchen"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "device_id": DEVICE_ID,
                "measurement": "humidity",
                "fields": {"value": 50.0},
                "tags": {"location": "kitchen"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "device_id": DEVICE_ID,
                "measurement": "pressure",
                "fields": {"value": 1015.0},
                "tags": {"location": "kitchen"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/influxdb/telemetry/batch",
            headers=headers,
            json=batch_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Batch telemetry write successful: {result}")
            return True
        else:
            print(f"❌ Batch telemetry write failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error writing batch telemetry: {e}")
        return False

def test_query_device_data():
    """Test querying device data from InfluxDB"""
    print("🔍 Testing device data query from InfluxDB...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    # Wait a bit for data to be written
    time.sleep(2)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/influxdb/device/{DEVICE_ID}/data",
            headers=headers,
            params={"start": "-1h", "stop": "now()"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Device data query successful: Found {result.get('count', 0)} data points")
            if result.get('data_points'):
                print(f"Sample data point: {result['data_points'][0]}")
            return True
        else:
            print(f"❌ Device data query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error querying device data: {e}")
        return False

def test_get_latest_data():
    """Test getting latest device data from InfluxDB"""
    print("🔍 Testing latest device data query from InfluxDB...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/influxdb/device/{DEVICE_ID}/latest",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Latest data query successful: {result}")
            return True
        elif response.status_code == 404:
            print("ℹ️ No latest data found (expected for new device)")
            return True
        else:
            print(f"❌ Latest data query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting latest data: {e}")
        return False

def test_device_telemetry_integration():
    """Test device telemetry submission with InfluxDB integration"""
    print("🔗 Testing device telemetry submission with InfluxDB integration...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # First register a test device if it doesn't exist
    device_data = {
        "name": DEVICE_ID,
        "device_type": "sensor",
        "description": "Test device for InfluxDB integration",
        "location": "test_lab"
    }
    
    # Try to register device (may fail if already exists)
    try:
        register_response = requests.post(
            f"{BASE_URL}/api/v1/devices/register",
            headers=headers,
            json=device_data
        )
        if register_response.status_code == 201:
            print(f"✅ Test device registered successfully")
            device_info = register_response.json()
            device_api_key = device_info.get('device', {}).get('api_key', API_KEY)
        else:
            print(f"ℹ️ Device registration failed (may already exist): {register_response.status_code}")
            device_api_key = API_KEY  # Use existing API key
    except Exception as e:
        print(f"ℹ️ Device registration error: {e}")
        device_api_key = API_KEY
    
    # Submit telemetry data via device API
    telemetry_headers = {
        "Content-Type": "application/json",
        "X-API-Key": device_api_key
    }
    
    telemetry_payload = {
        "data": {
            "temperature": 25.5,
            "humidity": 60.0,
            "battery_level": 85.0,
            "signal_strength": -45
        },
        "type": "environmental",
        "metadata": {
            "firmware_version": "1.0.0",
            "location": "test_lab"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/devices/telemetry",
            headers=telemetry_headers,
            json=telemetry_payload
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Device telemetry submission successful: {result}")
            return True
        else:
            print(f"❌ Device telemetry submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error submitting device telemetry: {e}")
        return False

def test_influxdb_stats():
    """Test InfluxDB statistics endpoint"""
    print("📈 Testing InfluxDB statistics...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/influxdb/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ InfluxDB stats: {stats}")
            return True
        else:
            print(f"❌ InfluxDB stats failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting InfluxDB stats: {e}")
        return False

def main():
    """Run all InfluxDB integration tests"""
    print("🚀 Starting InfluxDB Integration Tests")
    print("=" * 50)
    
    tests = [
        test_influxdb_health,
        test_influxdb_stats,
        test_write_telemetry_direct,
        test_write_telemetry_batch,
        test_query_device_data,
        test_get_latest_data,
        test_device_telemetry_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n{'-' * 30}")
        try:
            if test():
                passed += 1
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All InfluxDB integration tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
