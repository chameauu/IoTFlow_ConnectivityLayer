#!/usr/bin/env python3
"""
MQTT Fleet Simulator for IoTFlow
Simulates multiple IoT devices connecting via MQTT
"""

import os
import sys
import time
import json
import signal
import random
import logging
import argparse
import threading
from typing import List, Dict
from mqtt_device_simulator import MQTTDeviceSimulator


class MQTTFleetSimulator:
    def __init__(
        self,
        device_count=5,
        device_types=None,
        host="localhost",
        port=1883,
        username="admin",
        password="admin123",
    ):
        self.device_count = device_count
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.devices = []
        self.device_threads = []
        self.exit_flag = False
        
        # Default device types if not specified
        self.device_types = device_types or [
            "temperature_sensor",
            "motion_sensor",
            "smart_meter"
        ]
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        self.logger = logging.getLogger("Fleet-Simulator")
    
    def create_device(self, device_id, device_type):
        """Create a device simulator"""
        return MQTTDeviceSimulator(
            device_id=device_id,
            device_type=device_type,
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password
        )
    
    def device_thread_function(self, device, duration, interval, stagger_start=0):
        """Function to run a device in a separate thread"""
        if stagger_start > 0:
            time.sleep(stagger_start)
        
        device.run(duration=duration, telemetry_interval=interval)
    
    def generate_unique_id(self, prefix, idx):
        """Generate a unique device ID"""
        return f"{prefix}-{idx:04d}"
    
    def run(self, duration=300, telemetry_interval=5, stagger_start=True):
        """Run the fleet simulation"""
        
        self.logger.info("🚀 Starting MQTT Fleet Simulation")
        self.logger.info(f"   Devices: {self.device_count}")
        self.logger.info(f"   MQTT Broker: {self.host}:{self.port}")
        self.logger.info(f"   Duration: {duration} seconds")
        
        # Set up signal handlers for clean exit
        def signal_handler(sig, frame):
            self.logger.info("🛑 Stopping fleet simulation...")
            self.exit_flag = True
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create and start devices
        for i in range(self.device_count):
            # Select a device type
            device_type = random.choice(self.device_types)
            
            # Generate a unique device ID with the type as prefix
            device_id = self.generate_unique_id(device_type, i+1)
            
            # Create the device
            device = self.create_device(device_id, device_type)
            self.devices.append(device)
            
            # Calculate stagger time if enabled
            stagger_time = random.uniform(0, 5) if stagger_start else 0
            
            # Start device in a separate thread
            thread = threading.Thread(
                target=self.device_thread_function,
                args=(device, duration, telemetry_interval, stagger_time)
            )
            thread.daemon = True
            self.device_threads.append(thread)
            thread.start()
            
            self.logger.info(f"Started device {device_id} ({device_type})")
        
        self.logger.info(f"All {self.device_count} devices started")
        
        # Wait for all threads to complete or until interrupted
        start_time = time.time()
        try:
            while not self.exit_flag and (time.time() - start_time < duration + 10):
                # Check if all threads have finished
                if all(not t.is_alive() for t in self.device_threads):
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self.exit_flag = True
            
            # Give threads time to exit gracefully
            for thread in self.device_threads:
                if thread.is_alive():
                    thread.join(timeout=2)
        
        self.logger.info("✅ Fleet simulation completed")
        return True


def main():
    """Main function to run the fleet simulator from command line"""
    parser = argparse.ArgumentParser(description='MQTT Fleet Simulator for IoTFlow')
    parser.add_argument('--count', type=int, default=5,
                        help='Number of devices to simulate')
    parser.add_argument('--types', nargs='+', 
                        default=['temperature_sensor', 'motion_sensor', 'smart_meter'],
                        help='List of device types to simulate')
    parser.add_argument('--host', default='localhost',
                        help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883,
                        help='MQTT broker port')
    parser.add_argument('--username', default='admin',
                        help='MQTT username')
    parser.add_argument('--password', default='admin123',
                        help='MQTT password')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration of simulation in seconds')
    parser.add_argument('--interval', type=int, default=5,
                        help='Telemetry publishing interval in seconds')
    parser.add_argument('--no-stagger', action='store_true',
                        help='Disable staggered start of devices')
    
    args = parser.parse_args()
    
    # Create and run fleet simulator
    fleet = MQTTFleetSimulator(
        device_count=args.count,
        device_types=args.types,
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    fleet.run(
        duration=args.duration,
        telemetry_interval=args.interval,
        stagger_start=not args.no_stagger
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
