#!/bin/bash
"""
MQTT Monitor Script for New Device Simulator
Monitor all topics for a specific device or all devices
"""

# Default values
DEVICE_NAME=""
MQTT_HOST="localhost"
MQTT_PORT="1883"
SHOW_ALL=false

# Help function
show_help() {
    echo "MQTT Monitor Script for IoTFlow Device Simulators"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --device NAME    Monitor specific device (e.g., TestDevice003)"
    echo "  -a, --all           Monitor all device topics"
    echo "  -h, --host HOST     MQTT broker host (default: localhost)"
    echo "  -p, --port PORT     MQTT broker port (default: 1883)"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -d TestDevice003                    # Monitor specific device"
    echo "  $0 -a                                  # Monitor all devices"
    echo "  $0 -d HighFreqSensor -h 192.168.1.100 # Custom host"
    echo ""
    echo "Topics monitored:"
    echo "  devices/DEVICE/telemetry  - Sensor data"
    echo "  devices/DEVICE/heartbeat  - Health status"
    echo "  devices/DEVICE/status     - Device status"
    echo "  devices/DEVICE/errors     - Error reports"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--device)
            DEVICE_NAME="$2"
            shift 2
            ;;
        -a|--all)
            SHOW_ALL=true
            shift
            ;;
        -h|--host)
            MQTT_HOST="$2"
            shift 2
            ;;
        -p|--port)
            MQTT_PORT="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if mosquitto_sub is installed
if ! command -v mosquitto_sub &> /dev/null; then
    echo "❌ mosquitto_sub not found. Please install mosquitto-clients:"
    echo "   sudo apt-get install mosquitto-clients"
    exit 1
fi

# Determine topic pattern
if [ "$SHOW_ALL" = true ]; then
    TOPIC_PATTERN="devices/+/+"
    echo "🔍 Monitoring ALL device topics on $MQTT_HOST:$MQTT_PORT"
elif [ -n "$DEVICE_NAME" ]; then
    TOPIC_PATTERN="devices/$DEVICE_NAME/+"
    echo "🔍 Monitoring device '$DEVICE_NAME' on $MQTT_HOST:$MQTT_PORT"
else
    echo "❌ Please specify either a device name (-d) or use --all"
    echo "Use --help for more information"
    exit 1
fi

echo "📡 Topic pattern: $TOPIC_PATTERN"
echo "🎯 Press Ctrl+C to stop monitoring"
echo "----------------------------------------"

# Start monitoring
mosquitto_sub -h "$MQTT_HOST" -p "$MQTT_PORT" -t "$TOPIC_PATTERN" -v --pretty
