#!/usr/bin/env python3
"""
New Advanced MQTT Device Simulator for IoTFlow
A comprehensive, production-ready device simulator with advanced features
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
import requests
import math
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import paho.mqtt.client as mqtt


class AdvancedMQTTDeviceSimulator:
    """
    Advanced MQTT Device Simulator with comprehensive IoT device behavior
    """
    
    def __init__(
        self,
        device_name: str,
        device_type: str = "smart_sensor",
        host: str = "localhost",
        mqtt_port: int = 1883,
        http_port: int = 5000,
        qos: int = 1,
        simulation_profile: str = "default",
        force_register: bool = False,
        auto_suffix: bool = False
    ):
        self.device_name = device_name
        self.device_type = device_type
        self.host = host
        self.mqtt_port = mqtt_port
        self.http_port = http_port
        self.qos = qos
        self.simulation_profile = simulation_profile
        self.force_register = force_register
        self.auto_suffix = auto_suffix
        self.base_url = f"http://{host}:{http_port}"
        
        # Device registration data
        self.device_id = None
        self.api_key = None
        self.registered = False
        
        # MQTT connection
        self.client_id = f"iotflow-new-{device_name}-{uuid.uuid4().hex[:8]}"
        self.client = None
        self.connected = False
        
        # Control flags
        self.exit_flag = False
        self.simulation_running = False
        
        # Device state
        self.battery_level = 100.0
        self.start_time = datetime.now()
        self.message_count = 0
        self.last_heartbeat = None
        self.last_telemetry = None
        self.device_status = "initializing"
        
        # Simulation parameters
        self.telemetry_interval = 5  # seconds
        self.heartbeat_interval = 60  # seconds
        self.error_rate = 0.02  # 2% error rate
        self.network_jitter = True
        
        # Setup logging
        self._setup_logging()
        
        # Load simulation profile
        self._load_simulation_profile()
        
        # Initialize MQTT topics
        self._setup_mqtt_topics()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Configure logging for the device simulator"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'logs/device_{self.device_name}.log', mode='a')
            ]
        )
        self.logger = logging.getLogger(f"NewMQTT-{self.device_name}")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
    
    def _load_simulation_profile(self):
        """Load simulation profile configurations"""
        profiles = {
            "default": {
                "telemetry_types": ["temperature", "humidity", "pressure", "battery"],
                "telemetry_interval": 5,
                "heartbeat_interval": 60,
                "error_rate": 0.02,
                "battery_drain_rate": 0.1  # % per hour
            },
            "high_frequency": {
                "telemetry_types": ["temperature", "humidity", "pressure", "accelerometer", "gyroscope"],
                "telemetry_interval": 5,
                "heartbeat_interval": 30,
                "error_rate": 0.01,
                "battery_drain_rate": 0.5
            },
            "energy_efficient": {
                "telemetry_types": ["temperature", "battery"],
                "telemetry_interval": 300,  # 5 minutes
                "heartbeat_interval": 600,  # 10 minutes
                "error_rate": 0.001,
                "battery_drain_rate": 0.05
            },
            "industrial": {
                "telemetry_types": ["temperature", "pressure", "vibration", "power_consumption"],
                "telemetry_interval": 10,
                "heartbeat_interval": 30,
                "error_rate": 0.005,
                "battery_drain_rate": 0.3
            }
        }
        
        profile = profiles.get(self.simulation_profile, profiles["default"])
        
        self.telemetry_types = profile["telemetry_types"]
        self.telemetry_interval = profile["telemetry_interval"]
        self.heartbeat_interval = profile["heartbeat_interval"]
        self.error_rate = profile["error_rate"]
        self.battery_drain_rate = profile["battery_drain_rate"]
        
        self.logger.info(f"🔧 Loaded simulation profile: {self.simulation_profile}")
        self.logger.info(f"   Telemetry types: {', '.join(self.telemetry_types)}")
        self.logger.info(f"   Intervals: telemetry={self.telemetry_interval}s, heartbeat={self.heartbeat_interval}s")
    
    def _setup_mqtt_topics(self):
        """Setup MQTT topic structure"""
        self.topics = {
            "telemetry": f"devices/{self.device_name}/telemetry",
            "heartbeat": f"devices/{self.device_name}/heartbeat",
            "status": f"devices/{self.device_name}/status",
            "commands": f"devices/{self.device_name}/commands",
            "config": f"devices/{self.device_name}/config",
            "errors": f"devices/{self.device_name}/errors"
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.exit_flag = True
        self.simulation_running = False
    
    def register_device(self) -> bool:
        """Register the device with the IoTFlow server or retrieve existing credentials"""
        self.logger.info(f"🔗 Checking device registration: {self.device_name}")
        
        # If force registration is requested, skip checking existing device
        if self.force_register:
            self.logger.info("🔄 Force registration requested, skipping existing device check")
            return self._register_new_device()
        
        # Check if device already exists
        if self._check_existing_device():
            return True
        
        # If auto-suffix is enabled and device exists, try with suffix
        if self.auto_suffix and self._device_name_exists():
            original_name = self.device_name
            suffix = 1
            while self._device_name_exists():
                self.device_name = f"{original_name}_{suffix}"
                suffix += 1
                if suffix > 100:  # Prevent infinite loop
                    self.logger.error("❌ Too many devices with similar names")
                    return False
            
            self.logger.info(f"🔄 Using device name: {self.device_name}")
            # Update topics with new name
            self._setup_mqtt_topics()
        
        # Register the device (with potentially modified name)
        return self._register_new_device()
    
    def _check_existing_device(self) -> bool:
        """Check if device already exists and provide guidance"""
        try:
            # Try to get device info by name using admin endpoint
            response = requests.get(
                f"{self.base_url}/api/v1/admin/devices",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                devices = devices_data.get('devices', []) if isinstance(devices_data, dict) else devices_data
                
                # Look for our device by name
                for device in devices:
                    if device.get('name') == self.device_name:
                        device_id = device.get('id')
                        
                        self.logger.warning(f"⚠️ Device '{self.device_name}' already exists (ID: {device_id})")
                        self.logger.info(f"   Status: {device.get('status', 'unknown')}")
                        self.logger.info(f"   Created: {device.get('created_at', 'unknown')}")
                        self.logger.info(f"   Type: {device.get('device_type', 'unknown')}")
                        
                        # Since admin endpoint doesn't return API keys, suggest solutions
                        self.logger.info(f"💡 To continue testing with this device:")
                        self.logger.info(f"   1. Use a different device name: --name {self.device_name}_new")
                        self.logger.info(f"   2. Or use --force-register to attempt re-registration")
                        self.logger.info(f"   3. Or delete the existing device from the admin panel")
                        
                        return False  # Cannot proceed without API key
                
                # Device not found - safe to register
                self.logger.debug(f"📋 Device '{self.device_name}' not found in {len(devices)} registered devices")
                return False
            else:
                self.logger.debug(f"⚠️ Could not check existing devices: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"⚠️ Could not check existing devices: {e}")
            return False
    
    def _device_name_exists(self) -> bool:
        """Check if device name already exists (simplified check)"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/admin/devices",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                devices = devices_data.get('devices', []) if isinstance(devices_data, dict) else devices_data
                
                # Check if any device has this name
                for device in devices:
                    if device.get('name') == self.device_name:
                        return True
                return False
            else:
                return False
                
        except requests.exceptions.RequestException:
            return False
    
    def _register_new_device(self) -> bool:
        """Register a new device with the IoTFlow server"""
        self.logger.info(f"📝 Registering new device: {self.device_name}")
        
        device_data = {
            "name": self.device_name,
            "description": f"New advanced MQTT {self.device_type} simulator",
            "device_type": self.device_type,
            "location": "Advanced Simulation Environment",
            "firmware_version": "2.1.0",
            "hardware_version": "new-mqtt-sim-v2.1",
            "capabilities": self.telemetry_types + [
                "mqtt_communication",
                "command_handling",
                "status_reporting",
                "error_reporting"
            ],
            "metadata": {
                "simulation": True,
                "protocol": "mqtt",
                "profile": self.simulation_profile,
                "registration_time": datetime.now().isoformat(),
                "simulator_version": "2.1.0"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/devices/register",
                json=device_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.device_id = data['device']['id']
                self.api_key = data['device']['api_key']
                self.registered = True
                self.device_status = "registered"
                
                self.logger.info(f"✅ Device registered successfully!")
                self.logger.info(f"   Device ID: {self.device_id}")
                self.logger.info(f"   API Key: {self.api_key[:8]}...")
                return True
            elif response.status_code == 409:
                # Device name already exists - provide helpful guidance
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                
                self.logger.error(f"❌ Device name '{self.device_name}' already exists")
                self.logger.info(f"💡 Solutions:")
                self.logger.info(f"   1. Use a different name: --name {self.device_name}_v2")
                self.logger.info(f"   2. Use --force-register (may cause issues)")
                self.logger.info(f"   3. Delete existing device from admin panel")
                self.logger.info(f"   4. Use auto-generated name (remove --name argument)")
                return False
            else:
                error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                self.logger.error(f"❌ Registration failed: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Registration error: {e}")
            return False
    
    def _setup_mqtt_client(self):
        """Initialize and configure MQTT client"""
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        
        # Set authentication
        if self.device_id and self.api_key:
            self.client.username_pw_set(str(self.device_id), self.api_key)
        
        # Configure connection options
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            self.device_status = "connected"
            self.logger.info(f"🔌 Connected to MQTT broker at {self.host}:{self.mqtt_port}")
            
            # Subscribe to command and config topics
            client.subscribe(self.topics["commands"], qos=self.qos)
            client.subscribe(self.topics["config"], qos=self.qos)
            
            # Send initial status
            self._publish_status("online")
            
        else:
            self.connected = False
            self.device_status = "connection_failed"
            error_messages = {
                1: "incorrect protocol version",
                2: "invalid client identifier",
                3: "server unavailable",
                4: "bad username or password",
                5: "not authorized"
            }
            error_msg = error_messages.get(rc, f"unknown error {rc}")
            self.logger.error(f"❌ MQTT connection failed: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        self.device_status = "disconnected"
        if rc != 0:
            self.logger.warning(f"📡 Unexpected MQTT disconnection (code: {rc})")
        else:
            self.logger.info("📴 MQTT disconnected")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            self.logger.info(f"📨 Received message on {topic}")
            
            if topic == self.topics["commands"]:
                self._handle_command(payload)
            elif topic == self.topics["config"]:
                self._handle_config_update(payload)
            else:
                self.logger.debug(f"🔍 Unhandled topic: {topic}")
                
        except json.JSONDecodeError:
            self.logger.error(f"❌ Invalid JSON in message: {msg.payload}")
        except Exception as e:
            self.logger.error(f"❌ Error processing message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful message publish"""
        self.logger.debug(f"📤 Message {mid} published successfully")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for successful subscription"""
        self.logger.debug(f"📥 Subscribed with QoS {granted_qos}")
    
    def _handle_command(self, command: Dict[str, Any]):
        """Handle device commands"""
        command_type = command.get("type")
        command_id = command.get("id", "unknown")
        
        self.logger.info(f"🎯 Processing command: {command_type} (ID: {command_id})")
        
        response = {
            "command_id": command_id,
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        try:
            if command_type == "restart":
                self.logger.info("🔄 Simulating device restart...")
                response["message"] = "Device restart initiated"
                
            elif command_type == "update_interval":
                new_interval = command.get("interval", 30)
                self.telemetry_interval = new_interval
                response["message"] = f"Telemetry interval updated to {new_interval}s"
                self.logger.info(f"⏱️ Telemetry interval changed to {new_interval}s")
                
            elif command_type == "get_status":
                response["device_status"] = self._get_device_status()
                response["message"] = "Status retrieved"
                
            elif command_type == "calibrate":
                self.logger.info("🎛️ Simulating sensor calibration...")
                time.sleep(2)  # Simulate calibration time
                response["message"] = "Calibration completed"
                
            else:
                response["status"] = "error"
                response["message"] = f"Unknown command: {command_type}"
                self.logger.warning(f"❓ Unknown command received: {command_type}")
            
            # Send command response
            self._publish_message("status", response)
            
        except Exception as e:
            response["status"] = "error"
            response["message"] = f"Command execution failed: {str(e)}"
            self.logger.error(f"❌ Command execution error: {e}")
            self._publish_message("status", response)
    
    def _handle_config_update(self, config: Dict[str, Any]):
        """Handle configuration updates"""
        self.logger.info(f"⚙️ Received configuration update")
        
        try:
            if "telemetry_interval" in config:
                self.telemetry_interval = config["telemetry_interval"]
                self.logger.info(f"📊 Telemetry interval updated to {self.telemetry_interval}s")
            
            if "heartbeat_interval" in config:
                self.heartbeat_interval = config["heartbeat_interval"]
                self.logger.info(f"💓 Heartbeat interval updated to {self.heartbeat_interval}s")
            
            if "error_rate" in config:
                self.error_rate = config["error_rate"]
                self.logger.info(f"⚠️ Error rate updated to {self.error_rate}")
            
            # Send acknowledgment
            ack = {
                "type": "config_ack",
                "device_id": self.device_id,
                "timestamp": datetime.now().isoformat(),
                "applied_config": config
            }
            self._publish_message("status", ack)
            
        except Exception as e:
            self.logger.error(f"❌ Configuration update error: {e}")
    
    def _generate_telemetry_data(self) -> Dict[str, Any]:
        """Generate realistic telemetry data based on device type and profile"""
        data = {
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "message_id": self.message_count
        }
        
        # Generate data for each telemetry type
        for telemetry_type in self.telemetry_types:
            if telemetry_type == "temperature":
                # Realistic temperature with daily cycle
                hour = datetime.now().hour
                base_temp = 22 + 8 * math.sin((hour - 6) * math.pi / 12)
                data["temperature"] = round(base_temp + random.uniform(-2, 2), 2)
                
            elif telemetry_type == "humidity":
                # Humidity inversely related to temperature
                temp = data.get("temperature", 25)
                base_humidity = 70 - (temp - 20) * 2
                data["humidity"] = round(max(30, min(90, base_humidity + random.uniform(-5, 5))), 1)
                
            elif telemetry_type == "pressure":
                data["pressure"] = round(random.uniform(1010, 1020), 2)
                
            elif telemetry_type == "battery":
                # Simulate battery drain
                runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                self.battery_level = max(0, 100 - runtime_hours * self.battery_drain_rate)
                data["battery_level"] = round(self.battery_level, 1)
                
            elif telemetry_type == "accelerometer":
                data["accelerometer"] = {
                    "x": round(random.uniform(-2, 2), 3),
                    "y": round(random.uniform(-2, 2), 3),
                    "z": round(random.uniform(8, 12), 3)  # Gravity
                }
                
            elif telemetry_type == "gyroscope":
                data["gyroscope"] = {
                    "x": round(random.uniform(-0.5, 0.5), 3),
                    "y": round(random.uniform(-0.5, 0.5), 3),
                    "z": round(random.uniform(-0.5, 0.5), 3)
                }
                
            elif telemetry_type == "vibration":
                data["vibration"] = round(random.uniform(0, 10), 2)
                
            elif telemetry_type == "power_consumption":
                data["power_consumption"] = round(random.uniform(0.5, 5.0), 2)
        
        # Add signal quality
        data["signal_strength"] = random.randint(-80, -40)
        data["signal_quality"] = random.randint(60, 100)
        
        return data
    
    def _generate_heartbeat_data(self) -> Dict[str, Any]:
        """Generate heartbeat data"""
        return {
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "status": self.device_status,
            "uptime": int((datetime.now() - self.start_time).total_seconds()),
            "message_count": self.message_count,
            "battery_level": round(self.battery_level, 1),
            "memory_usage": random.randint(40, 80),
            "cpu_usage": random.randint(10, 50)
        }
    
    def _get_device_status(self) -> Dict[str, Any]:
        """Get comprehensive device status"""
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "status": self.device_status,
            "connected": self.connected,
            "uptime": int((datetime.now() - self.start_time).total_seconds()),
            "message_count": self.message_count,
            "battery_level": round(self.battery_level, 1),
            "simulation_profile": self.simulation_profile,
            "telemetry_interval": self.telemetry_interval,
            "heartbeat_interval": self.heartbeat_interval,
            "last_telemetry": self.last_telemetry.isoformat() if self.last_telemetry else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    def _publish_message(self, topic_type: str, data: Dict[str, Any]) -> bool:
        """Publish message to MQTT broker"""
        if not self.connected:
            self.logger.warning("📡 Cannot publish - not connected to MQTT broker")
            return False
        
        try:
            topic = self.topics.get(topic_type)
            if not topic:
                self.logger.error(f"❌ Unknown topic type: {topic_type}")
                return False
            
            # Simulate network errors
            if random.random() < self.error_rate:
                self.logger.warning(f"📡 Simulated network error for {topic_type}")
                return False
            
            # Add network jitter
            if self.network_jitter:
                time.sleep(random.uniform(0, 0.1))
            
            # Publish message
            result = self.client.publish(topic, json.dumps(data), qos=self.qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"📤 Published {topic_type} to {topic}")
                return True
            else:
                self.logger.error(f"❌ Failed to publish {topic_type}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Publish error: {e}")
            return False
    
    def _publish_status(self, status: str):
        """Publish device status"""
        status_data = {
            "device_id": self.device_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self._publish_message("status", status_data)
    
    def connect_mqtt(self) -> bool:
        """Connect to MQTT broker"""
        if not self.registered:
            self.logger.error("❌ Device must be registered before connecting to MQTT")
            return False
        
        try:
            self._setup_mqtt_client()
            self.logger.info(f"🔌 Connecting to MQTT broker at {self.host}:{self.mqtt_port}")
            self.client.connect(self.host, self.mqtt_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if self.connected:
                self.logger.info("✅ MQTT connection established")
                return True
            else:
                self.logger.error("❌ MQTT connection timeout")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ MQTT connection error: {e}")
            return False
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self._publish_status("offline")
            time.sleep(0.5)  # Allow status message to be sent
            
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            
        self.connected = False
        self.logger.info("📴 Disconnected from MQTT broker")
    
    def run_simulation(self, duration: int = 300):
        """Run the complete device simulation"""
        self.logger.info(f"🚀 Starting advanced MQTT device simulation")
        self.logger.info(f"   Device: {self.device_name} ({self.device_type})")
        self.logger.info(f"   Profile: {self.simulation_profile}")
        self.logger.info(f"   Duration: {duration} seconds")
        self.logger.info(f"   Telemetry interval: {self.telemetry_interval}s")
        self.logger.info(f"   Heartbeat interval: {self.heartbeat_interval}s")
        
        # Step 1: Register device
        if not self.register_device():
            self.logger.error("❌ Device registration failed. Exiting.")
            return False
        
        # Step 2: Connect to MQTT
        if not self.connect_mqtt():
            self.logger.error("❌ MQTT connection failed. Exiting.")
            return False
        
        # Step 3: Run simulation loop
        self.simulation_running = True
        start_time = time.time()
        last_telemetry = 0
        last_heartbeat = 0
        
        try:
            while self.simulation_running and not self.exit_flag:
                current_time = time.time()
                
                # Check if simulation duration exceeded
                if duration > 0 and (current_time - start_time) >= duration:
                    self.logger.info(f"⏰ Simulation duration ({duration}s) completed")
                    break
                
                # Send heartbeat
                if current_time - last_heartbeat >= self.heartbeat_interval:
                    heartbeat_data = self._generate_heartbeat_data()
                    if self._publish_message("heartbeat", heartbeat_data):
                        self.last_heartbeat = datetime.now()
                        self.logger.info(f"💓 Heartbeat sent - Uptime: {heartbeat_data['uptime']}s")
                    last_heartbeat = current_time
                
                # Send telemetry
                if current_time - last_telemetry >= self.telemetry_interval:
                    telemetry_data = self._generate_telemetry_data()
                    if self._publish_message("telemetry", telemetry_data):
                        self.message_count += 1
                        self.last_telemetry = datetime.now()
                        
                        # Log key metrics
                        temp = telemetry_data.get("temperature", "N/A")
                        battery = telemetry_data.get("battery_level", "N/A")
                        self.logger.info(f"📊 Telemetry sent - Temp: {temp}°C, Battery: {battery}%")
                    
                    last_telemetry = current_time
                
                # Check connection health
                if not self.connected:
                    self.logger.warning("📡 MQTT connection lost, attempting reconnection...")
                    if not self.connect_mqtt():
                        self.logger.error("❌ Reconnection failed, waiting before retry...")
                        time.sleep(5)
                
                time.sleep(1)  # Main loop interval
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Simulation interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Simulation error: {e}")
        finally:
            self.simulation_running = False
            self.disconnect_mqtt()
        
        self.logger.info(f"✅ Simulation completed for device {self.device_name}")
        self.logger.info(f"   Total messages sent: {self.message_count}")
        self.logger.info(f"   Final battery level: {self.battery_level:.1f}%")
        
        return True


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Advanced MQTT Device Simulator for IoTFlow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python new_mqtt_device_simulator.py --name MyDevice

  # High-frequency sensor
  python new_mqtt_device_simulator.py --name HighFreqSensor --profile high_frequency --duration 600

  # Industrial device
  python new_mqtt_device_simulator.py --name IndustrialSensor --type industrial_sensor --profile industrial

  # Energy-efficient device
  python new_mqtt_device_simulator.py --name LowPowerSensor --profile energy_efficient --duration 3600
        """
    )
    
    parser.add_argument('--name', 
                       default=f"NewDevice_{random.randint(1000, 9999)}", 
                       help='Device name (default: auto-generated)')
    
    parser.add_argument('--type', 
                       default='smart_sensor',
                       choices=['smart_sensor', 'industrial_sensor', 'environmental_sensor', 'motion_sensor', 'energy_meter'],
                       help='Device type (default: smart_sensor)')
    
    parser.add_argument('--profile', 
                       default='default',
                       choices=['default', 'high_frequency', 'energy_efficient', 'industrial'],
                       help='Simulation profile (default: default)')
    
    parser.add_argument('--host', 
                       default='localhost',
                       help='MQTT broker host (default: localhost)')
    
    parser.add_argument('--mqtt-port', 
                       type=int, default=1883,
                       help='MQTT broker port (default: 1883)')
    
    parser.add_argument('--http-port', 
                       type=int, default=5000,
                       help='HTTP API port (default: 5000)')
    
    parser.add_argument('--duration', 
                       type=int, default=300,
                       help='Simulation duration in seconds (default: 300, 0 = infinite)')
    
    parser.add_argument('--qos', 
                       type=int, default=1, choices=[0, 1, 2],
                       help='MQTT QoS level (default: 1)')
    
    parser.add_argument('--log-level', 
                       default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    parser.add_argument('--force-register', 
                       action='store_true',
                       help='Force re-registration even if device already exists')
    
    parser.add_argument('--auto-suffix', 
                       action='store_true',
                       help='Automatically add suffix to device name if it already exists')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check if IoTFlow service is available
    try:
        response = requests.get(f"http://{args.host}:{args.http_port}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ IoTFlow service is not responding correctly at {args.host}:{args.http_port}")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to IoTFlow service at {args.host}:{args.http_port}")
        print(f"   Error: {e}")
        print("   Make sure the service is running: poetry run python app.py")
        return 1
    
    # Create and run simulator
    simulator = AdvancedMQTTDeviceSimulator(
        device_name=args.name,
        device_type=args.type,
        host=args.host,
        mqtt_port=args.mqtt_port,
        http_port=args.http_port,
        qos=args.qos,
        simulation_profile=args.profile,
        force_register=args.force_register,
        auto_suffix=args.auto_suffix
    )
    
    success = simulator.run_simulation(args.duration)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
