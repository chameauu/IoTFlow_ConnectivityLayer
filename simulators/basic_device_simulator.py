#!/usr/bin/env python3
"""
Basic IoT Device Simulator
A simple Python script that acts as an IoT device
"""

import requests
import json
import time
import random
import math
from datetime import datetime, timedelta
import argparse
import logging

class BasicIoTDevice:
    def __init__(self, device_name, device_type="sensor", base_url="http://localhost:5000"):
        self.device_name = device_name
        self.device_type = device_type
        self.base_url = base_url
        self.api_key = None
        self.device_id = None
        self.is_running = False
        self.battery_level = 100.0
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"Device-{device_name}")
    
    def register_device(self):
        """Register the device with the connectivity layer"""
        self.logger.info(f"🔗 Registering device: {self.device_name}")
        
        device_data = {
            "name": self.device_name,
            "description": f"Simulated {self.device_type} device",
            "device_type": self.device_type,
            "location": "Simulation Environment",
            "firmware_version": "1.0.0",
            "hardware_version": "sim-v1.0"
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
                self.api_key = data['device']['api_key']
                self.device_id = data['device']['id']
                self.logger.info(f"✅ Device registered successfully!")
                self.logger.info(f"   Device ID: {self.device_id}")
                self.logger.info(f"   API Key: {self.api_key[:8]}...")
                return True
            else:
                self.logger.error(f"❌ Registration failed: {response.json()}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to keep device online"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/devices/heartbeat",
                headers={"X-API-Key": self.api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.debug("💓 Heartbeat sent")
                return True
            else:
                self.logger.warning(f"❌ Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Heartbeat error: {e}")
            return False
    
    def generate_basic_telemetry(self):
        """Generate basic sensor telemetry data"""
        # Simulate daily temperature cycle (18-35°C)
        hour = datetime.now().hour
        base_temp = 22 + 8 * math.sin((hour - 6) * math.pi / 12)
        temperature = round(base_temp + random.uniform(-2, 2), 2)
        
        # Simulate humidity (inversely related to temperature)
        humidity = round(70 - (temperature - 20) * 2 + random.uniform(-5, 5), 1)
        humidity = max(30, min(90, humidity))  # Clamp between 30-90%
        
        # Simulate battery drain
        runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.battery_level = max(0, 100 - runtime_hours * 0.5)  # 0.5% per hour
        
        return {
            "temperature": temperature,
            "humidity": humidity,
            "pressure": round(random.uniform(1010, 1020), 2),
            "battery_level": round(self.battery_level, 1),
            "signal_strength": random.randint(-80, -40),
            "timestamp": datetime.now().isoformat()
        }
    
    def send_telemetry(self, data):
        """Send telemetry data to the server"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/devices/telemetry",
                json={"data": data},
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 201:
                self.logger.info(f"📊 Telemetry sent: temp={data['temperature']}°C, "
                               f"humidity={data['humidity']}%, battery={data['battery_level']}%")
                return True
            else:
                self.logger.error(f"❌ Telemetry failed: {response.status_code} - {response.json()}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Telemetry error: {e}")
            return False
    
    def simulate_network_failure(self, failure_rate=0.05):
        """Simulate network failures"""
        return random.random() < failure_rate
    
    def run_simulation(self, duration=300, telemetry_interval=30, heartbeat_interval=60):
        """Run the device simulation"""
        if not self.register_device():
            return
        
        self.logger.info(f"🚀 Starting simulation for {duration} seconds")
        self.logger.info(f"   Telemetry every {telemetry_interval}s")
        self.logger.info(f"   Heartbeat every {heartbeat_interval}s")
        self.logger.info("   Press Ctrl+C to stop")
        
        self.is_running = True
        start_time = time.time()
        last_telemetry = 0
        last_heartbeat = 0
        
        try:
            while self.is_running and (time.time() - start_time) < duration:
                current_time = time.time()
                
                # Simulate network failure
                if self.simulate_network_failure():
                    self.logger.warning("📡 Network failure simulated - skipping this cycle")
                    time.sleep(5)
                    continue
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # Send telemetry
                if current_time - last_telemetry >= telemetry_interval:
                    telemetry_data = self.generate_basic_telemetry()
                    self.send_telemetry(telemetry_data)
                    last_telemetry = current_time
                
                time.sleep(1)  # Check every second
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Simulation stopped by user")
        
        self.logger.info(f"✅ Simulation completed for device {self.device_name}")


def main():
    parser = argparse.ArgumentParser(description='Basic IoT Device Simulator')
    parser.add_argument('--name', default=f"Device_{random.randint(1000, 9999)}", 
                       help='Device name')
    parser.add_argument('--type', default='sensor', 
                       help='Device type (sensor, actuator, etc.)')
    parser.add_argument('--duration', type=int, default=300, 
                       help='Simulation duration in seconds (default: 300)')
    parser.add_argument('--telemetry-interval', type=int, default=30, 
                       help='Telemetry interval in seconds (default: 30)')
    parser.add_argument('--heartbeat-interval', type=int, default=60, 
                       help='Heartbeat interval in seconds (default: 60)')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the IoT service')
    
    args = parser.parse_args()
    
    # Check if service is available
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ IoT service is not responding correctly")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to IoT service at {args.url}")
        print(f"   Error: {e}")
        print("   Make sure the service is running: poetry run python app.py")
        return 1
    
    # Run simulation
    device = BasicIoTDevice(args.name, args.type, args.url)
    device.run_simulation(args.duration, args.telemetry_interval, args.heartbeat_interval)
    return 0


if __name__ == "__main__":
    exit(main())
