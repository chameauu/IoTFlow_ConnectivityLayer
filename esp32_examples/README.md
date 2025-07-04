# ESP32 IoTFlow Device with API Key Authentication

This ESP32 project demonstrates a complete IoT device implementation with secure API key authentication for the IoTFlow platform.

## 🔐 Authentication Features

### Automatic Device Registration
- **Auto-registration**: Device automatically registers with the IoTFlow server on first boot
- **Persistent Storage**: API key and device ID are stored in ESP32's flash memory
- **Recovery**: Stored credentials are loaded on boot to avoid re-registration

### API Key Management
- **Secure Storage**: API keys are stored using ESP32's Preferences library
- **Validation**: API key format and length validation
- **Refresh**: Automatic API key refresh when authentication fails
- **Factory Reset**: Clear all credentials and force re-registration

### Authentication Flow

```
1. Device Boot
   ├── Load stored credentials from flash
   ├── Validate API key format
   └── If valid: Use existing credentials
       If invalid: Register new device

2. Device Registration (HTTP POST)
   ├── Send device info to /api/v1/devices/register
   ├── Receive device_id and api_key
   ├── Validate received API key
   └── Save credentials to persistent storage

3. MQTT Authentication
   ├── Include api_key in all MQTT messages
   ├── Handle authentication errors gracefully
   └── Auto-refresh API key on auth failures
```

## 📡 MQTT Topics with Authentication

All MQTT messages include the `api_key` field for server-side authentication:

### Telemetry Data
```json
{
  "api_key": "your_device_api_key",
  "ts": "timestamp",
  "temperature": 25,
  "humidity": 60,
  "cpu_temp": 45.2,
  "free_heap": 234560,
  "uptime": 3600
}
```

### Status Messages
```json
{
  "api_key": "your_device_api_key",
  "timestamp": "timestamp",
  "status": "online",
  "device_id": 123
}
```

### Command Responses
```json
{
  "api_key": "your_device_api_key",
  "timestamp": "timestamp",
  "command": "led_on",
  "status": "success",
  "device_id": 123
}
```

## 🎮 Remote Commands

The device responds to various commands sent via MQTT:

### Device Control
- `led_on` - Turn on the LED
- `led_off` - Turn off the LED
- `get_status` - Get current device status

### Authentication Management
- `refresh_api_key` - Force API key refresh
- `factory_reset` - Clear all credentials and restart
- `get_credentials_info` - Get credential debugging info

### Example Command
```json
{
  "command": "led_on"
}
```

## 🔧 Configuration

### Device Settings
```cpp
String device_name = "esp32_101";    // Unique device name
String device_type = "esp32";
String firmware_version = "1.0.0";
String location = "lab";
```

### Server Settings
```cpp
const char* server_host = "192.168.0.13";
const int mqtt_port = 1883;
const int http_port = 5000;
```

### WiFi Settings
```cpp
const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
```

## 🛡️ Security Features

### API Key Validation
- Minimum length: 16 characters
- Maximum length: 128 characters  
- Valid characters: alphanumeric + `-`, `_`, `.`, `+`, `/`

### Error Handling
- **MQTT Authentication Errors**: Automatic API key refresh
- **Too Many Failures**: Clear credentials and force re-registration
- **Invalid API Keys**: Clear storage and re-register
- **Network Errors**: Retry with exponential backoff

### Persistent Storage
- Credentials stored in ESP32's NVS (Non-Volatile Storage)
- Survives power cycles and firmware updates
- Secure flash memory partition

## 📊 Monitoring

### Debug Output
The device provides comprehensive debug output:

```
✅ Device registered successfully!
📋 Device ID: 123
🔑 API Key: abcd1234...
💾 Credentials saved to persistent storage
🔌 Attempting MQTT connection... ✅ connected
📡 Subscribed to: iotflow/devices/123/commands/control
```

### Error Messages
```
❌ MQTT bad credentials - may need API key refresh
🔄 API key refreshed after credential error
✅ API key refreshed successfully!
```

## 🔄 Credential Lifecycle

### First Boot
1. No stored credentials found
2. Device registers with server
3. Receives API key
4. Saves credentials to flash
5. Connects to MQTT

### Subsequent Boots
1. Load credentials from flash
2. Validate API key format
3. Connect to MQTT with stored credentials

### Authentication Failure
1. MQTT connection fails with auth error
2. Attempt API key refresh
3. If refresh fails, clear credentials
4. Force device re-registration

### Factory Reset
1. Receive factory reset command
2. Clear all stored credentials
3. Restart device
4. Device re-registers on next boot

## 📋 Hardware Requirements

- ESP32 development board
- DHT11 temperature/humidity sensor (GPIO 23)
- LED (built-in on GPIO 2)
- WiFi network connection

## 🚀 Installation

1. Configure WiFi credentials in `main.cpp`
2. Set server IP address and ports
3. Upload to ESP32 using PlatformIO
4. Monitor serial output for registration status

## 🔍 Troubleshooting

### Device Won't Register
- Check WiFi connection
- Verify server is running
- Check server URL and port
- Review serial output for error messages

### MQTT Connection Fails
- Verify device is registered
- Check API key validity
- Try manual API key refresh
- Check MQTT broker status

### Authentication Errors
- API key may be expired
- Use `refresh_api_key` command
- Try factory reset if persistent
- Check server-side authentication logs

## 📁 File Structure

```
esp32_examples/
├── src/
│   └── main.cpp           # Main device code with authentication
├── platformio.ini         # PlatformIO configuration
├── esp32_mqtt_client.ino  # Arduino IDE compatibility
└── README.md             # This documentation
```

## 🔮 Future Enhancements

- [ ] Certificate-based authentication (TLS/SSL)
- [ ] API key rotation schedule
- [ ] Encrypted credential storage
- [ ] OTA firmware updates with authentication
- [ ] Device attestation and identity verification
