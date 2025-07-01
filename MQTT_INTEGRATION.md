# MQTT Integration for IoTFlow

This document describes the MQTT integration implementation for the IoT Connectivity Layer, providing real-time device communication capabilities.

## 🏗️ Architecture Overview

The MQTT integration adds a publish/subscribe messaging layer to IoTFlow, enabling:

- **Real-time device communication** via MQTT protocol
- **Secure authentication** with username/password and ACL
- **Hierarchical topic structure** for organized message routing
- **Quality of Service (QoS)** levels for reliable message delivery
- **TLS/SSL encryption** for secure connections (production)

```
IoT Devices ←→ MQTT Broker ←→ IoTFlow API Server ←→ PostgreSQL Database
     ↑              ↑                    ↑
   MQTT          Eclipse              REST API
 Protocol       Mosquitto           (Flask App)
```

## 📋 Phase 1 Implementation Status

### ✅ Completed Features

1. **MQTT Broker Setup**
   - Eclipse Mosquitto 2.0 integration via Docker
   - Multi-port configuration (1883, 8883, 9001)
   - Persistent data storage
   - Health checks and monitoring

2. **Security Configuration**
   - Username/password authentication
   - Access Control Lists (ACL) for topic permissions
   - Rate limiting and connection controls
   - TLS/SSL support (configurable)

3. **Topic Architecture**
   - Hierarchical topic structure (`iotflow/devices/{device_id}/...`)
   - Device-specific topics (telemetry, commands, status)
   - Fleet management topics
   - System and monitoring topics
   - Wildcard subscription patterns

4. **MQTT Client Service**
   - Robust connection management with auto-reconnect
   - Message routing and handling
   - Callback system for telemetry, commands, and status
   - Comprehensive error handling and logging

5. **REST API Integration**
   - MQTT management endpoints
   - Device command publishing
   - Fleet command broadcasting
   - Topic validation and monitoring

6. **Management Tools**
   - `mqtt_manage.sh` script for broker administration
   - User credential management
   - Device credential generation
   - Backup and monitoring utilities

## 🚀 Quick Start

### 1. Start MQTT Broker

```bash
# Setup and start the MQTT broker
./mqtt_manage.sh setup

# Setup admin user (default password: admin123)
./mqtt_manage.sh setup-admin

# Check broker status
./mqtt_manage.sh status
```

### 2. Generate Device Credentials

```bash
# Generate credentials for a device
./mqtt_manage.sh generate-device sensor_001

# This creates username/password for the device
# and saves credentials to device_credentials_sensor_001.txt
```

### 3. Test MQTT Connection

```bash
# Test connection with admin credentials
./mqtt_manage.sh test admin admin123
```

### 4. Start the IoTFlow Application

```bash
# Copy environment configuration
cp .env.example .env

# Start the application (MQTT will auto-connect)
python app.py
```

## 📡 Topic Structure

The MQTT topics follow a hierarchical structure under the base topic `iotflow/`:

### Device Topics

```
iotflow/devices/{device_id}/
├── telemetry/
│   ├── sensors/     # Sensor readings (temperature, humidity, etc.)
│   ├── metrics/     # Device performance metrics
│   └── events/      # Device events and alerts
├── commands/
│   ├── config/      # Configuration commands
│   ├── control/     # Control commands (start, stop, etc.)
│   └── firmware/    # Firmware update commands
├── status/
│   ├── heartbeat    # Regular heartbeat messages
│   ├── online       # Device online status
│   └── offline      # Device offline status
└── config/          # Device configuration settings
```

### System Topics

```
iotflow/
├── fleet/
│   ├── commands/{group_id}  # Fleet-wide commands
│   └── status/{group_id}    # Fleet status updates
├── system/
│   ├── health/              # System health status
│   ├── metrics/             # System metrics
│   └── alerts/              # System alerts
├── discovery/
│   ├── register/{device_id} # Device registration
│   └── response/{device_id} # Registration responses
└── monitoring/
    ├── broker/              # Broker monitoring
    ├── clients/             # Client monitoring
    └── traffic/             # Traffic monitoring
```

## 🔐 Security Features

### Authentication

- **Username/Password**: Each device has unique credentials
- **Client ID**: Devices use their device ID as client identifier
- **ACL Control**: Topic-level access permissions

### Access Control Rules

- Devices can only access their own topics (`iotflow/devices/{device_id}/...`)
- Admin users have full access to all topics
- System topics are admin-only
- Pattern-based permissions using client ID substitution

### TLS/SSL (Production)

```bash
# Enable TLS in environment configuration
MQTT_USE_TLS=true
MQTT_CA_CERT_PATH=/path/to/ca.crt
MQTT_CERT_FILE_PATH=/path/to/server.crt
MQTT_KEY_FILE_PATH=/path/to/server.key
```

## 🔧 API Endpoints

### MQTT Management

- `GET /api/v1/mqtt/status` - Get MQTT broker status
- `POST /api/v1/mqtt/publish` - Publish message to broker
- `POST /api/v1/mqtt/subscribe` - Subscribe to topic (admin)
- `GET /api/v1/mqtt/topics/structure` - Get topic structure
- `POST /api/v1/mqtt/topics/validate` - Validate topic

### Device Communication

- `POST /api/v1/mqtt/device/{device_id}/command` - Send device command
- `GET /api/v1/mqtt/topics/device/{device_id}` - Get device topics
- `POST /api/v1/mqtt/fleet/{group_id}/command` - Send fleet command

### Monitoring

- `GET /api/v1/mqtt/monitoring/metrics` - Get MQTT metrics (admin)

## 💾 Message Examples

### Device Telemetry

```json
// Topic: iotflow/devices/sensor_001/telemetry/sensors
{
  "temperature": 23.5,
  "humidity": 65.2,
  "pressure": 1013.25,
  "timestamp": "2025-07-01T10:30:00Z",
  "device_id": "sensor_001"
}
```

### Device Command

```json
// Topic: iotflow/devices/sensor_001/commands/config
{
  "command": "update_interval",
  "parameters": {
    "interval_seconds": 30
  },
  "command_id": "cmd_12345",
  "timestamp": "2025-07-01T10:30:00Z"
}
```

### Device Status

```json
// Topic: iotflow/devices/sensor_001/status/heartbeat
{
  "status": "online",
  "uptime": 86400,
  "battery_level": 95,
  "signal_strength": -45,
  "timestamp": "2025-07-01T10:30:00Z"
}
```

## 🛠️ Management Commands

### Broker Management

```bash
# Start/stop/restart broker
./mqtt_manage.sh start
./mqtt_manage.sh stop
./mqtt_manage.sh restart

# Monitor logs
./mqtt_manage.sh logs

# Check status
./mqtt_manage.sh status
```

### User Management

```bash
# Create user
./mqtt_manage.sh create-user device001 secretpassword

# Delete user
./mqtt_manage.sh delete-user device001

# List users
./mqtt_manage.sh list-users

# Generate device credentials
./mqtt_manage.sh generate-device my_sensor
```

### Backup and Maintenance

```bash
# Backup configuration
./mqtt_manage.sh backup

# Test connection
./mqtt_manage.sh test admin admin123
```

## 📊 Quality of Service (QoS) Levels

Different message types use appropriate QoS levels:

- **QoS 0** (At most once): Heartbeat messages, non-critical telemetry
- **QoS 1** (At least once): Sensor data, status updates, alerts
- **QoS 2** (Exactly once): Critical commands, configuration changes

## 🔍 Monitoring and Troubleshooting

### Health Checks

The broker includes health checks accessible via:

```bash
# Docker health check
docker ps | grep iotflow_mosquitto

# Manual health test
./mqtt_manage.sh test
```

### Log Monitoring

```bash
# Real-time logs
./mqtt_manage.sh logs

# Application logs
tail -f logs/iotflow.log
```

### Common Issues

1. **Connection Refused**: Check if broker is running and ports are open
2. **Authentication Failed**: Verify username/password in password file
3. **Permission Denied**: Check ACL configuration for topic access
4. **SSL/TLS Issues**: Verify certificate paths and configurations

## 🔮 Next Steps (Phase 2 & 3)

### Planned Enhancements

1. **Advanced Security**
   - Client certificate authentication
   - JWT token integration
   - Rate limiting per client

2. **Message Persistence**
   - Database integration for telemetry storage
   - Message queuing for offline devices
   - Historical data retention policies

3. **Monitoring & Analytics**
   - Real-time dashboards
   - Message flow visualization
   - Performance metrics and alerting

4. **Device Management**
   - Auto-discovery and provisioning
   - Firmware update orchestration
   - Device grouping and fleet management

## 📚 References

- [Eclipse Mosquitto Documentation](https://mosquitto.org/documentation/)
- [MQTT Protocol Specification](https://mqtt.org/mqtt-specification/)
- [Paho MQTT Python Client](https://eclipse.org/paho/clients/python/)
- [IoTFlow API Documentation](../README.md)
