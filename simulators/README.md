# IoT Device Simulator - Quick Start Guide

## 🚀 **Phase 1 Complete: Simple Device Simulator**

Your IoT device simulators are ready! Here's how to use them:

## **Quick Start Options**

### **Option 1: Interactive Mode (Recommended)**

```bash
cd simulators
python3 simulate.py --interactive
```

### **Option 2: Single Device Test**

```bash
# Basic sensor device
python3 basic_device_simulator.py --duration 120 --telemetry-interval 20

# Specific device types
python3 device_types.py --device-type temperature --duration 120
python3 device_types.py --device-type door_lock --duration 120
python3 device_types.py --device-type camera --duration 120
```

### **Option 3: Fleet Simulation**

```bash
# Home setup (9 devices)
python3 fleet_simulator.py --preset home --duration 300

# Office setup (16 devices)
python3 fleet_simulator.py --preset office --duration 300

# Custom fleet
python3 fleet_simulator.py --preset custom --temperature-sensors 3 --cameras 2
```

## **Device Types Available**

### **1. Basic Sensor Device**

- **Data**: Temperature, humidity, pressure, battery, signal
- **Pattern**: Daily temperature cycles (18-35°C)
- **Features**: Network failure simulation, battery drain

### **2. Temperature Sensor**

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

```bash
# 3-minute temperature sensor test
python3 device_types.py --device-type temperature --duration 180 --interval 20

# 5-minute home fleet simulation
python3 fleet_simulator.py --preset home --duration 300 --telemetry-interval 30

# Custom device with specific name
python3 basic_device_simulator.py --name "MyTestDevice" --duration 120
```

### **Load Testing**

```bash
# Factory simulation for 10 minutes (30 devices)
python3 fleet_simulator.py --preset factory --duration 600 --telemetry-interval 30

# High-frequency data collection
python3 basic_device_simulator.py --telemetry-interval 10 --duration 300
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

### **3. Monitor Telemetry Data**

```bash
curl -s "http://localhost:5000/api/v1/admin/telemetry?limit=10" | python3 -m json.tool
```

### **4. Dashboard Statistics**

```bash
curl -s "http://localhost:5000/api/v1/admin/dashboard" | python3 -m json.tool
```

## **Real-Time Monitoring**

While simulations are running, you can monitor:

- **Device count**: Total registered devices
- **Online devices**: Currently active devices
- **Telemetry rate**: Data points per minute
- **System health**: Database and Redis status
- **Rate limiting**: API request patterns

## **Next Steps**

Your **Phase 1** implementation is complete! Ready for:

- **Phase 2**: Advanced Device Behaviors & Fleet Management
- **Phase 3**: Hardware Integration (Raspberry Pi, Arduino)
- **Phase 4**: Real-time Dashboard & Analytics

## **Troubleshooting**

### **"Cannot connect to service"**

1. Start Docker services: `./docker-manage.sh start`
2. Start Flask app: `poetry run python app.py`
3. Check health: `curl http://localhost:5000/health`

### **"Registration failed"**

- Check if device name already exists
- Verify service is running
- Check network connectivity

### **"Rate limit exceeded"**

- This is normal and expected!
- Rate limiting is working correctly
- Devices will automatically retry

---

**🎉 Phase 1 Complete! Your IoT device simulators are ready to test your connectivity layer.**
