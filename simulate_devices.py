#!/usr/bin/env python3
"""
IoT Device Simulator for IoTFlow MQTT Integration
Simulates multiple IoT devices connecting to the MQTT broker and sending telemetry data
"""

import json
import time
import random
import threading
import sys
import signal
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import uuid

try:
    import paho.mqtt.client as mqtt
    from src.mqtt.topics import MQTTTopicManager
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install MQTT dependencies with Poetry:")
    print("poetry add paho-mqtt")
    sys.exit(1)


class IoTDevice:
    """Simulates a single IoT device"""
    
    def __init__(self, device_id: str, device_type: str, username: str, password: str):
        self.device_id = device_id
        self.device_type = device_type
        self.username = username
        self.password = password
        
        # MQTT Configuration
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        
        # Device state
        self.is_running = False
        self.is_connected = False
        self.last_telemetry = {}
        
        # Simulation parameters
        self.telemetry_interval = random.uniform(5, 15)  # 5-15 seconds
        self.location = {
            "lat": random.uniform(33.0, 42.0),  # Somewhere in the US
            "lon": random.uniform(-120.0, -80.0),
            "accuracy": random.uniform(1.0, 10.0)
        }
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=f"{device_id}_{uuid.uuid4().hex[:8]}")
        self.client.username_pw_set(username, password)
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        
        # Get device topics
        self.topics = MQTTTopicManager.get_device_topics(device_id)
        
        print(f"🤖 Device {device_id} ({device_type}) initialized")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Called when device connects to MQTT broker"""
        if rc == 0:
            self.is_connected = True
            print(f"✅ Device {self.device_id} connected to MQTT broker")
            
            # Subscribe to command topics
            if 'device_commands_config' in self.topics:
                client.subscribe(self.topics['device_commands_config'])
            if 'device_commands_control' in self.topics:
                client.subscribe(self.topics['device_commands_control'])
            
            # Publish online status
            self._publish_status("online")
            
        else:
            print(f"❌ Device {self.device_id} failed to connect: {mqtt.connack_string(rc)}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Called when device disconnects from MQTT broker"""
        self.is_connected = False
        if rc != 0:
            print(f"⚠️ Device {self.device_id} unexpectedly disconnected")
        else:
            print(f"📴 Device {self.device_id} disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages (commands)"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"📨 Device {self.device_id} received command on {topic}: {payload}")
            
            # Handle different command types
            if 'config' in topic:
                self._handle_config_command(payload)
            elif 'reboot' in topic:
                self._handle_reboot_command(payload)
            
        except Exception as e:
            print(f"❌ Error processing message on {topic}: {e}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Called when subscription is successful"""
        print(f"📡 Device {self.device_id} subscribed to command topics")
    
    def _handle_config_command(self, payload):
        """Handle configuration update commands"""
        if 'interval' in payload:
            self.telemetry_interval = float(payload['interval'])
            print(f"🔧 Device {self.device_id} telemetry interval updated to {self.telemetry_interval}s")
        
        # Send acknowledgment
        ack_payload = {
            "device_id": self.device_id,
            "command": "config_update",
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if 'device_responses_command' in self.topics:
            self.client.publish(self.topics['device_responses_command'], json.dumps(ack_payload))
    
    def _handle_reboot_command(self, payload):
        """Handle reboot commands"""
        print(f"🔄 Device {self.device_id} rebooting...")
        
        # Publish offline status
        self._publish_status("rebooting")
        
        # Simulate reboot delay
        time.sleep(3)
        
        # Publish online status
        self._publish_status("online")
        
        # Send acknowledgment
        ack_payload = {
            "device_id": self.device_id,
            "command": "reboot",
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if 'device_responses_command' in self.topics:
            self.client.publish(self.topics['device_responses_command'], json.dumps(ack_payload))
    
    def _publish_status(self, status: str):
        """Publish device status"""
        status_payload = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": self.location
        }
        
        # Use appropriate status topic
        if status == "online" and 'device_status_online' in self.topics:
            topic = self.topics['device_status_online']
        elif status == "offline" and 'device_status_offline' in self.topics:
            topic = self.topics['device_status_offline']
        elif 'device_status_online' in self.topics:
            topic = self.topics['device_status_online']  # Default
        else:
            return  # No valid topic available
        
        self.client.publish(topic, json.dumps(status_payload), retain=True)
    
    def _generate_telemetry(self) -> Dict[str, Any]:
        """Generate realistic telemetry data based on device type"""
        base_data = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": self.location
        }
        
        if self.device_type == "temperature":
            # Temperature sensor data
            base_temp = 22.0
            variation = random.uniform(-5.0, 8.0)
            base_data.update({
                "temperature": round(base_temp + variation, 2),
                "unit": "celsius",
                "battery_level": random.uniform(75, 100),
                "signal_strength": random.uniform(-80, -30)
            })
            
        elif self.device_type == "humidity":
            # Humidity sensor data
            base_data.update({
                "humidity": round(random.uniform(30, 80), 2),
                "temperature": round(random.uniform(18, 28), 2),
                "unit": "percent",
                "battery_level": random.uniform(65, 100),
                "signal_strength": random.uniform(-85, -25)
            })
            
        elif self.device_type == "pressure":
            # Pressure sensor data
            base_data.update({
                "pressure": round(random.uniform(980, 1020), 2),
                "altitude": round(random.uniform(100, 500), 2),
                "unit": "hPa",
                "battery_level": random.uniform(80, 100),
                "signal_strength": random.uniform(-75, -35)
            })
            
        elif self.device_type == "motion":
            # Motion sensor data
            base_data.update({
                "motion_detected": random.choice([True, False]),
                "confidence": random.uniform(0.7, 1.0),
                "battery_level": random.uniform(60, 100),
                "signal_strength": random.uniform(-70, -40)
            })
            
        elif self.device_type == "gateway":
            # Gateway device data
            base_data.update({
                "cpu_usage": round(random.uniform(10, 60), 2),
                "memory_usage": round(random.uniform(30, 80), 2),
                "disk_usage": round(random.uniform(20, 70), 2),
                "uptime": random.randint(3600, 86400),  # 1 hour to 1 day
                "connected_devices": random.randint(5, 25),
                "network_status": "connected"
            })
            
        else:
            # Generic sensor data
            base_data.update({
                "value": round(random.uniform(0, 100), 2),
                "battery_level": random.uniform(70, 100),
                "signal_strength": random.uniform(-80, -30)
            })
        
        return base_data
    
    def _telemetry_loop(self):
        """Main telemetry publishing loop"""
        while self.is_running:
            if self.is_connected:
                try:
                    # Generate telemetry data
                    telemetry = self._generate_telemetry()
                    self.last_telemetry = telemetry
                    
                    # Determine topic based on device type
                    if self.device_type in ["temperature", "humidity", "pressure", "motion"]:
                        if 'device_telemetry_sensors' in self.topics:
                            topic = self.topics['device_telemetry_sensors']
                        elif 'device_telemetry_data' in self.topics:
                            topic = self.topics['device_telemetry_data']
                        else:
                            print(f"❌ No telemetry topic found for {self.device_id}")
                            continue
                    elif self.device_type == "gateway":
                        if 'device_telemetry_status' in self.topics:
                            topic = self.topics['device_telemetry_status']
                        elif 'device_telemetry_data' in self.topics:
                            topic = self.topics['device_telemetry_data']
                        else:
                            print(f"❌ No telemetry topic found for {self.device_id}")
                            continue
                    else:
                        if 'device_telemetry_data' in self.topics:
                            topic = self.topics['device_telemetry_data']
                        else:
                            print(f"❌ No telemetry topic found for {self.device_id}")
                            continue
                    
                    # Publish telemetry
                    self.client.publish(topic, json.dumps(telemetry))
                    print(f"📊 Device {self.device_id} sent telemetry: {telemetry.get('temperature', telemetry.get('humidity', telemetry.get('motion_detected', 'data')))}")
                    
                except Exception as e:
                    print(f"❌ Error sending telemetry for {self.device_id}: {e}")
            
            time.sleep(self.telemetry_interval)
    
    def start(self):
        """Start the device simulation"""
        try:
            print(f"🚀 Starting device {self.device_id}...")
            
            # Connect to MQTT broker
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Start MQTT loop in background
            self.client.loop_start()
            
            # Set running flag
            self.is_running = True
            
            # Start telemetry thread
            self.telemetry_thread = threading.Thread(target=self._telemetry_loop)
            self.telemetry_thread.daemon = True
            self.telemetry_thread.start()
            
            print(f"✅ Device {self.device_id} started successfully")
            
        except Exception as e:
            print(f"❌ Failed to start device {self.device_id}: {e}")
            return False
        
        return True
    
    def stop(self):
        """Stop the device simulation"""
        print(f"🛑 Stopping device {self.device_id}...")
        
        # Set running flag to False
        self.is_running = False
        
        if self.is_connected:
            # Publish offline status
            self._publish_status("offline")
            
            # Disconnect from broker
            self.client.disconnect()
        
        # Stop MQTT loop
        self.client.loop_stop()
        
        print(f"⏹️ Device {self.device_id} stopped")


class DeviceFleetSimulator:
    """Manages multiple simulated devices"""
    
    def __init__(self):
        self.devices = {}
        self.is_running = False
    
    def add_device(self, device_id: str, device_type: str, username: str, password: str):
        """Add a device to the fleet"""
        device = IoTDevice(device_id, device_type, username, password)
        self.devices[device_id] = device
        return device
    
    def start_all(self):
        """Start all devices in the fleet"""
        print(f"🚀 Starting fleet of {len(self.devices)} devices...")
        
        self.is_running = True
        
        for device in self.devices.values():
            device.start()
            time.sleep(1)  # Stagger starts
        
        print("✅ All devices started")
    
    def stop_all(self):
        """Stop all devices in the fleet"""
        print("🛑 Stopping all devices...")
        
        self.is_running = False
        
        for device in self.devices.values():
            device.stop()
        
        print("⏹️ All devices stopped")
    
    def get_status(self):
        """Get status of all devices"""
        status = {}
        for device_id, device in self.devices.items():
            status[device_id] = {
                "connected": device.is_connected,
                "running": device.is_running,
                "type": device.device_type,
                "last_telemetry": device.last_telemetry
            }
        return status


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Received interrupt signal. Shutting down...")
    global fleet_simulator
    if 'fleet_simulator' in globals():
        fleet_simulator.stop_all()
    sys.exit(0)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="IoT Device Simulator for MQTT")
    parser.add_argument("--device", "-d", required=True, help="Device ID")
    parser.add_argument("--type", "-t", default="temperature", 
                       choices=["temperature", "humidity", "pressure", "motion", "gateway"],
                       help="Device type")
    parser.add_argument("--username", "-u", help="MQTT username (defaults to device ID)")
    parser.add_argument("--password", "-p", help="MQTT password")
    parser.add_argument("--fleet", "-f", action="store_true", help="Run a fleet of devices")
    
    args = parser.parse_args()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    global fleet_simulator
    fleet_simulator = DeviceFleetSimulator()
    
    if args.fleet:
        # Create a fleet of different devices
        devices_config = [
            {"id": "temp_sensor_001", "type": "temperature"},
            {"id": "humid_sensor_001", "type": "humidity"},
            {"id": "pressure_sensor_001", "type": "pressure"},
            {"id": "motion_sensor_001", "type": "motion"},
            {"id": "gateway_001", "type": "gateway"}
        ]
        
        print("🚛 Creating device fleet...")
        
        for config in devices_config:
            username = config["id"]
            password = args.password or "defaultpass123"
            fleet_simulator.add_device(config["id"], config["type"], username, password)
        
        fleet_simulator.start_all()
        
        # Keep running until interrupted
        try:
            while fleet_simulator.is_running:
                time.sleep(10)
                print(f"📊 Fleet status: {len([d for d in fleet_simulator.devices.values() if d.is_connected])}/{len(fleet_simulator.devices)} devices connected")
        except KeyboardInterrupt:
            pass
    
    else:
        # Single device simulation
        username = args.username or args.device
        password = args.password or "defaultpass123"
        
        device = fleet_simulator.add_device(args.device, args.type, username, password)
        
        if device.start():
            try:
                # Keep running until interrupted
                while device.is_running:
                    time.sleep(5)
                    if device.is_connected:
                        print(f"💚 Device {args.device} is running (last telemetry interval: {device.telemetry_interval:.1f}s)")
            except KeyboardInterrupt:
                pass
        
        device.stop()


if __name__ == "__main__":
    main()
