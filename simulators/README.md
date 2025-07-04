# IoT Device Simulators - Production Ready

## 🚀 **Advanced MQTT Device Simulator**

A comprehensive, production-ready MQTT device simulator with advanced features for the IoTFlow platform.

## **Quick Start**

### **Basic Usage**

```bash
# Run with default settings
poetry run python new_mqtt_device_simulator.py --name MyTestDevice

# Run for specific duration
poetry run python new_mqtt_device_simulator.py --name MyDevice --duration 600
```

### **Simulation Profiles**

Choose from 4 pre-configured profiles:

```bash
# Default profile (standard sensor)
poetry run python new_mqtt_device_simulator.py --name StandardSensor --profile default

# High-frequency motion sensor
poetry run python new_mqtt_device_simulator.py \
    --name MotionSensor001 \
    --type motion_sensor \
    --profile high_frequency \
    --duration 1800

# Energy-efficient environmental sensor
poetry run python new_mqtt_device_simulator.py \
    --name EnvSensor001 \
    --type environmental_sensor \
    --profile energy_efficient \
    --duration 3600

# Industrial sensor with vibration monitoring
poetry run python new_mqtt_device_simulator.py \
    --name IndustrialSensor001 \
    --type industrial_sensor \
    --profile industrial \
    --duration 1800
```

## **Advanced Features**

### **1. Comprehensive Device Types**

- **smart_sensor** - Standard IoT sensor (default)
- **industrial_sensor** - Industrial monitoring device
- **environmental_sensor** - Environmental monitoring
- **motion_sensor** - Motion and acceleration detection
- **energy_meter** - Power consumption monitoring

- **Data**: Temperature, humidity, location status
- **Pattern**: Indoor vs outdoor temperature patterns
- **Locations**: Indoor, Outdoor, Greenhouse, Server Room

### **3. Smart Door Lock**

- **Data**: Lock status, access events, attempt counter
- **Pattern**: More activity during day hours
- **Events**: Lock/unlock, status checks, access attempts

### **4. Security Camera**

- **Data**: Motion detection, recording status, storage usage
- **Pattern**: Peak motion during rush hours, less at night
- **Features**: Night vision mode, storage tracking

### **5. Air Quality Monitor**

- **Data**: PM2.5, CO2, temperature, humidity, AQI
- **Pattern**: PM2.5 peaks during rush hours
- **Features**: Air quality index calculation

### **6. Smart Thermostat**

- **Data**: Current/target temperature, mode, energy usage
- **Pattern**: Scheduled temperature control
- **Features**: Auto heating/cooling, energy monitoring

## **Simulation Features**

### **✅ Device Registration Workflow**

- Automatic device registration with unique API keys
- Device ID and API key management
- Registration failure handling

### **✅ Authentication & Security**

- API key-based authentication
- Secure headers (X-API-Key)
- Rate limiting compliance

### **✅ Periodic Heartbeat**

- Configurable heartbeat intervals (default: 60s)
- Online/offline status tracking
- Automatic reconnection on failures

### **✅ Realistic Data Patterns**

- Daily temperature cycles based on time of day
- Activity patterns (more motion during peak hours)
- Seasonal and environmental variations

### **✅ Network Failure Simulation**

- Random connection drops (5% failure rate)
- Automatic retry logic
- Graceful error handling

### **✅ Battery Level Simulation**

- Gradual battery drain over time
- Battery level reporting in telemetry
- Power management simulation

### **✅ Configurable Intervals**

- Telemetry: 20s - 300s (customizable per device)
- Heartbeat: 60s - 300s
- Device-specific optimized intervals

## **Fleet Presets**

### **🏠 Home Setup (9 devices)**

- 3x Temperature sensors (indoor/outdoor)
- 2x Smart door locks (front/back)
- 2x Security cameras (yard/driveway)
- 1x Air quality monitor
- 1x Smart thermostat

### **🏢 Office Setup (16 devices)**

- 5x Temperature sensors (multiple rooms)
- 3x Smart door locks (entrances)
- 4x Security cameras (comprehensive coverage)
- 2x Air quality monitors
- 2x Smart thermostats (zone control)

### **🏭 Factory Setup (30 devices)**

- 10x Temperature sensors (multiple zones)
- 5x Smart door locks (security doors)
- 8x Security cameras (full coverage)
- 4x Air quality monitors (environmental)
- 3x Smart thermostats (large zone control)

## **Command Examples**

### **Quick Device Tests**

## **Testing Examples**

### **Quick Tests**

```bash
# 2-minute default sensor test
poetry run python new_mqtt_device_simulator.py --name QuickTest --duration 120

# High-frequency motion sensor test
poetry run python new_mqtt_device_simulator.py \
    --name MotionTest \
    --type motion_sensor \
    --profile high_frequency \
    --duration 180

# Energy-efficient long-running test
poetry run python new_mqtt_device_simulator.py \
    --name LongRunTest \
    --profile energy_efficient \
    --duration 3600
```

### **Load Testing**

```bash
# Multiple devices (run in separate terminals)
poetry run python new_mqtt_device_simulator.py --name Device001 --duration 600 &
poetry run python new_mqtt_device_simulator.py --name Device002 --duration 600 &
poetry run python new_mqtt_device_simulator.py --name Device003 --duration 600 &

# High-frequency industrial sensors
poetry run python new_mqtt_device_simulator.py \
    --name IndustrialSensor001 \
    --type industrial_sensor \
    --profile industrial \
    --duration 1800
```

## **Monitoring Your Simulations**

### **1. Check Device Registration**

```bash
curl -s "http://localhost:5000/api/v1/admin/devices" | python3 -m json.tool
```

### **2. View System Health**

```bash
curl -s "http://localhost:5000/health?detailed=true" | python3 -m json.tool
```

### **3. Monitor MQTT Activity**

```bash
# Monitor specific device
../scripts/monitor_mqtt.sh -d MyTestDevice

# Monitor all devices
../scripts/monitor_mqtt.sh -a

# Send commands
poetry run python ../scripts/send_device_command.py -d MyTestDevice -c get_status
```

### **2. Simulation Profiles**

- **Default**: temperature, humidity, pressure, battery (30s/60s intervals)
- **High Frequency**: includes accelerometer/gyroscope (5s/30s intervals)
- **Energy Efficient**: minimal telemetry for battery preservation (5min/10min intervals)
- **Industrial**: vibration and power monitoring (10s/30s intervals)

### **3. Realistic Telemetry Generation**

- **Temperature**: Daily cycles with realistic variations
- **Humidity**: Correlated with temperature
- **Battery**: Gradual drain based on profile
- **Motion**: Accelerometer and gyroscope data
- **Industrial**: Vibration and power consumption

### **4. Command & Control**

Remote command support via MQTT:

```bash
# Send commands using the utility script
poetry run python ../scripts/send_device_command.py -d MyDevice -c restart
poetry run python ../scripts/send_device_command.py -d MyDevice -c get_status
poetry run python ../scripts/send_device_command.py -d MyDevice -c update_interval --interval 10
```

## **Monitoring & Testing**

### **Monitor MQTT Topics**

```bash
# Monitor all topics for a device
../scripts/monitor_mqtt.sh -d MyTestDevice

# Monitor all device activity
../scripts/monitor_mqtt.sh -a

# Using mosquitto_sub directly
mosquitto_sub -h localhost -p 1883 -t "devices/MyTestDevice/+" -v
```

### **MQTT Topics Structure**

- `devices/{name}/telemetry` - Sensor data
- `devices/{name}/heartbeat` - Device health status
- `devices/{name}/status` - Status updates and command responses
- `devices/{name}/commands` - Remote commands (subscribe)
- `devices/{name}/config` - Configuration updates (subscribe)
- `devices/{name}/errors` - Error reports

## **Integration with IoTFlow**

### **1. HTTP Device Registration**
- Automatically registers with `/api/v1/devices/register`
- Receives device ID and API key for authentication

### **2. MQTT Authentication**
- Uses device ID and API key for secure MQTT connection
- Follows IoTFlow's authentication protocol

### **3. Data Flow**
- Telemetry → MQTT → IoTFlow → IoTDB
- Heartbeat and status monitoring
- Command handling and responses

## **Example Output**

```
2025-07-04 10:30:15,123 - INFO - [NewMQTT-MyTestDevice] - 🔧 Loaded simulation profile: default
2025-07-04 10:30:15,124 - INFO - [NewMQTT-MyTestDevice] - 🔗 Registering device: MyTestDevice
2025-07-04 10:30:15,456 - INFO - [NewMQTT-MyTestDevice] - ✅ Device registered successfully!
2025-07-04 10:30:15,457 - INFO - [NewMQTT-MyTestDevice] - 🔌 Connected to MQTT broker at localhost:1883
2025-07-04 10:30:15,678 - INFO - [NewMQTT-MyTestDevice] - 💓 Heartbeat sent - Uptime: 1s
2025-07-04 10:30:45,789 - INFO - [NewMQTT-MyTestDevice] - 📊 Telemetry sent - Temp: 24.5°C, Battery: 99.9%
```

## **Requirements**

- IoTFlow service running (`poetry run python app.py`)
- MQTT broker active (included in docker-compose)
- Python packages: `paho-mqtt`, `requests` (included in pyproject.toml)

## **Troubleshooting**

### **"Cannot connect to IoTFlow service"**

1. Start Docker services: `./docker-manage.sh start`
2. Start Flask app: `poetry run python app.py`
3. Check health: `curl http://localhost:5000/health`

### **"Device name already exists"**

- Use a different device name
- Each device name must be unique in the system

### **"MQTT connection failed"**

- Ensure device registration was successful
- Check MQTT broker is running (docker-compose)
- Verify network connectivity

### **"Command not working"**

- Ensure device is running and connected
- Check MQTT topic names are correct
- Monitor with `mosquitto_sub` to verify message flow

## **File Structure**

```
simulators/
├── new_mqtt_device_simulator.py    # Main advanced simulator
├── NEW_MQTT_SIMULATOR.md          # Detailed documentation
└── README.md                      # This file
```

---

**🎉 Production-Ready MQTT Device Simulator!**

For detailed documentation, see [`NEW_MQTT_SIMULATOR.md`](NEW_MQTT_SIMULATOR.md)
