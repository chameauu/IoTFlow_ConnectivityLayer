# New MQTT Device Simulator

A comprehensive, production-ready MQTT device simulator with advanced features for the IoTFlow platform.

## Features

### 🚀 **Advanced Capabilities**
- **HTTP Device Registration**: Automatically registers with IoTFlow server before MQTT communication
- **Multiple Simulation Profiles**: Pre-configured profiles for different device types
- **Realistic Telemetry**: Generated based on device type and environmental factors
- **Command Handling**: Responds to remote commands and configuration updates
- **Error Simulation**: Configurable network errors and failures
- **Graceful Shutdown**: Handles signals for clean disconnection

### 📊 **Simulation Profiles**

1. **Default Profile**
   - Telemetry: temperature, humidity, pressure, battery
   - Interval: 30s telemetry, 60s heartbeat
   - Error rate: 2%
   - Battery drain: 0.1%/hour

2. **High Frequency Profile**
   - Telemetry: temperature, humidity, pressure, accelerometer, gyroscope
   - Interval: 5s telemetry, 30s heartbeat
   - Error rate: 1%
   - Battery drain: 0.5%/hour

3. **Energy Efficient Profile**
   - Telemetry: temperature, battery
   - Interval: 5min telemetry, 10min heartbeat
   - Error rate: 0.1%
   - Battery drain: 0.05%/hour

4. **Industrial Profile**
   - Telemetry: temperature, pressure, vibration, power consumption
   - Interval: 10s telemetry, 30s heartbeat
   - Error rate: 0.5%
   - Battery drain: 0.3%/hour

### 🎯 **Command Support**
- `restart`: Simulate device restart
- `update_interval`: Change telemetry interval
- `get_status`: Request device status
- `calibrate`: Simulate sensor calibration

## Usage

### Basic Usage
```bash
# Run with default settings
python simulators/new_mqtt_device_simulator.py --name MyTestDevice

# Run for specific duration
python simulators/new_mqtt_device_simulator.py --name MyDevice --duration 600
```

### Advanced Usage
```bash
# High-frequency industrial sensor
python simulators/new_mqtt_device_simulator.py \
    --name IndustrialSensor001 \
    --type industrial_sensor \
    --profile industrial \
    --duration 1800

# Energy-efficient environmental sensor
python simulators/new_mqtt_device_simulator.py \
    --name EnvSensor001 \
    --type environmental_sensor \
    --profile energy_efficient \
    --duration 3600

# Custom MQTT settings
python simulators/new_mqtt_device_simulator.py \
    --name CustomDevice \
    --host 192.168.1.100 \
    --mqtt-port 1883 \
    --http-port 5000 \
    --qos 2
```

### Debug Mode
```bash
# Run with debug logging
python simulators/new_mqtt_device_simulator.py \
    --name DebugDevice \
    --log-level DEBUG
```

## MQTT Topics

The simulator publishes to the following topics:
- `devices/{device_name}/telemetry` - Sensor data
- `devices/{device_name}/heartbeat` - Device health status
- `devices/{device_name}/status` - Device status and responses
- `devices/{device_name}/errors` - Error reports

The simulator subscribes to:
- `devices/{device_name}/commands` - Remote commands
- `devices/{device_name}/config` - Configuration updates

## Monitoring

### Monitor All Device Topics
```bash
# Monitor all topics for a device
mosquitto_sub -h localhost -p 1883 -t "devices/MyTestDevice/+" -v

# Monitor specific telemetry
mosquitto_sub -h localhost -p 1883 -t "devices/MyTestDevice/telemetry" -v
```

### Send Commands
```bash
# Restart device
mosquitto_pub -h localhost -p 1883 \
    -t "devices/MyTestDevice/commands" \
    -m '{"type":"restart","id":"cmd001"}'

# Update telemetry interval
mosquitto_pub -h localhost -p 1883 \
    -t "devices/MyTestDevice/commands" \
    -m '{"type":"update_interval","interval":10,"id":"cmd002"}'

# Get device status
mosquitto_pub -h localhost -p 1883 \
    -t "devices/MyTestDevice/commands" \
    -m '{"type":"get_status","id":"cmd003"}'
```

## Log Files

The simulator creates log files in the `logs/` directory:
- `logs/device_{device_name}.log` - Device-specific logs
- Console output for real-time monitoring

## Dependencies

Required Python packages (already in project):
- `paho-mqtt` - MQTT client
- `requests` - HTTP requests
- Standard library modules

## Integration with IoTFlow

1. **Device Registration**: Uses IoTFlow's `/api/v1/devices/register` endpoint
2. **Authentication**: Uses device ID and API key for MQTT authentication
3. **Data Storage**: Telemetry is stored in IoTDB via IoTFlow's processing pipeline
4. **Monitoring**: Compatible with IoTFlow's monitoring and alerting systems

## Error Handling

- **Network Failures**: Automatic reconnection with exponential backoff
- **MQTT Disconnections**: Graceful reconnection handling
- **Registration Failures**: Clear error messages and retry logic
- **Message Failures**: Configurable error rate simulation

## Best Practices

1. **Start IoTFlow First**: Ensure the IoTFlow service is running
2. **Unique Device Names**: Use unique names to avoid conflicts
3. **Monitor Resources**: Check system resources for multiple simulators
4. **Log Monitoring**: Use log files for debugging and analysis
5. **Graceful Shutdown**: Use Ctrl+C for clean shutdown

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if IoTFlow service is running
   - Verify host and port settings

2. **Registration Failed**
   - Check HTTP endpoint availability
   - Verify network connectivity

3. **MQTT Authentication Failed**
   - Ensure device registration was successful
   - Check MQTT broker configuration

4. **Missing Logs Directory**
   - The simulator automatically creates the logs directory
   - Ensure write permissions

## Example Output

```
2025-07-04 10:30:15,123 - INFO - [NewMQTT-MyTestDevice] - 🔧 Loaded simulation profile: default
2025-07-04 10:30:15,124 - INFO - [NewMQTT-MyTestDevice] - 🔗 Registering device: MyTestDevice
2025-07-04 10:30:15,456 - INFO - [NewMQTT-MyTestDevice] - ✅ Device registered successfully!
2025-07-04 10:30:15,457 - INFO - [NewMQTT-MyTestDevice] - 🔌 Connecting to MQTT broker at localhost:1883
2025-07-04 10:30:15,567 - INFO - [NewMQTT-MyTestDevice] - 🔌 Connected to MQTT broker at localhost:1883
2025-07-04 10:30:15,678 - INFO - [NewMQTT-MyTestDevice] - 💓 Heartbeat sent - Uptime: 1s
2025-07-04 10:30:45,789 - INFO - [NewMQTT-MyTestDevice] - 📊 Telemetry sent - Temp: 24.5°C, Battery: 99.9%
```
