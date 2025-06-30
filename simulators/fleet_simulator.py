#!/usr/bin/env python3
"""
Multi-Device Fleet Simulator
Simulate multiple IoT devices of different types running concurrently
"""

import threading
import time
import random
import argparse
import logging
from datetime import datetime
from device_types import (
    TemperatureSensor, SmartDoorLock, SecurityCamera, 
    AirQualityMonitor, SmartThermostat
)

class IoTFleetSimulator:
    """Manage multiple IoT devices simultaneously"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.devices = []
        self.threads = []
        self.is_running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("FleetSimulator")
    
    def create_device_fleet(self, fleet_config):
        """Create a fleet of devices based on configuration"""
        device_id = 1
        
        for device_type, count in fleet_config.items():
            for i in range(count):
                device_name = f"{device_type}_{device_id:03d}"
                
                if device_type == "temperature":
                    location = random.choice(["Indoor", "Outdoor", "Greenhouse", "Server Room"])
                    device = TemperatureSensor(device_name, location, self.base_url)
                elif device_type == "door_lock":
                    device = SmartDoorLock(device_name, self.base_url)
                elif device_type == "camera":
                    device = SecurityCamera(device_name, self.base_url)
                elif device_type == "air_quality":
                    device = AirQualityMonitor(device_name, self.base_url)
                elif device_type == "thermostat":
                    device = SmartThermostat(device_name, self.base_url)
                else:
                    continue
                
                # Override telemetry method for specialized devices
                if hasattr(device, 'generate_telemetry'):
                    device.generate_basic_telemetry = device.generate_telemetry
                
                self.devices.append(device)
                device_id += 1
        
        self.logger.info(f"Created fleet of {len(self.devices)} devices")
        return len(self.devices)
    
    def run_device_simulation(self, device, telemetry_interval, heartbeat_interval, duration):
        """Run simulation for a single device in a thread"""
        try:
            # Add small random delay to prevent all devices registering at once
            time.sleep(random.uniform(0, 5))
            
            # Custom intervals for different device types
            if "camera" in device.device_name.lower():
                telemetry_interval = random.randint(45, 75)  # Cameras send less frequently
            elif "thermostat" in device.device_name.lower():
                telemetry_interval = random.randint(120, 180)  # Thermostats less frequent
            elif "door_lock" in device.device_name.lower():
                telemetry_interval = random.randint(60, 120)  # Locks on events
            
            device.run_simulation(duration, telemetry_interval, heartbeat_interval)
            
        except Exception as e:
            self.logger.error(f"Device {device.device_name} simulation failed: {e}")
    
    def start_fleet_simulation(self, duration=600, base_telemetry_interval=60, heartbeat_interval=120):
        """Start simulation for all devices in the fleet"""
        if not self.devices:
            self.logger.error("No devices in fleet. Create devices first.")
            return
        
        self.logger.info(f"🚀 Starting fleet simulation with {len(self.devices)} devices")
        self.logger.info(f"   Duration: {duration} seconds")
        self.logger.info(f"   Base telemetry interval: {base_telemetry_interval}s")
        self.logger.info(f"   Heartbeat interval: {heartbeat_interval}s")
        
        self.is_running = True
        
        # Start each device in its own thread
        for device in self.devices:
            # Add some randomization to intervals
            telemetry_interval = base_telemetry_interval + random.randint(-10, 10)
            
            thread = threading.Thread(
                target=self.run_device_simulation,
                args=(device, telemetry_interval, heartbeat_interval, duration),
                name=f"Thread-{device.device_name}"
            )
            thread.start()
            self.threads.append(thread)
        
        self.logger.info(f"Started {len(self.threads)} device threads")
        
        try:
            # Wait for all threads to complete
            for thread in self.threads:
                thread.join()
        except KeyboardInterrupt:
            self.logger.info("🛑 Fleet simulation stopped by user")
            self.is_running = False
        
        self.logger.info("✅ Fleet simulation completed")
    
    def get_fleet_summary(self):
        """Get summary of the device fleet"""
        summary = {}
        for device in self.devices:
            device_type = device.device_type
            if device_type not in summary:
                summary[device_type] = 0
            summary[device_type] += 1
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='IoT Fleet Simulator')
    parser.add_argument('--preset', 
                       choices=['home', 'office', 'factory', 'custom'],
                       default='home',
                       help='Preset device configuration')
    parser.add_argument('--duration', type=int, default=600, 
                       help='Simulation duration in seconds')
    parser.add_argument('--telemetry-interval', type=int, default=60,
                       help='Base telemetry interval in seconds')
    parser.add_argument('--heartbeat-interval', type=int, default=120,
                       help='Heartbeat interval in seconds')
    parser.add_argument('--url', default='http://localhost:5000',
                       help='IoT service base URL')
    
    # Custom fleet configuration
    parser.add_argument('--temperature-sensors', type=int, default=0,
                       help='Number of temperature sensors')
    parser.add_argument('--door-locks', type=int, default=0,
                       help='Number of smart door locks')
    parser.add_argument('--cameras', type=int, default=0,
                       help='Number of security cameras')
    parser.add_argument('--air-monitors', type=int, default=0,
                       help='Number of air quality monitors')
    parser.add_argument('--thermostats', type=int, default=0,
                       help='Number of smart thermostats')
    
    args = parser.parse_args()
    
    # Define preset configurations
    presets = {
        'home': {
            'temperature': 3,      # Living room, bedroom, outdoor
            'door_lock': 2,        # Front door, back door
            'camera': 2,           # Front yard, driveway
            'air_quality': 1,      # Living room
            'thermostat': 1        # Main thermostat
        },
        'office': {
            'temperature': 5,      # Multiple rooms
            'door_lock': 3,        # Main entrance, office doors
            'camera': 4,           # Entrances, hallways
            'air_quality': 2,      # Main areas
            'thermostat': 2        # Different zones
        },
        'factory': {
            'temperature': 10,     # Multiple zones
            'door_lock': 5,        # Security doors
            'camera': 8,           # Comprehensive coverage
            'air_quality': 4,      # Environmental monitoring
            'thermostat': 3        # Zone control
        }
    }
    
    # Determine fleet configuration
    if args.preset == 'custom':
        fleet_config = {
            'temperature': args.temperature_sensors,
            'door_lock': args.door_locks,
            'camera': args.cameras,
            'air_quality': args.air_monitors,
            'thermostat': args.thermostats
        }
    else:
        fleet_config = presets[args.preset]
    
    # Check if service is available
    import requests
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ IoT service is not responding correctly")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to IoT service at {args.url}")
        print(f"   Error: {e}")
        return 1
    
    # Create and run fleet simulation
    fleet = IoTFleetSimulator(args.url)
    device_count = fleet.create_device_fleet(fleet_config)
    
    if device_count == 0:
        print("❌ No devices configured. Use --preset or specify device counts.")
        return 1
    
    print(f"📊 Fleet Configuration ({args.preset}):")
    for device_type, count in fleet.get_fleet_summary().items():
        print(f"   {device_type}: {count} devices")
    
    print(f"\n🌐 Connecting to IoT service at {args.url}")
    fleet.start_fleet_simulation(
        args.duration, 
        args.telemetry_interval, 
        args.heartbeat_interval
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
