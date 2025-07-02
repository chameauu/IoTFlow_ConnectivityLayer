#!/usr/bin/env python3
"""
MQTT Device Simulator for IoTFlow
A device simulator that publishes telemetry data via MQTT
"""

import os
import sys
import time
import json
import random
import signal
import logging
import argparse
import threading
from datetime import datetime
import paho.mqtt.client as mqtt


class MQTTDeviceSimulator:
    def __init__(
        self,
        device_id,
        device_type="sensor",
        host="localhost",
        port=1883,
        username="admin",
        password="admin123",
        qos=1,
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.qos = qos
        self.client_id = f"iotflow-device-{device_id}"
        self.exit_flag = False
        self.connected = False
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        self.logger = logging.getLogger(f"Device-{device_id}")
        
        # Topics
        self.telemetry_topic = f"iotflow/devices/{self.device_id}/telemetry/sensors"
        self.status_topic = f"iotflow/devices/{self.device_id}/status/online"
        self.commands_topic = f"iotflow/devices/{self.device_id}/commands"
        self.config_topic = f"iotflow/devices/{self.device_id}/config"
        
        # Device properties
        self.battery_level = 100.0
        self.start_time = datetime.now()
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
        # Set credentials if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Set last will and testament
        self.client.will_set(
            self.status_topic,
            json.dumps({"status": "offline", "device_id": self.device_id}),
            qos=1,
            retain=True
        )
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to broker"""
        if rc == 0:
            self.logger.info("✅ Connected to MQTT broker successfully")
            self.connected = True
            
            # Subscribe to command topics
            self.client.subscribe(self.commands_topic, qos=self.qos)
            self.client.subscribe(self.config_topic, qos=self.qos)
            
            # Publish online status
            self.publish_status("online")
        else:
            connection_errors = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error_msg = connection_errors.get(rc, f"Unknown error (code: {rc})")
            self.logger.error(f"❌ Failed to connect: {error_msg}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects from broker"""
        self.connected = False
        if rc != 0:
            self.logger.warning("❗ Unexpected disconnection from MQTT broker")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def on_message(self, client, userdata, msg):
        """Callback when client receives a message"""
        try:
            payload = msg.payload.decode('utf-8')
            self.logger.info(f"📩 Message received on {msg.topic}")
            
            try:
                data = json.loads(payload)
                self.logger.info(f"   Payload: {json.dumps(data, indent=2)}")
                
                # Handle command messages
                if msg.topic == self.commands_topic:
                    self.handle_command(data)
                # Handle configuration messages
                elif msg.topic == self.config_topic:
                    self.handle_config(data)
            except json.JSONDecodeError:
                self.logger.warning(f"   Non-JSON payload: {payload}")
        except Exception as e:
            self.logger.error(f"❌ Error processing message: {e}")
    
    def on_publish(self, client, userdata, mid):
        """Callback when client publishes a message"""
        self.logger.debug(f"Message published (ID: {mid})")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.logger.info(f"Connecting to MQTT broker at {self.host}:{self.port}")
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            self.logger.error(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.publish_status("offline")
            time.sleep(1)  # Give time for the message to be sent
        
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_status(self, status):
        """Publish device status"""
        payload = {
            "device_id": self.device_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"📤 Publishing status: {status}")
        self.client.publish(
            self.status_topic,
            json.dumps(payload),
            qos=self.qos,
            retain=True
        )
    
    def publish_telemetry(self, data):
        """Publish telemetry data"""
        if not self.connected:
            self.logger.warning("❌ Cannot publish telemetry: not connected")
            return False
        
        try:
            self.logger.info(f"📤 Publishing telemetry data")
            self.client.publish(
                self.telemetry_topic,
                json.dumps(data),
                qos=self.qos
            )
            return True
        except Exception as e:
            self.logger.error(f"❌ Error publishing telemetry: {e}")
            return False
    
    def generate_telemetry(self):
        """Generate telemetry data based on device type"""
        # Base telemetry data
        telemetry = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update battery level (drain over time)
        runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.battery_level = max(10, 100 - runtime_hours * 0.5)  # 0.5% per hour, min 10%
        
        # Different telemetry based on device type
        if self.device_type == "temperature_sensor":
            # Simulate temperature following daily cycle
            hour = datetime.now().hour
            base_temp = 22 + 5 * (0.5 + 0.5 * (hour - 12) / 12)
            temperature = round(base_temp + random.uniform(-1.5, 1.5), 2)
            
            # Humidity inversely related to temperature
            humidity = round(70 - (temperature - 20) * 2 + random.uniform(-5, 5), 1)
            humidity = max(30, min(90, humidity))
            
            telemetry["measurements"] = {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": round(random.uniform(1010, 1020), 2)
            }
        elif self.device_type == "motion_sensor":
            # Motion detection (10% chance of motion)
            motion_detected = random.random() < 0.1
            
            telemetry["measurements"] = {
                "motion": motion_detected,
                "light_level": round(random.uniform(0, 1000), 1),
                "proximity": round(random.uniform(0, 100), 1) if motion_detected else None
            }
        elif self.device_type == "smart_meter":
            # Energy consumption increases during daytime
            hour = datetime.now().hour
            base_power = 100 + 150 * (1 if 8 <= hour <= 22 else 0.3) 
            
            telemetry["measurements"] = {
                "power": round(base_power + random.uniform(-20, 20), 1),
                "voltage": round(220 + random.uniform(-5, 5), 1),
                "current": round((base_power + random.uniform(-10, 10)) / 220, 3),
                "frequency": round(50 + random.uniform(-0.1, 0.1), 2),
                "total_energy": round(random.uniform(5000, 6000), 1)
            }
        else:
            # Default sensor data
            telemetry["measurements"] = {
                "value": round(random.uniform(0, 100), 2),
                "unit": "units"
            }
        
        # Add status information
        telemetry["status"] = {
            "battery_level": round(self.battery_level, 1),
            "signal_strength": random.randint(-90, -30),
            "uptime": int((datetime.now() - self.start_time).total_seconds())
        }
        
        return telemetry
    
    def handle_command(self, command_data):
        """Handle commands received from the broker"""
        self.logger.info(f"🔧 Processing command: {command_data}")
        
        # Extract command type
        command_type = command_data.get("type")
        if not command_type:
            self.logger.warning("❌ Received command with no type")
            return
        
        # Handle different command types
        if command_type == "reboot":
            self.logger.info("📢 Received reboot command")
            self.publish_status("rebooting")
            time.sleep(2)
            self.publish_status("online")
        
        elif command_type == "update":
            self.logger.info("📢 Received update command")
            self.publish_status("updating")
            time.sleep(3)
            self.publish_status("online")
        
        elif command_type == "configure":
            self.logger.info("📢 Received configure command")
            # Process configuration changes
            if "config" in command_data:
                self.logger.info(f"Updating configuration: {command_data['config']}")
        
        else:
            self.logger.warning(f"❌ Unknown command type: {command_type}")
    
    def handle_config(self, config_data):
        """Handle configuration updates"""
        self.logger.info(f"⚙️ Received configuration update: {config_data}")
    
    def run(self, duration=300, telemetry_interval=5):
        """Run the device simulation"""
        
        # For debugging - log topic names
        self.logger.info(f"Telemetry topic: {self.telemetry_topic}")
        self.logger.info(f"Status topic: {self.status_topic}")
        
        # Connect to the broker
        if not self.connect():
            self.logger.error("❌ Failed to connect to MQTT broker, exiting")
            return False
        
        self.logger.info(f"🚀 Starting device simulation")
        self.logger.info(f"   Device ID: {self.device_id}")
        self.logger.info(f"   Device Type: {self.device_type}")
        self.logger.info(f"   Duration: {duration} seconds")
        self.logger.info(f"   Telemetry Interval: {telemetry_interval} seconds")
        
        # Only set up signal handler in main thread to avoid threading issues
        if threading.current_thread() is threading.main_thread():
            # Set up signal handlers for clean exit
            def signal_handler(sig, frame):
                self.logger.info("🛑 Stopping device simulation...")
                self.exit_flag = True
            
            signal.signal(signal.SIGINT, signal_handler)
        
        # Run simulation loop
        start_time = time.time()
        last_telemetry = 0
        
        try:
            while not self.exit_flag and (time.time() - start_time < duration):
                current_time = time.time()
                
                # Send telemetry data at specified interval
                if current_time - last_telemetry >= telemetry_interval:
                    telemetry_data = self.generate_telemetry()
                    self.publish_telemetry(telemetry_data)
                    last_telemetry = current_time
                
                # Small delay to avoid CPU hogging
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"❌ Error during simulation: {e}")
            return False
        finally:
            # Disconnect cleanly
            self.disconnect()
            
        self.logger.info("✅ Device simulation completed")
        return True


def main():
    """Main function to run the simulator from command line"""
    parser = argparse.ArgumentParser(description='MQTT Device Simulator for IoTFlow')
    parser.add_argument('--id', default=f"device-{random.randint(1000, 9999)}",
                        help='Device ID (default: randomly generated)')
    parser.add_argument('--type', default='temperature_sensor',
                        choices=['temperature_sensor', 'motion_sensor', 'smart_meter', 'generic'],
                        help='Device type')
    parser.add_argument('--host', default='localhost',
                        help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883,
                        help='MQTT broker port')
    parser.add_argument('--username', default='admin',
                        help='MQTT username')
    parser.add_argument('--password', default='admin123',
                        help='MQTT password')
    parser.add_argument('--qos', type=int, default=1, choices=[0, 1, 2],
                        help='MQTT QoS level (0, 1, or 2)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration of simulation in seconds')
    parser.add_argument('--interval', type=int, default=5,
                        help='Telemetry publishing interval in seconds')
    
    args = parser.parse_args()
    
    # Create and run device simulator
    device = MQTTDeviceSimulator(
        device_id=args.id,
        device_type=args.type,
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        qos=args.qos
    )
    
    success = device.run(duration=args.duration, telemetry_interval=args.interval)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
