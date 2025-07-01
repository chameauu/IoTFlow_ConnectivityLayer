#!/usr/bin/env python3
"""
Comprehensive IoTFlow system test with MQTT and InfluxDB integration.
Tests end-to-end data flow: device → MQTT → server → InfluxDB.
"""

import paho.mqtt.client as mqtt
import requests
import json
import time
import threading
import sys
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

# Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "device_001"
MQTT_PASSWORD = "device_001_password"
HTTP_BASE_URL = "http://localhost:5000"
HTTP_API_KEY = "your-api-key-here"

# Test device configuration
TEST_DEVICES = [
    {
        "id": "esp32_001",
        "name": "ESP32 Temperature Sensor",
        "type": "environmental",
        "location": "office"
    },
    {
        "id": "esp32_002", 
        "name": "ESP32 Motion Detector",
        "type": "security",
        "location": "hallway"
    },
    {
        "id": "esp32_003",
        "name": "ESP32 Air Quality Monitor",
        "type": "environmental",
        "location": "living_room"
    }
]

class MQTTTelemetrySimulator:
    """Simulates IoT devices sending telemetry via MQTT"""
    
    def __init__(self, device_config: Dict[str, str]):
        self.device_config = device_config
        self.device_id = device_config["id"]
        self.client = None
        self.connected = False
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT device {self.device_id} connected successfully")
            
            # Subscribe to command topic
            command_topic = f"iotflow/devices/{self.device_id}/commands/+"
            client.subscribe(command_topic, qos=1)
            print(f"📡 Subscribed to commands: {command_topic}")
        else:
            print(f"❌ MQTT device {self.device_id} connection failed: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        print(f"🔌 MQTT device {self.device_id} disconnected")
    
    def on_message(self, client, userdata, msg):
        """MQTT message callback for commands"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"📨 Device {self.device_id} received command: {topic} -> {payload}")
            
            # Send command response
            response_topic = f"iotflow/devices/{self.device_id}/status/command_response"
            response = {
                "command_id": payload.get("command_id", "unknown"),
                "status": "executed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response": "Command executed successfully"
            }
            client.publish(response_topic, json.dumps(response), qos=1)
            
        except Exception as e:
            print(f"❌ Error processing command for {self.device_id}: {e}")
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id=f"simulator_{self.device_id}")
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Connect
            self.client.connect(MQTT_HOST, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            return self.connected
            
        except Exception as e:
            print(f"❌ MQTT connection error for {self.device_id}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
    
    def generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate realistic telemetry data based on device type"""
        base_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": self.device_id,
            "battery_level": random.uniform(60, 100),
            "signal_strength": random.randint(-80, -30)
        }
        
        device_type = self.device_config["type"]
        
        if device_type == "environmental":
            base_data.update({
                "temperature": random.uniform(18, 28),
                "humidity": random.uniform(30, 70),
                "pressure": random.uniform(1000, 1025),
                "air_quality_index": random.randint(10, 150)
            })
        elif device_type == "security":
            base_data.update({
                "motion_detected": random.choice([True, False]),
                "detection_confidence": random.uniform(0.7, 1.0),
                "ambient_light": random.randint(0, 1000)
            })
        
        return base_data
    
    def send_telemetry(self):
        """Send telemetry data via MQTT"""
        if not self.connected:
            return False
        
        try:
            # Generate telemetry data
            telemetry_data = self.generate_telemetry_data()
            
            # Send to different measurement topics
            topics = [
                f"iotflow/devices/{self.device_id}/telemetry/sensor_data",
                f"iotflow/devices/{self.device_id}/telemetry/status"
            ]
            
            for topic in topics:
                payload = json.dumps(telemetry_data)
                result = self.client.publish(topic, payload, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"📊 Device {self.device_id} sent telemetry to {topic}")
                else:
                    print(f"❌ Failed to send telemetry from {self.device_id}: {result.rc}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending telemetry from {self.device_id}: {e}")
            return False
    
    def send_status_update(self):
        """Send device status update"""
        if not self.connected:
            return False
        
        try:
            status_data = {
                "device_id": self.device_id,
                "status": "online",
                "uptime": random.randint(3600, 86400),
                "memory_usage": random.uniform(20, 80),
                "cpu_usage": random.uniform(10, 50),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            topic = f"iotflow/devices/{self.device_id}/status/heartbeat"
            payload = json.dumps(status_data)
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"💓 Device {self.device_id} sent heartbeat")
                return True
            else:
                print(f"❌ Failed to send heartbeat from {self.device_id}: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending status from {self.device_id}: {e}")
            return False
    
    def run_simulation(self, duration: int = 60, interval: int = 5):
        """Run telemetry simulation for specified duration"""
        print(f"🚀 Starting telemetry simulation for {self.device_id} (duration: {duration}s)")
        
        self.running = True
        start_time = time.time()
        last_telemetry = 0
        last_status = 0
        
        while self.running and (time.time() - start_time) < duration:
            current_time = time.time()
            
            # Send telemetry data
            if current_time - last_telemetry >= interval:
                self.send_telemetry()
                last_telemetry = current_time
            
            # Send status update (less frequent)
            if current_time - last_status >= (interval * 3):
                self.send_status_update()
                last_status = current_time
            
            time.sleep(1)
        
        print(f"🏁 Simulation completed for {self.device_id}")


class HTTPTelemetrySimulator:
    """Simulates devices sending telemetry via HTTP API"""
    
    def __init__(self, device_config: Dict[str, str]):
        self.device_config = device_config
        self.device_id = device_config["id"]
        self.api_key = None
        self.registered = False
    
    def register_device(self) -> bool:
        """Register device via HTTP API"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": HTTP_API_KEY
        }
        
        device_data = {
            "name": self.device_config["name"],
            "device_type": self.device_config["type"],
            "description": f"HTTP test device: {self.device_id}",
            "location": self.device_config["location"]
        }
        
        try:
            response = requests.post(
                f"{HTTP_BASE_URL}/api/v1/devices/register",
                headers=headers,
                json=device_data
            )
            
            if response.status_code == 201:
                result = response.json()
                self.api_key = result.get("device", {}).get("api_key")
                self.registered = True
                print(f"✅ HTTP device {self.device_id} registered successfully")
                return True
            elif response.status_code == 409:
                # Device already exists
                print(f"ℹ️ HTTP device {self.device_id} already registered")
                self.api_key = HTTP_API_KEY  # Use default API key
                self.registered = True
                return True
            else:
                print(f"❌ HTTP device registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ HTTP device registration error: {e}")
            return False
    
    def send_telemetry(self) -> bool:
        """Send telemetry via HTTP API"""
        if not self.registered:
            return False
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key or HTTP_API_KEY
        }
        
        # Generate telemetry data
        telemetry_data = {
            "temperature": random.uniform(20, 30),
            "humidity": random.uniform(40, 80),
            "pressure": random.uniform(1005, 1020),
            "battery_level": random.uniform(70, 100)
        }
        
        payload = {
            "data": telemetry_data,
            "type": "sensor_reading",
            "metadata": {
                "location": self.device_config["location"],
                "transmission_method": "http"
            }
        }
        
        try:
            response = requests.post(
                f"{HTTP_BASE_URL}/api/v1/devices/telemetry",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 201:
                print(f"📊 HTTP device {self.device_id} sent telemetry successfully")
                return True
            else:
                print(f"❌ HTTP telemetry failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ HTTP telemetry error: {e}")
            return False


def test_system_health():
    """Test overall system health"""
    print("🏥 Testing system health...")
    
    try:
        # Test main health endpoint
        response = requests.get(f"{HTTP_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Main system health OK")
        else:
            print(f"❌ Main system health failed: {response.status_code}")
            return False
        
        # Test MQTT health
        headers = {"X-API-Key": HTTP_API_KEY}
        response = requests.get(f"{HTTP_BASE_URL}/api/v1/mqtt/status", headers=headers)
        if response.status_code == 200:
            mqtt_status = response.json()
            print(f"✅ MQTT status: {mqtt_status.get('connected', 'unknown')}")
        else:
            print(f"⚠️ MQTT status check failed: {response.status_code}")
        
        # Test InfluxDB health
        response = requests.get(f"{HTTP_BASE_URL}/api/v1/influxdb/health", headers=headers)
        if response.status_code == 200:
            influx_status = response.json()
            print(f"✅ InfluxDB status: {influx_status.get('influxdb', {}).get('status', 'unknown')}")
        else:
            print(f"⚠️ InfluxDB status check failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ System health check error: {e}")
        return False


def query_telemetry_data():
    """Query and display telemetry data from InfluxDB"""
    print("🔍 Querying telemetry data from InfluxDB...")
    
    headers = {"X-API-Key": HTTP_API_KEY}
    
    for device in TEST_DEVICES:
        device_id = device["id"]
        
        try:
            # Query recent data
            response = requests.get(
                f"{HTTP_BASE_URL}/api/v1/influxdb/device/{device_id}/data",
                headers=headers,
                params={"start": "-10m", "stop": "now()"}
            )
            
            if response.status_code == 200:
                result = response.json()
                count = result.get("count", 0)
                print(f"📊 Device {device_id}: {count} data points found")
                
                # Show sample data point
                if result.get("data_points"):
                    sample = result["data_points"][0]
                    print(f"   Sample: {sample.get('field')}={sample.get('value')} at {sample.get('time')}")
            else:
                print(f"⚠️ Query failed for {device_id}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Query error for {device_id}: {e}")
    
    print()


def main():
    """Run comprehensive IoTFlow integration test"""
    print("🚀 Starting Comprehensive IoTFlow Integration Test")
    print("=" * 60)
    
    # Test system health first
    if not test_system_health():
        print("❌ System health check failed. Exiting.")
        return 1
    
    print(f"\n{'-' * 40}")
    print("🔄 Starting MQTT telemetry simulation...")
    
    # Create MQTT simulators
    mqtt_simulators = []
    mqtt_threads = []
    
    for device in TEST_DEVICES[:2]:  # Use first 2 devices for MQTT
        simulator = MQTTTelemetrySimulator(device)
        if simulator.connect():
            mqtt_simulators.append(simulator)
            
            # Start simulation in thread
            thread = threading.Thread(
                target=simulator.run_simulation,
                args=(30, 3),  # 30 seconds, 3 second interval
                daemon=True
            )
            thread.start()
            mqtt_threads.append(thread)
        else:
            print(f"❌ Failed to connect MQTT simulator for {device['id']}")
    
    print(f"\n{'-' * 40}")
    print("🌐 Starting HTTP telemetry simulation...")
    
    # Create HTTP simulator
    http_simulator = HTTPTelemetrySimulator(TEST_DEVICES[2])  # Use last device for HTTP
    if http_simulator.register_device():
        # Send HTTP telemetry periodically
        for i in range(10):  # Send 10 telemetry messages
            http_simulator.send_telemetry()
            time.sleep(2)
    
    print(f"\n{'-' * 40}")
    print("⏳ Waiting for MQTT simulations to complete...")
    
    # Wait for MQTT threads to complete
    for thread in mqtt_threads:
        thread.join()
    
    # Disconnect MQTT simulators
    for simulator in mqtt_simulators:
        simulator.disconnect()
    
    print(f"\n{'-' * 40}")
    print("🔍 Analyzing results...")
    
    # Wait a bit for data to be processed
    time.sleep(5)
    
    # Query and display results
    query_telemetry_data()
    
    print("=" * 60)
    print("🎉 Comprehensive integration test completed!")
    print("Check InfluxDB and server logs for detailed information.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
