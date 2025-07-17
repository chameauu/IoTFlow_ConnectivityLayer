#!/usr/bin/env python3
"""
MQTT Connection Test Script
Used to validate MQTT connectivity in CI environment
"""

import paho.mqtt.client as mqtt
import sys
import time

def on_connect(client, userdata, flags, rc):
    connection_result = "Connected" if rc == 0 else f"Failed to connect with result code {rc}"
    print(f"MQTT Connection: {connection_result}")

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

def main():
    client_id = "mqtt_test_client"
    host = "localhost"
    port = 1883
    
    print(f"Attempting to connect to MQTT broker at {host}:{port}")
    
    client = mqtt.Client(client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(host, port, 60)
        print("Connection successful")
        
        # Test publish
        test_topic = "iotflow/test/ci"
        test_payload = '{"test":"hello from CI"}'
        print(f"Publishing to {test_topic}: {test_payload}")
        client.publish(test_topic, test_payload)
        
        # Subscribe to test topic
        client.subscribe(test_topic)
        print(f"Subscribed to {test_topic}")
        
        # Process messages for 2 seconds
        client.loop_start()
        time.sleep(2)
        client.loop_stop()
        
        client.disconnect()
        print("MQTT test completed successfully")
        return 0
    except Exception as e:
        print(f"MQTT test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
