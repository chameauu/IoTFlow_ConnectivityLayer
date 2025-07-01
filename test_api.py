#!/usr/bin/env python3
"""
API Testing Script for IoT Connectivity Layer
This script demonstrates how to interact with the API endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_VERSION = "v1"

class IoTAPITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.device_api_key = None
        self.device_id = None
    
    def test_health_check(self):
        """Test the health check endpoint"""
        print("\n1. Testing Health Check...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def test_device_registration(self):
        """Test device registration"""
        print("\n2. Testing Device Registration...")
        
        device_data = {
            "name": f"Test Device {int(time.time())}",
            "description": "Test device for API validation",
            "device_type": "sensor",
            "location": "Test Lab",
            "firmware_version": "1.0.0",
            "hardware_version": "v1.0"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/{API_VERSION}/devices/register",
                json=device_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"Device registered successfully!")
                print(f"Device ID: {data['device']['id']}")
                print(f"API Key: {data['device']['api_key']}")
                
                # Store for subsequent tests
                self.device_api_key = data['device']['api_key']
                self.device_id = data['device']['id']
                return True
            else:
                print(f"Registration failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def test_device_status(self):
        """Test device status endpoint"""
        print("\n3. Testing Device Status...")
        
        if not self.device_api_key:
            print("No API key available. Skipping test.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/{API_VERSION}/devices/status",
                headers={"X-API-Key": self.device_api_key}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Device status retrieved successfully!")
                print(f"Device Name: {data['device']['name']}")
                print(f"Status: {data['device']['status']}")
                print(f"Online: {data['device']['is_online']}")
                return True
            else:
                print(f"Status check failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def test_telemetry_submission(self):
        """Test telemetry data submission"""
        print("\n4. Testing Telemetry Submission...")
        
        if not self.device_api_key:
            print("No API key available. Skipping test.")
            return False
        
        # Send multiple telemetry records
        test_data = [
            {
                "data": {
                    "temperature": 22.5,
                    "humidity": 65,
                    "pressure": 1013.25
                },
                "metadata": {
                    "battery_level": 85,
                    "signal_strength": -45
                },
                "type": "sensor"
            },
            {
                "data": {
                    "temperature": 23.1,
                    "humidity": 62,
                    "pressure": 1012.8
                },
                "metadata": {
                    "battery_level": 84,
                    "signal_strength": -43
                },
                "type": "sensor"
            }
        ]
        
        success_count = 0
        
        for i, telemetry_data in enumerate(test_data, 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/{API_VERSION}/devices/telemetry",
                    json=telemetry_data,
                    headers={
                        "X-API-Key": self.device_api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"  Telemetry {i} - Status Code: {response.status_code}")
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"  Telemetry {i} - ID: {data['telemetry_id']}")
                    success_count += 1
                else:
                    print(f"  Telemetry {i} - Failed: {response.json()}")
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Telemetry {i} - Error: {str(e)}")
        
        print(f"Successfully submitted {success_count}/{len(test_data)} telemetry records")
        return success_count > 0
    
    def test_telemetry_retrieval(self):
        """Test telemetry data retrieval"""
        print("\n5. Testing Telemetry Retrieval...")
        
        if not self.device_api_key:
            print("No API key available. Skipping test.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/{API_VERSION}/devices/telemetry?limit=5",
                headers={"X-API-Key": self.device_api_key}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved {data['count']} telemetry records")
                
                for i, record in enumerate(data['telemetry'][:2], 1):  # Show first 2
                    print(f"  Record {i}:")
                    print(f"    Timestamp: {record['timestamp']}")
                    print(f"    Data: {record['payload']}")
                
                return True
            else:
                print(f"Retrieval failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def test_heartbeat(self):
        """Test device heartbeat"""
        print("\n6. Testing Device Heartbeat...")
        
        if not self.device_api_key:
            print("No API key available. Skipping test.")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/{API_VERSION}/devices/heartbeat",
                headers={"X-API-Key": self.device_api_key}
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Heartbeat successful!")
                print(f"Device ID: {data['device_id']}")
                print(f"Status: {data['status']}")
                return True
            else:
                print(f"Heartbeat failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def test_admin_endpoints(self):
        """Test admin endpoints (no authentication required for demo)"""
        print("\n7. Testing Admin Endpoints...")
        
        # Test dashboard stats
        try:
            response = requests.get(f"{self.base_url}/api/{API_VERSION}/admin/dashboard")
            print(f"Dashboard - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                stats = data['statistics']
                print(f"  Total Devices: {stats['devices']['total']}")
                print(f"  Active Devices: {stats['devices']['active']}")
                print(f"  Total Telemetry: {stats['telemetry']['total_records']}")
            
        except Exception as e:
            print(f"Dashboard Error: {str(e)}")
        
        # Test device listing
        try:
            response = requests.get(f"{self.base_url}/api/{API_VERSION}/admin/devices?per_page=5")
            print(f"Device List - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Listed {len(data['devices'])} devices")
                print(f"  Total devices in system: {data['pagination']['total']}")
            
        except Exception as e:
            print(f"Device List Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("IoT Connectivity Layer - API Testing")
        print("="*50)
        
        test_results = []
        
        # Run tests
        test_results.append(("Health Check", self.test_health_check()))
        test_results.append(("Device Registration", self.test_device_registration()))
        test_results.append(("Device Status", self.test_device_status()))
        test_results.append(("Telemetry Submission", self.test_telemetry_submission()))
        test_results.append(("Telemetry Retrieval", self.test_telemetry_retrieval()))
        test_results.append(("Device Heartbeat", self.test_heartbeat()))
        
        # Admin tests (always run regardless of device registration)
        self.test_admin_endpoints()
        
        # Print summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = 0
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\nPassed: {passed}/{len(test_results)} tests")
        
        if self.device_api_key:
            print(f"\nTest device API key: {self.device_api_key}")
            print("You can use this API key for manual testing.")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("Server is not responding correctly. Please start the Flask application.")
            exit(1)
    except requests.exceptions.RequestException:
        print("Cannot connect to the server. Please ensure the Flask application is running on http://localhost:5000")
        print("\nTo start the server, run: python app.py")
        exit(1)
    
    # Run tests
    tester = IoTAPITester()
    tester.run_all_tests()
