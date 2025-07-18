#!/bin/bash
# Script to verify IoTDB connection

set -e

echo "Verifying IoTDB connection..."

# Simple connection test
if ! nc -z localhost 6667; then
    echo "Error: IoTDB not listening on port 6667"
    exit 1
fi

# Wait for IoTDB to fully initialize
echo "Port 6667 is open, waiting for full initialization..."
sleep 10

# Get container ID
CONTAINER_ID=$(docker ps | grep iotdb | awk '{print $1}')
echo "IoTDB container ID: $CONTAINER_ID"

# Check container logs for successful startup
if docker logs $CONTAINER_ID 2>&1 | grep -q "IoTDB is set up"; then
    echo "IoTDB started successfully"
else
    echo "IoTDB may not be fully initialized yet, checking status..."
    docker logs $CONTAINER_ID 2>&1 | tail -n 50
fi

echo "IoTDB verification completed"
exit 0
