#!/usr/bin/env python3
"""
Device Data Monitor for IoTFlow Platform
Monitor MQTT messages and IoTDB data for a specific device
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import argparse
from datetime import datetime
import threading
import sqlite3
import os

# MQTT broker settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# Database settings
DB_PATH = "instance/iotflow.db"

class DeviceDataMonitor:
    def __init__(self, device_id):
        self.device_id = device_id
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.message_count = 0
        self.last_message_time = None
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker")
            
            # Subscribe to all topics for this device
            topics = [
                f"iotflow/devices/{self.device_id}/telemetry/+",
                f"iotflow/devices/{self.device_id}/status/+",
                f"iotflow/devices/{self.device_id}/commands/+"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                print(f"📡 Subscribed to: {topic}")
        else:
            print(f"❌ Failed to connect to MQTT broker, return code {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        self.message_count += 1
        self.last_message_time = datetime.now()
        
        print(f"\n🔔 Message #{self.message_count} received at {self.last_message_time.strftime('%H:%M:%S')}")
        print(f"📍 Topic: {msg.topic}")
        
        try:
            # Try to parse as JSON
            payload = json.loads(msg.payload.decode())
            print(f"📦 Payload (JSON):")
            print(json.dumps(payload, indent=2))
            
            # Check if it has the expected structure
            if "api_key" in payload:
                print("✅ Contains API key")
            if "timestamp" in payload:
                print("✅ Contains timestamp")
            if "data" in payload:
                print("✅ Contains data section")
                data_keys = list(payload["data"].keys())
                print(f"   Data keys: {data_keys}")
            if "metadata" in payload:
                print("✅ Contains metadata section")
                
        except json.JSONDecodeError:
            # If not JSON, just show raw payload
            print(f"📦 Payload (Raw): {msg.payload.decode()}")
        
        print("-" * 50)
    
    def check_database_data(self):
        """Check SQLite database for device data"""
        if not os.path.exists(DB_PATH):
            print(f"❌ Database not found at {DB_PATH}")
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if device exists
            cursor.execute("SELECT * FROM devices WHERE id = ?", (self.device_id,))
            device = cursor.fetchone()
            
            if device:
                print(f"✅ Device {self.device_id} found in database")
                print(f"   Device info: {device}")
            else:
                print(f"❌ Device {self.device_id} not found in database")
                return
            
            # Check for telemetry data
            cursor.execute("""
                SELECT COUNT(*) FROM telemetry_data 
                WHERE device_id = ? 
                AND timestamp > datetime('now', '-1 hour')
            """, (self.device_id,))
            
            recent_count = cursor.fetchone()[0]
            print(f"📊 Recent telemetry records (last hour): {recent_count}")
            
            # Get latest telemetry
            cursor.execute("""
                SELECT timestamp, data_type, value, metadata 
                FROM telemetry_data 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 5
            """, (self.device_id,))
            
            latest_data = cursor.fetchall()
            if latest_data:
                print("📈 Latest telemetry data:")
                for row in latest_data:
                    print(f"   {row[0]} | {row[1]} | {row[2]} | {row[3]}")
            else:
                print("❌ No telemetry data found")
            
            conn.close()
            
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
    
    def start_monitoring(self):
        """Start monitoring MQTT messages"""
        print(f"🚀 Starting monitoring for device: {self.device_id}")
        print(f"🏠 MQTT Broker: {MQTT_HOST}:{MQTT_PORT}")
        print(f"💾 Database: {DB_PATH}")
        print("=" * 60)
        
        # Check database first
        self.check_database_data()
        print("=" * 60)
        
        # Start MQTT monitoring
        try:
            self.mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
            
            # Start MQTT loop in background
            self.mqtt_client.loop_start()
            
            print("👂 Listening for MQTT messages... (Press Ctrl+C to stop)")
            
            # Keep running and show periodic stats
            start_time = time.time()
            while True:
                time.sleep(10)
                elapsed = time.time() - start_time
                print(f"\n📊 Stats after {int(elapsed)}s: {self.message_count} messages received")
                if self.last_message_time:
                    print(f"   Last message: {self.last_message_time.strftime('%H:%M:%S')}")
                else:
                    print("   No messages received yet")
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

def check_iotdb_data(device_id):
    """Check IoTDB for device data using docker"""
    print(f"\n🔍 Checking IoTDB for device {device_id}...")
    
    # IoTDB queries to check for data
    queries = [
        f"SHOW TIMESERIES root.iotflow.devices.device_{device_id}.**",
        f"SELECT * FROM root.iotflow.devices.device_{device_id}.** WHERE time > now() - 1h",
        f"SELECT COUNT(*) FROM root.iotflow.devices.device_{device_id}.** WHERE time > now() - 1h"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        # Note: You'll need to run this manually or implement IoTDB client
        print("   Run this query in IoTDB CLI:")
        print(f"   ./docker-manage.sh iotdb")
        print(f"   Then execute: {query}")

def main():
    parser = argparse.ArgumentParser(description='Monitor device data in IoTFlow platform')
    parser.add_argument('device_id', help='Device ID to monitor (e.g., 1 for my_esp32_001)')
    parser.add_argument('--check-iotdb', action='store_true', help='Also show IoTDB check instructions')
    
    args = parser.parse_args()
    
    try:
        device_id = int(args.device_id)
    except ValueError:
        print("❌ Device ID must be a number")
        sys.exit(1)
    
    monitor = DeviceDataMonitor(device_id)
    
    if args.check_iotdb:
        check_iotdb_data(device_id)
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
