#!/bin/bash
# Complete Data Flow Checker for ESP32 device
# Checks MQTT broker, database, and IoTDB for device data

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check if device ID is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <device_id>"
    echo "Example: $0 1 (for my_esp32_001)"
    exit 1
fi

DEVICE_ID=$1

echo "🚀 Complete Data Flow Check for Device $DEVICE_ID"
echo "============================================================"

# 1. Check if services are running
log_step "Checking if services are running..."

if ! docker compose ps | grep -q "Up"; then
    log_error "Services are not running. Start them with: ./docker-manage.sh start"
    exit 1
fi

# Check specific services
for service in mosquitto iotdb redis; do
    if docker compose ps $service | grep -q "Up"; then
        log_info "$service is running"
    else
        log_error "$service is not running"
    fi
done

echo

# 2. Check MQTT broker connectivity
log_step "Testing MQTT broker connectivity..."

python3 -c "
import paho.mqtt.client as mqtt
import sys

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('✅ MQTT broker is accessible')
        client.disconnect()
    else:
        print(f'❌ MQTT connection failed with code {rc}')
        sys.exit(1)

client = mqtt.Client()
client.on_connect = on_connect

try:
    client.connect('localhost', 1883, 60)
    client.loop_start()
    import time
    time.sleep(2)
    client.loop_stop()
except Exception as e:
    print(f'❌ MQTT connection error: {e}')
    sys.exit(1)
"

echo

# 3. Check SQLite database
log_step "Checking SQLite database for device $DEVICE_ID..."

if [ ! -f "instance/iotflow.db" ]; then
    log_error "SQLite database not found. Run: ./docker-manage.sh init-app"
    exit 1
fi

python3 -c "
import sqlite3
import sys

try:
    conn = sqlite3.connect('instance/iotflow.db')
    cursor = conn.cursor()
    
    # Check if device exists
    cursor.execute('SELECT id, name, api_key FROM devices WHERE id = ?', ($DEVICE_ID,))
    device = cursor.fetchone()
    
    if device:
        print(f'✅ Device $DEVICE_ID found: {device[1]} (API Key: {device[2][:8]}...)')
    else:
        print(f'❌ Device $DEVICE_ID not found in database')
        sys.exit(1)
    
    # Check recent telemetry
    cursor.execute('''
        SELECT COUNT(*) FROM telemetry_data 
        WHERE device_id = ? AND timestamp > datetime(\"now\", \"-1 hour\")
    ''', ($DEVICE_ID,))
    
    count = cursor.fetchone()[0]
    print(f'📊 Recent telemetry records (last hour): {count}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"

echo

# 4. Check IoTDB data
log_step "Checking IoTDB for device $DEVICE_ID data..."

python3 scripts/check_iotdb_data.py $DEVICE_ID

echo

# 5. Show MQTT topic structure
log_step "Expected MQTT topics for device $DEVICE_ID:"
echo "📤 Publish (ESP32 → Server):"
echo "   iotflow/devices/$DEVICE_ID/telemetry/sensors"
echo "   iotflow/devices/$DEVICE_ID/telemetry/events"
echo "   iotflow/devices/$DEVICE_ID/telemetry/metrics"
echo "   iotflow/devices/$DEVICE_ID/status/heartbeat"
echo "   iotflow/devices/$DEVICE_ID/status/online"

echo
echo "📥 Subscribe (Server → ESP32):"
echo "   iotflow/devices/$DEVICE_ID/commands/control"

echo

# 6. Real-time monitoring option
log_step "Monitoring Options:"
echo "1. Monitor MQTT messages in real-time:"
echo "   python3 scripts/monitor_device_data.py $DEVICE_ID"
echo
echo "2. Test MQTT connectivity:"
echo "   python3 scripts/mqtt_test_client.py"
echo
echo "3. Check IoTDB data:"
echo "   python3 scripts/check_iotdb_data.py $DEVICE_ID"
echo
echo "4. View MQTT logs:"
echo "   ./docker-manage.sh logs mosquitto"
echo
echo "5. View application logs:"
echo "   tail -f logs/iotflow.log"

echo
echo "============================================================"
log_info "Data flow check completed for device $DEVICE_ID"

# Ask if user wants to start real-time monitoring
read -p "Start real-time MQTT monitoring for device $DEVICE_ID? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting real-time monitoring..."
    python3 scripts/monitor_device_data.py $DEVICE_ID
fi
