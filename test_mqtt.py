#!/usr/bin/env python3
"""
Simple MQTT Test Script for IoTFlow
Tests the MQTT integration without starting the full Flask application
"""

import json
import time
import sys
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    from src.mqtt.topics import MQTTTopicManager
    from src.mqtt.client import MQTTConfig, MQTTClientService
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install MQTT dependencies with Poetry:")
    print("poetry add paho-mqtt asyncio-mqtt")
    sys.exit(1)


def test_mqtt_integration():
    """Test MQTT broker connection and topic functionality"""
    
    print("🚀 IoTFlow MQTT Integration Test")
    print("=" * 50)
    
    # Test 1: Topic Manager
    print("\n📋 Testing Topic Manager...")
    
    try:
        # Test topic generation
        device_id = "sensor_001"
        device_topics = MQTTTopicManager.get_device_topics(device_id)
        
        print(f"✅ Generated {len(device_topics)} topics for device: {device_id}")
        
        # Test topic validation
        test_topic = MQTTTopicManager.get_topic("device_telemetry_sensors", device_id=device_id)
        is_valid = MQTTTopicManager.validate_topic(test_topic)
        
        print(f"✅ Topic validation: {test_topic} -> {is_valid}")
        
        # Test topic parsing
        parsed = MQTTTopicManager.parse_topic(test_topic)
        print(f"✅ Topic parsing successful: {parsed['device_id']} -> {parsed['topic_type']}")
        
    except Exception as e:
        print(f"❌ Topic Manager test failed: {e}")
        return False
    
    # Test 2: MQTT Client Configuration
    print("\n🔧 Testing MQTT Client Configuration...")
    
    try:
        # Create MQTT configuration
        mqtt_config = MQTTConfig(
            host="localhost",
            port=1883,
            username="admin",
            password="admin123",
            client_id="iotflow_test_client"
        )
        
        print(f"✅ MQTT Config created: {mqtt_config.host}:{mqtt_config.port}")
        
        # Create MQTT client service
        mqtt_service = MQTTClientService(mqtt_config)
        print("✅ MQTT Client service created")
        
    except Exception as e:
        print(f"❌ MQTT Client configuration failed: {e}")
        return False
    
    # Test 3: MQTT Broker Connection
    print("\n🌐 Testing MQTT Broker Connection...")
    
    try:
        # Test connection
        if mqtt_service.connect():
            print("✅ Connected to MQTT broker successfully")
            
            # Wait a moment for connection to stabilize
            time.sleep(2)
            
            # Test publish
            test_payload = {
                "device_id": device_id,
                "temperature": 23.5,
                "humidity": 65.2,
                "timestamp": datetime.utcnow().isoformat(),
                "test": True
            }
            
            telemetry_topic = MQTTTopicManager.get_topic("device_telemetry_sensors", device_id=device_id)
            
            if mqtt_service.publish(telemetry_topic, test_payload):
                print(f"✅ Published test message to: {telemetry_topic}")
            else:
                print("❌ Failed to publish test message")
                return False
            
            # Test status update
            status_topic = MQTTTopicManager.get_topic("device_status_online", device_id=device_id)
            status_payload = {
                "device_id": device_id,
                "status": "online",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if mqtt_service.publish(status_topic, status_payload, retain=True):
                print(f"✅ Published status message to: {status_topic}")
            else:
                print("❌ Failed to publish status message")
                return False
            
            # Get connection status
            status = mqtt_service.get_connection_status()
            print(f"✅ Connection status: {status['connected']}")
            
            # Disconnect
            mqtt_service.disconnect()
            print("✅ Disconnected from MQTT broker")
            
        else:
            print("❌ Failed to connect to MQTT broker")
            print("   Make sure the broker is running: ./mqtt_manage.sh status")
            return False
            
    except Exception as e:
        print(f"❌ MQTT Broker connection test failed: {e}")
        return False
    
    return True


def test_topic_examples():
    """Show example topics and their usage"""
    
    print("\n📡 Topic Structure Examples")
    print("=" * 50)
    
    device_id = "sensor_001"
    group_id = "warehouse_a"
    
    # Device topics
    print(f"\n🔧 Device Topics for '{device_id}':")
    device_topics = MQTTTopicManager.get_device_topics(device_id)
    
    for topic_name, topic_path in list(device_topics.items())[:6]:  # Show first 6
        topic_structure = MQTTTopicManager.get_topic_structure(topic_name)
        print(f"  {topic_structure.topic_type.value:12} | {topic_path}")
    
    # Fleet topics
    print(f"\n🚛 Fleet Topics for '{group_id}':")
    fleet_topics = MQTTTopicManager.get_fleet_topics(group_id)
    
    for topic_name, topic_path in fleet_topics.items():
        topic_structure = MQTTTopicManager.get_topic_structure(topic_name)
        print(f"  {topic_structure.topic_type.value:12} | {topic_path}")
    
    # Wildcard patterns
    print(f"\n🔍 Wildcard Subscription Patterns:")
    patterns = MQTTTopicManager.get_wildcard_patterns()
    
    for pattern_name, pattern in list(patterns.items())[:4]:  # Show first 4
        print(f"  {pattern_name:20} | {pattern}")


def main():
    """Main test function"""
    
    print("🧪 Starting IoTFlow MQTT Integration Tests...")
    
    # Show topic examples first
    test_topic_examples()
    
    # Run integration tests
    if test_mqtt_integration():
        print("\n" + "=" * 50)
        print("🎉 All MQTT integration tests passed!")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: poetry install")
        print("   2. Copy environment: cp .env.example .env")
        print("   3. Start the application: poetry run python app.py")
        print("   4. Test API endpoints at http://localhost:5000")
        print("\n📚 Check MQTT_INTEGRATION.md for detailed documentation")
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ MQTT integration tests failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Check broker status: ./mqtt_manage.sh status")
        print("   2. Check broker logs: ./mqtt_manage.sh logs")
        print("   3. Verify credentials: ./mqtt_manage.sh test admin admin123")
        return 1


if __name__ == "__main__":
    sys.exit(main())
