#!/usr/bin/env python3
"""
Send Commands to MQTT Devices
A utility script to send commands to running MQTT device simulators
"""

import json
import argparse
import paho.mqtt.client as mqtt
import time
import uuid


def send_command(device_name, command_type, host="localhost", port=1883, **kwargs):
    """Send a command to a specific device"""
    
    client = mqtt.Client(client_id=f"command-sender-{uuid.uuid4().hex[:8]}")
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker")
        else:
            print(f"❌ Failed to connect: {rc}")
    
    def on_publish(client, userdata, mid):
        print(f"📤 Command sent successfully")
    
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        print(f"🔌 Connecting to MQTT broker at {host}:{port}")
        client.connect(host, port, 60)
        client.loop_start()
        
        # Wait for connection
        time.sleep(1)
        
        # Prepare command
        command = {
            "type": command_type,
            "id": f"cmd-{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            **kwargs
        }
        
        topic = f"devices/{device_name}/commands"
        
        print(f"📨 Sending command to {device_name}:")
        print(f"   Topic: {topic}")
        print(f"   Command: {json.dumps(command, indent=2)}")
        
        # Send command
        result = client.publish(topic, json.dumps(command), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            time.sleep(1)  # Allow time for publishing
            print(f"✅ Command sent successfully!")
        else:
            print(f"❌ Failed to send command: {result.rc}")
        
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Send commands to MQTT device simulators',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restart a device
  python send_device_command.py -d TestDevice003 -c restart

  # Update telemetry interval
  python send_device_command.py -d TestDevice003 -c update_interval --interval 10

  # Get device status
  python send_device_command.py -d TestDevice003 -c get_status

  # Calibrate sensors
  python send_device_command.py -d TestDevice003 -c calibrate
        """
    )
    
    parser.add_argument('-d', '--device', required=True,
                       help='Device name to send command to')
    
    parser.add_argument('-c', '--command', required=True,
                       choices=['restart', 'update_interval', 'get_status', 'calibrate'],
                       help='Command to send')
    
    parser.add_argument('--host', default='localhost',
                       help='MQTT broker host (default: localhost)')
    
    parser.add_argument('--port', type=int, default=1883,
                       help='MQTT broker port (default: 1883)')
    
    parser.add_argument('--interval', type=int,
                       help='New telemetry interval (for update_interval command)')
    
    args = parser.parse_args()
    
    # Prepare command arguments
    command_kwargs = {}
    
    if args.command == 'update_interval':
        if not args.interval:
            print("❌ --interval is required for update_interval command")
            return 1
        command_kwargs['interval'] = args.interval
    
    # Send command
    send_command(
        device_name=args.device,
        command_type=args.command,
        host=args.host,
        port=args.port,
        **command_kwargs
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
