# ESP32 Device Registration Workflow

This document explains how ESP32 devices must register with the IoTFlow server before they can send MQTT data.

## Overview

The new workflow requires ESP32 devices to:
1. ✅ **Register via HTTP API** - Get device ID and API key
2. ✅ **Validate registration** - Server checks device status  
3. ✅ **Send MQTT data** - Only after successful registration

## Security Benefits

- 🔐 **Device Authentication**: Only registered devices can send data
- 🛡️ **API Key Validation**: Each device has unique credentials
- 📊 **Access Control**: Server validates every message
- 🚫 **Unauthorized Prevention**: Unregistered devices are blocked

## ESP32 Implementation

### 1. Device Registration (HTTP)

The ESP32 first registers via HTTP POST to get credentials:

```cpp
// Registration endpoint: POST /api/v1/devices/register
{
  "name": "my_esp32_001",
  "device_type": "esp32", 
  "description": "ESP32 IoT device with sensors",
  "location": "lab",
  "firmware_version": "1.0.0",
  "hardware_version": "ESP32-WROOM-32",
  "capabilities": ["temperature", "humidity", "wifi_monitoring"]
}

// Server response:
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "my_esp32_001", 
    "api_key": "abc123...",
    "status": "active"
  }
}
```

### 2. MQTT Communication (After Registration)

Only after registration can the device send MQTT data:

```cpp
// Topic: iotflow/devices/{device_id}/telemetry/sensors
{
  "api_key": "abc123...",
  "timestamp": "2025-07-04T10:30:00Z",
  "data": {
    "temperature": 23.5,
    "humidity": 65.2
  },
  "metadata": {
    "device_type": "esp32",
    "firmware_version": "1.0.0"
  }
}
```

## Updated ESP32 Code Flow

```cpp
void setup() {
  // 1. Connect to WiFi
  setup_wifi();
  
  // 2. Register device (HTTP API)
  if (register_device_with_server()) {
    // 3. Setup MQTT only after registration
    client.setServer(server_host, mqtt_port);
    client.setCallback(mqtt_callback);
  }
}

void loop() {
  // Only send MQTT data if registered
  if (!device_registered) {
    // Retry registration every 30 seconds
    retry_registration();
    return;
  }
  
  // Normal MQTT operations
  send_telemetry_data();
}
```

## Server-Side Validation

The server validates each MQTT message:

1. **API Key Check**: `validate_device_registration(device_id, api_key)`
2. **Device Status**: Must be "active" in database
3. **Message Format**: JSON with required fields
4. **Authorization**: `is_device_registered_for_mqtt(payload)`

## Testing the Workflow

### 1. Test Device Registration

```bash
# Register a new ESP32 device
python3 scripts/esp32_registration_test.py my_esp32_001
```

This will:
- ✅ Register the device via HTTP API
- ✅ Test device status endpoint
- ✅ Send test telemetry data
- ✅ Provide ESP32 configuration values

### 2. Monitor Data Flow

```bash
# Check complete data flow
./scripts/check_device_data_flow.sh 1

# Monitor real-time MQTT messages
python3 scripts/monitor_device_data.py 1

# Check IoTDB data storage
python3 scripts/check_iotdb_data.py 1
```

### 3. MQTT Command Line Testing

```bash
# Subscribe to device topics
mosquitto_sub -h localhost -t "iotflow/devices/1/telemetry/+" -v

# Test device status
mosquitto_sub -h localhost -t "iotflow/devices/1/status/+" -v

# Check all device messages
mosquitto_sub -h localhost -t "iotflow/devices/+/+/+" -v
```

## Error Handling

### Registration Failures

- **409 Conflict**: Device name already exists
  - Solution: Use different device name or delete existing device
  
- **500 Server Error**: Database/server issues
  - Solution: Check server logs and database connectivity

### MQTT Authorization Failures  

- **Invalid API Key**: Device not found or API key mismatch
- **Device Inactive**: Device status is not "active"
- **Missing Fields**: Payload missing required fields (api_key, data)

## Configuration Files

### ESP32 Arduino Code
```cpp
// Update these values after registration:
const int device_id = 1;  // From registration response
const char* device_api_key = "your_api_key";  // From registration response
String device_name = "my_esp32_001";  // Unique device name
const char* server_host = "192.168.1.100";  // Your server IP
```

### PlatformIO Dependencies
```ini
lib_deps = 
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^6.21.3
    adafruit/DHT sensor library@^1.4.4
```

## Security Considerations

1. **API Key Storage**: Store securely, don't hardcode in production
2. **Network Security**: Use TLS/SSL for production deployments  
3. **Device Lifecycle**: Deactivate devices when decommissioned
4. **Key Rotation**: Implement API key rotation for long-term deployments

## Troubleshooting

### Device Won't Register
- Check server is running: `./docker-manage.sh status`
- Verify network connectivity between ESP32 and server
- Check server logs: `tail -f logs/iotflow.log`

### MQTT Data Not Received
- Verify device registration status
- Check API key is correct
- Monitor MQTT broker: `./docker-manage.sh logs mosquitto`
- Use monitoring script: `python3 scripts/monitor_device_data.py 1`

### Data Not in IoTDB
- Check IoTDB connectivity: `python3 scripts/check_iotdb_data.py 1`
- Verify telemetry processing: Check application logs
- Test direct telemetry: `python3 scripts/mqtt_test_client.py`
