#!/bin/bash
# This script verifies the MQTT broker is running and accessible

set -e

echo "Verifying MQTT broker..."
echo "Checking port 1883..."

# Check if port is open
if nc -z localhost 1883; then
    echo "Port 1883 is open"
else
    echo "Error: MQTT broker not listening on port 1883"
    exit 1
fi

# Install mosquitto clients if not already installed
if ! command -v mosquitto_pub &> /dev/null; then
    echo "Installing mosquitto clients..."
    apt-get update -qq && apt-get install -y -qq mosquitto-clients
fi

# Test MQTT with pub/sub
echo "Testing MQTT with publish and subscribe..."
TEMP_FILE=$(mktemp)
TEST_MESSAGE="test-message-$(date +%s)"

# Start subscriber in background
mosquitto_sub -h localhost -t test/mqtt/healthcheck -C 1 > $TEMP_FILE &
SUB_PID=$!

# Wait a moment for subscriber to connect
sleep 1

# Publish message
mosquitto_pub -h localhost -t test/mqtt/healthcheck -m "$TEST_MESSAGE"

# Wait for subscriber to receive message
wait $SUB_PID || { echo "Subscriber process failed"; exit 1; }

# Check received message
RECEIVED=$(cat $TEMP_FILE)
rm $TEMP_FILE

if [ "$RECEIVED" = "$TEST_MESSAGE" ]; then
    echo "✓ MQTT broker working correctly!"
    exit 0
else
    echo "✗ MQTT broker test failed. Expected '$TEST_MESSAGE', got '$RECEIVED'"
    exit 1
fi
