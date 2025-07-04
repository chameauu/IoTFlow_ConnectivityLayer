#!/usr/bin/env python3
"""
End-to-End Test Script for IoT Connectivity Layer
Tests everything from initialization to telemetry storage in InfluxDB
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import random
import uuid

class IoTFlowTester:
    def __init__(self, base_url="http://localhost:5000", mqtt_host="localhost", mqtt_port=1883):
        self.base_url = base_url
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.session = requests.Session()
        self.test_device_id = None
        self.test_api_key = None
        self.mqtt_client = None
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": "✅ PASS" if status else "❌ FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{result['status']} {test_name}")
        if details:
            print(f"   └─ {details}")
    
    def test_system_health(self):
        """Test 1: Check system health"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("System Health Check", True, f"Status: {data.get('status')}, Version: {data.get('version')}")
                return True
            else:
                self.log_test("System Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Health Check", False, str(e))
            return False
    
    def test_mqtt_broker_connection(self):
        """Test 2: Check MQTT broker connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/mqtt/status")
            if response.status_code == 200:
                data = response.json()
                connected = data.get('broker_info', {}).get('connected', False)
                self.log_test("MQTT Broker Connection", connected, f"Broker connected: {connected}")
                return connected
            else:
                self.log_test("MQTT Broker Connection", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MQTT Broker Connection", False, str(e))
            return False
    
    def test_device_registration(self):
        """Test 3: Register a new device"""
        try:
            device_name = f"E2E_Test_Device_{int(time.time())}"
            payload = {
                "name": device_name,
                "device_type": "sensor",
                "description": "End-to-end test device",
                "location": "Test Lab",
                "firmware_version": "1.0.0",
                "hardware_version": "v1.0"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/devices/register",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code in [200, 201]:  # Accept both 200 and 201
                data = response.json()
                device_info = data.get('device', {})
                self.test_device_id = device_info.get('id')
                self.test_api_key = device_info.get('api_key')
                self.log_test("Device Registration", True, f"Device ID: {self.test_device_id}, Name: {device_name}")
                return True
            else:
                self.log_test("Device Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Device Registration", False, str(e))
            return False
    
    def test_device_authentication(self):
        """Test 4: Test device authentication with API key"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            response = self.session.get(f"{self.base_url}/api/v1/devices/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                device_info = data.get('device', {})
                self.log_test("Device Authentication", True, f"Device authenticated: {device_info.get('name')}")
                return True
            else:
                self.log_test("Device Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Device Authentication", False, str(e))
            return False
    
    def test_device_configuration(self):
        """Test 5: Set and get device configuration"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            # Set configuration
            config_payload = {
                "config_key": "sampling_rate",
                "config_value": "30",
                "data_type": "integer"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/devices/config",
                headers=headers,
                json=config_payload
            )
            
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Device Configuration", False, f"Set config failed: HTTP {response.status_code}")
                return False
            
            # Get configuration
            response = self.session.get(f"{self.base_url}/api/v1/devices/config", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                config = data.get('configuration', {})
                self.log_test("Device Configuration", True, f"Config set and retrieved: {len(config)} items")
                return True
            else:
                self.log_test("Device Configuration", False, f"Get config failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Device Configuration", False, str(e))
            return False
    
    def test_rest_telemetry_submission(self):
        """Test 6: Submit telemetry via REST API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            telemetry_payload = {
                "data": {
                    "temperature": round(random.uniform(20.0, 30.0), 2),
                    "humidity": round(random.uniform(40.0, 80.0), 2),
                    "pressure": round(random.uniform(1000.0, 1020.0), 2)
                },
                "metadata": {
                    "sensor_type": "BME280",
                    "location": "test_lab",
                    "test_method": "rest_api"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/telemetry",
                headers=headers,
                json=telemetry_payload
            )
            
            if response.status_code in [200, 201]:  # Accept both 200 and 201
                data = response.json()
                self.log_test("REST Telemetry Submission", True, f"Telemetry stored: {data.get('message')}")
                return True
            else:
                self.log_test("REST Telemetry Submission", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("REST Telemetry Submission", False, str(e))
            return False
    
    def test_mqtt_telemetry_submission(self):
        """Test 7: Submit telemetry via MQTT"""
        try:
            # Create MQTT client
            client_id = f"e2e_test_{uuid.uuid4().hex[:8]}"
            self.mqtt_client = mqtt.Client(client_id)
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Prepare telemetry payload
            telemetry_payload = {
                "api_key": self.test_api_key,
                "data": {
                    "temperature": round(random.uniform(20.0, 30.0), 2),
                    "humidity": round(random.uniform(40.0, 80.0), 2),
                    "voltage": round(random.uniform(3.0, 3.7), 2)
                },
                "metadata": {
                    "sensor_type": "DHT22",
                    "location": "test_lab",
                    "test_method": "mqtt"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Publish to correct telemetry topic
            topic = f"iotflow/devices/{self.test_device_id}/telemetry"
            result = self.mqtt_client.publish(topic, json.dumps(telemetry_payload))
            
            # Wait for message to be processed
            time.sleep(2)
            
            # Disconnect
            self.mqtt_client.disconnect()
            
            self.log_test("MQTT Telemetry Submission", True, f"Published to topic: {topic}")
            return True
            
        except Exception as e:
            self.log_test("MQTT Telemetry Submission", False, str(e))
            return False
    
    def test_mqtt_status_message(self):
        """Test 8: Send status message via MQTT"""
        try:
            # Create MQTT client
            client_id = f"e2e_status_test_{uuid.uuid4().hex[:8]}"
            self.mqtt_client = mqtt.Client(client_id)
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Prepare status payload
            status_payload = {
                "device_id": str(self.test_device_id),
                "api_key": self.test_api_key,
                "status": "online",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Publish to status topic
            topic = f"iotflow/devices/{self.test_device_id}/status/online"
            result = self.mqtt_client.publish(topic, json.dumps(status_payload))
            
            # Wait for message to be processed
            time.sleep(2)
            
            # Disconnect
            self.mqtt_client.disconnect()
            
            self.log_test("MQTT Status Message", True, f"Published status to topic: {topic}")
            return True
            
        except Exception as e:
            self.log_test("MQTT Status Message", False, str(e))
            return False
    
    def test_telemetry_retrieval(self):
        """Test 9: Retrieve telemetry data"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            # Get telemetry data
            response = self.session.get(
                f"{self.base_url}/api/v1/devices/telemetry?start_time=-1h&limit=10",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                self.log_test("Telemetry Retrieval", True, f"Retrieved {count} telemetry records")
                return True
            else:
                self.log_test("Telemetry Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Telemetry Retrieval", False, str(e))
            return False
    
    def test_device_status_update(self):
        """Test 10: Check device status and telemetry count"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            response = self.session.get(f"{self.base_url}/api/v1/devices/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                device_info = data.get('device', {})
                telemetry_count = device_info.get('telemetry_count', 0)
                is_online = device_info.get('is_online', False)
                
                self.log_test("Device Status Update", True, 
                            f"Telemetry count: {telemetry_count}, Online: {is_online}")
                return True
            else:
                self.log_test("Device Status Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Device Status Update", False, str(e))
            return False
    
    def test_admin_device_details(self):
        """Test 11: Get device details via admin endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/admin/devices/{self.test_device_id}")
            
            if response.status_code == 200:
                data = response.json()
                device_info = data.get('device', {})
                configurations = data.get('configurations', {})
                
                self.log_test("Admin Device Details", True, 
                            f"Device retrieved with {len(configurations)} configurations")
                return True
            else:
                self.log_test("Admin Device Details", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Device Details", False, str(e))
            return False
    
    def test_influxdb_verification(self):
        """Test 12: Verify data is stored in InfluxDB (via telemetry count)"""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.test_api_key
            }
            
            # Get initial count
            response = self.session.get(f"{self.base_url}/api/v1/devices/status", headers=headers)
            if response.status_code != 200:
                self.log_test("InfluxDB Verification", False, "Failed to get initial status")
                return False
            
            initial_count = response.json().get('device', {}).get('telemetry_count', 0)
            
            # Send one more telemetry point
            telemetry_payload = {
                "data": {
                    "temperature": 25.0,
                    "test_verification": True
                },
                "metadata": {
                    "test_purpose": "influxdb_verification"
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/telemetry",
                headers=headers,
                json=telemetry_payload
            )
            
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("InfluxDB Verification", False, "Failed to send verification telemetry")
                return False
            
            # Wait for processing
            time.sleep(2)
            
            # Check updated count
            response = self.session.get(f"{self.base_url}/api/v1/devices/status", headers=headers)
            if response.status_code != 200:
                self.log_test("InfluxDB Verification", False, "Failed to get updated status")
                return False
            
            final_count = response.json().get('device', {}).get('telemetry_count', 0)
            
            if final_count > initial_count:
                self.log_test("InfluxDB Verification", True, 
                            f"Telemetry count increased: {initial_count} → {final_count}")
                return True
            else:
                self.log_test("InfluxDB Verification", False, 
                            f"Telemetry count unchanged: {initial_count} → {final_count}")
                return False
                
        except Exception as e:
            self.log_test("InfluxDB Verification", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting End-to-End IoT Connectivity Layer Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests in sequence
        tests = [
            self.test_system_health,
            self.test_mqtt_broker_connection,
            self.test_device_registration,
            self.test_device_authentication,
            self.test_device_configuration,
            self.test_rest_telemetry_submission,
            self.test_mqtt_telemetry_submission,
            self.test_mqtt_status_message,
            self.test_telemetry_retrieval,
            self.test_device_status_update,
            self.test_admin_device_details,
            self.test_influxdb_verification
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            if test_func():
                passed_tests += 1
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: ✅ {passed_tests}")
        print(f"Failed: ❌ {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration} seconds")
        
        if self.test_device_id:
            print(f"\nTest Device Created:")
            print(f"  - Device ID: {self.test_device_id}")
            print(f"  - API Key: {self.test_api_key}")
        
        print("\n🎯 End-to-End Test Complete!")
        
        return passed_tests == total_tests


def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    tester = IoTFlowTester(base_url=base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
