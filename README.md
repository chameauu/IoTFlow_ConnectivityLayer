# IoTFlow - IoT Device Connectivity Layer

A modern, production-ready IoT platform built with Python Flask for comprehensive device connectivity, telemetry data collection, and real-time analytics. Clean, modernized codebase with advanced MQTT device simulation and robust data storage.

![IoT Platform](https://img.shields.io/badge/Platform-IoT-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-orange)
![IoTDB](https://img.shields.io/badge/Database-IoTDB-yellow)
![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)

## 🚀 Features

### Core Capabilities
- **🔌 Device Management**: Complete device lifecycle with secure API key authentication
- **💾 Hybrid Data Storage**: SQLite for device metadata + IoTDB for time-series telemetry  
- **📡 Multi-Protocol Support**: HTTP REST API + MQTT pub/sub messaging
- **⚡ Real-time Analytics**: Advanced time-series queries, aggregations, and dashboards
- **🛡️ Enterprise Security**: API key authentication, rate limiting, and secure endpoints
- **📈 Scalable Architecture**: Redis caching, background processing, containerized services
- **🧪 Advanced Testing**: Production-ready device simulators and testing framework

### Production Features
- **🔍 Time-Series Analytics**: Complex IoTDB queries with filtering and aggregation
- **🤖 Smart Device Simulation**: Advanced MQTT simulator with realistic device behavior
- **📋 Admin Dashboard**: Complete device and telemetry management interface
- **📚 Modern Development**: Poetry dependency management and development workflow
- **🐳 Containerized Deployment**: Full Docker Compose development and production environment
- **📊 Comprehensive Monitoring**: Structured logging, metrics, health checks, and debugging tools

### Recent Improvements (v0.2)
- **✨ Cleaned up simulator environment** - Removed all legacy simulators, single advanced simulator
- **🔧 Enhanced device registration** - Smart handling of existing devices, auto-suffix options
- **📈 Improved error handling** - Better debugging and diagnostic capabilities
- **🔍 Enhanced data retrieval** - Comprehensive IoTDB data query and export tools
- **📝 Production documentation** - Complete setup, testing, and troubleshooting guides

## 🏗️ Architecture

```
    IoT Devices (HTTP/MQTT)
           ↓
    ┌─────────────────────────┐
    │   Load Balancer/Proxy   │
    └─────────────┬───────────┘
                  ↓
    ┌─────────────────────────┐
    │    Flask Application    │
    │   (REST API + MQTT)     │
    └─────────┬─────────┬─────┘
              ↓         ↓
    ┌─────────────┐   ┌──────────────┐
    │   SQLite    │   │    IoTDB     │
    │ (Devices)   │   │ (Telemetry)  │
    └─────────────┘   └──────────────┘
              ↓
    ┌─────────────────────────┐
    │   Redis (Cache/Queue)   │
    │   MQTT Broker           │
    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** 
- **Poetry** (recommended) or pip
- **Docker & Docker Compose**
- **Git**

### 1. Clone and Setup

```bash
git clone <repository-url>
cd IoTFlow_ConnectivityLayer

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional - defaults work for development)
nano .env
```

### 3. Start Services & Initialize

```bash
# Start all services (Redis, IoTDB, MQTT)
./docker-manage.sh start-all

# Initialize Python environment and database
./docker-manage.sh init-app

# Start Flask application
./docker-manage.sh run
```

### 4. Verify Installation

```bash
# Check service health
curl http://localhost:5000/health

# Run comprehensive tests
./docker-manage.sh test
```

## 🎮 Device Simulation & Testing

### 🤖 Advanced MQTT Device Simulator (v0.2)

The platform now includes a single, production-ready MQTT device simulator that replaces all legacy simulators. This advanced simulator provides realistic device behavior with multiple simulation profiles.

#### Quick Start Examples

```bash
# Basic smart sensor (default profile, 5 minutes)
poetry run python simulators/new_mqtt_device_simulator.py --name MyTestDevice

# High-frequency sensor (data every 5 seconds)
poetry run python simulators/new_mqtt_device_simulator.py \
    --name HighFreqSensor \
    --profile high_frequency \
    --duration 600

# Industrial sensor with comprehensive telemetry
poetry run python simulators/new_mqtt_device_simulator.py \
    --name IndustrialSensor001 \
    --type industrial_sensor \
    --profile industrial \
    --duration 1800

# Energy-efficient device (data every 5 minutes)
poetry run python simulators/new_mqtt_device_simulator.py \
    --name LowPowerSensor \
    --profile energy_efficient \
    --duration 3600
```

#### Advanced Options

```bash
# Handle existing device names automatically
poetry run python simulators/new_mqtt_device_simulator.py \
    --name ExistingDevice \
    --auto-suffix            # Adds _1, _2, etc. if name exists

# Force re-registration (use with caution)
poetry run python simulators/new_mqtt_device_simulator.py \
    --name ExistingDevice \
    --force-register

# Custom connection settings
poetry run python simulators/new_mqtt_device_simulator.py \
    --name RemoteDevice \
    --host remote-iot-server.com \
    --mqtt-port 1883 \
    --http-port 5000
```

#### Simulation Profiles

| Profile | Telemetry Interval | Data Types | Battery Drain | Use Case |
|---------|-------------------|------------|---------------|----------|
| `default` | 30 seconds | temperature, humidity, pressure, battery | 0.1%/hour | General IoT sensors |
| `high_frequency` | 5 seconds | temperature, humidity, pressure, accelerometer, gyroscope | 0.5%/hour | Motion/vibration sensors |
| `energy_efficient` | 5 minutes | temperature, battery | 0.05%/hour | Long-term deployment |
| `industrial` | 10 seconds | temperature, pressure, vibration, power_consumption | 0.3%/hour | Industrial monitoring |

#### Smart Registration Features

- **Existing Device Detection**: Automatically checks if device name already exists
- **Graceful Handling**: Provides clear guidance when device conflicts occur
- **Auto-suffix Option**: Automatically appends numbers to device names (e.g., `MyDevice_1`)
- **Force Registration**: Option to attempt re-registration of existing devices

### 🧪 Testing & Validation

#### End-to-End Testing
```bash
# Complete platform test
./docker-manage.sh test

# Test device registration and data flow
poetry run python scripts/test_esp32_registration.py

# Monitor device data in real-time
poetry run python scripts/monitor_device_data.py --device TestDevice
```

#### Data Verification
```bash
# Check IoTDB data storage
poetry run python scripts/retrieve_iotdb_data.py --list-devices
poetry run python scripts/retrieve_iotdb_data.py --device 5 --latest --limit 20

# Verify MQTT messaging
./scripts/monitor_mqtt.sh
```
## 📡 API Endpoints

The IoTFlow platform provides a comprehensive API for device management, telemetry data handling, administration, and system monitoring. The APIs follow RESTful principles and use the following authentication mechanisms:

- **No Authentication**: Public endpoints like health checks and device registration
- **API Key**: Device-specific endpoints requiring the `X-API-Key` header
- **Admin Token**: Administrative endpoints requiring `Authorization: admin <TOKEN>` header

### 🔌 Device Management

| Method | Endpoint                    | Description                    | Auth Required |
|--------|----------------------------|--------------------------------|---------------|
| POST   | `/api/v1/devices/register` | Register new device            | None          |
| GET    | `/api/v1/devices/status`   | Get device status & health     | API Key       |
| POST   | `/api/v1/devices/heartbeat`| Send device heartbeat          | API Key       |
| PUT    | `/api/v1/devices/config`   | Update device configuration    | API Key       |
| GET    | `/api/v1/devices/config`   | Get device configuration       | API Key       |
| GET    | `/api/v1/devices/mqtt-credentials` | Get MQTT connection credentials | API Key |
| GET    | `/api/v1/devices/statuses` | Get all device statuses        | None          |

### 📊 Telemetry & Data

| Method | Endpoint                           | Description                    | Auth Required |
|--------|------------------------------------|--------------------------------|---------------|
| POST   | `/api/v1/devices/telemetry`       | Submit telemetry data via HTTP  | API Key       |
| GET    | `/api/v1/devices/telemetry`       | Get device's own telemetry      | API Key       |
| POST   | `/api/v1/telemetry`               | Submit telemetry data          | API Key       |
| GET    | `/api/v1/telemetry/{device_id}`   | Get device telemetry history   | API Key*      |
| GET    | `/api/v1/telemetry/{device_id}/latest` | Get latest telemetry      | API Key*      |
| GET    | `/api/v1/telemetry/{device_id}/aggregated` | Get aggregated data   | API Key*      |
| DELETE | `/api/v1/telemetry/{device_id}`   | Delete device telemetry        | API Key*      |
| GET    | `/api/v1/telemetry/status`        | Get telemetry system status    | None          |

### 📡 MQTT Management

| Method | Endpoint                           | Description                    | Auth Required |
|--------|------------------------------------|--------------------------------|---------------|
| GET    | `/api/v1/mqtt/status`             | Get MQTT broker status         | None          |
| GET    | `/api/v1/mqtt/monitoring/metrics` | Get MQTT monitoring metrics    | None          |
| POST   | `/api/v1/mqtt/telemetry/{device_id}` | Submit telemetry via MQTT REST proxy | API Key |

### 🛠️ Administration

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| GET    | `/api/v1/admin/devices`       | List all devices            | Admin         |
| GET    | `/api/v1/admin/devices/{id}`  | Get device details          | Admin         |
| PUT    | `/api/v1/admin/devices/{id}`  | Update device               | Admin         |
| DELETE | `/api/v1/admin/devices/{id}`  | Delete device               | Admin         |
| PUT    | `/api/v1/admin/devices/{id}/status` | Update device status  | Admin         |
| GET    | `/api/v1/admin/stats`         | Get system statistics       | Admin         |
| GET    | `/api/v1/admin/cache/device-status` | Get device cache stats | Admin        |
| DELETE | `/api/v1/admin/cache/device-status` | Clear all device cache | Admin        |
| DELETE | `/api/v1/admin/cache/devices/{id}` | Clear specific device cache | Admin     |

### 🔍 System Health

| Method | Endpoint              | Description              | Auth Required |
|--------|-----------------------|--------------------------|---------------|
| GET    | `/health`             | API health check         | None          |
| GET    | `/api/v1/telemetry/status` | Telemetry system status | None      |

\* API Key required if accessing own device data; Admin token required for other devices

## 💡 Usage Examples

### Register a Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Temperature Sensor 001",
    "description": "Living room environmental sensor",
    "device_type": "temperature_sensor",
    "location": "Living Room",
    "firmware_version": "1.2.3",
    "hardware_version": "v2.1"
  }'
```

**Response:**
```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "Smart Temperature Sensor 001",
    "api_key": "rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB",
    "status": "active",
    "device_type": "temperature_sensor",
    "created_at": "2025-07-02T14:30:00Z"
  }
}
```

### Submit Telemetry Data

```bash
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 23.5,
      "humidity": 65.2,
      "pressure": 1013.25,
      "battery_level": 87,
      "signal_strength": -52
    },
    "metadata": {
      "location": "Living Room",
      "sensor_status": "active"
    },
    "timestamp": "2025-07-02T14:30:00Z"
  }'
```

### Query Telemetry Data

```bash
# Get latest telemetry
curl "http://localhost:5000/api/v1/telemetry/1/latest" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get historical data with filters
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-1h&limit=100" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get aggregated data (hourly averages)
curl "http://localhost:5000/api/v1/telemetry/1/aggregated?window=1h&start_time=-24h&field=temperature&aggregation=mean" \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"

# Get telemetry system status
curl "http://localhost:5000/api/v1/telemetry/status"
```

### Device Heartbeat

```bash
curl -X POST http://localhost:5000/api/v1/devices/heartbeat \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"
```

### MQTT Management

```bash
# Check MQTT service status
curl "http://localhost:5000/api/v1/mqtt/status"

# Get MQTT metrics
curl "http://localhost:5000/api/v1/mqtt/monitoring/metrics"

# Submit telemetry via MQTT REST proxy
curl -X POST http://localhost:5000/api/v1/mqtt/telemetry/1 \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 24.5,
      "humidity": 62.0
    },
    "timestamp": "2025-07-07T10:15:30Z"
  }'
```

### Administration APIs

```bash
# Get admin token from environment (for example purposes)
ADMIN_TOKEN="test"

# List all devices
curl "http://localhost:5000/api/v1/admin/devices" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Get detailed device information
curl "http://localhost:5000/api/v1/admin/devices/1" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Update device status
curl -X PUT "http://localhost:5000/api/v1/admin/devices/1/status" \
  -H "Authorization: admin ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "maintenance"
  }'

# Get system statistics
curl "http://localhost:5000/api/v1/admin/stats" \
  -H "Authorization: admin ${ADMIN_TOKEN}"

# Clear device cache
curl -X DELETE "http://localhost:5000/api/v1/admin/cache/devices/1" \
  -H "Authorization: admin ${ADMIN_TOKEN}"
```
## 🗃️ Data Architecture

### SQLite Database (Device Management)

**Devices Table:**
- `id` - Primary key
- `name` - Unique device identifier  
- `description` - Device description
- `device_type` - Category (sensor, actuator, camera, etc.)
- `api_key` - Unique authentication key (32 chars)
- `status` - Device status (active, inactive, maintenance)
- `location` - Physical location
- `firmware_version` - Current firmware version
- `hardware_version` - Hardware revision
- `created_at` - Registration timestamp
- `updated_at` - Last modification
- `last_seen` - Last heartbeat/activity

### IoTDB (Time-Series Telemetry)

**Time Series Structure:**
- **Storage Groups**: `root.iotflow.{device_id}`
- **Measurements**: Device data fields (temperature, humidity, etc.)
- **Data Types**: INT32, INT64, FLOAT, DOUBLE, TEXT, BOOLEAN
- **Timestamp**: Precise time-series indexing

## 🛠️ Development & Management

### Project Structure

```
IoTFlow_ConnectivityLayer/
├── 📁 src/                          # Core application code
│   ├── config/                      # Configuration management
│   │   ├── config.py               # Flask & database config
│   │   └── iotdb_config.py         # IoTDB configuration
│   ├── models/                      # SQLAlchemy database models
│   ├── routes/                      # API route handlers
│   │   ├── devices.py              # Device management endpoints
│   │   ├── telemetry.py            # Telemetry data endpoints
│   │   └── admin.py                # Administrative endpoints
│   ├── services/                    # Business logic services
│   │   └── iotdb.py                # IoTDB service layer
│   ├── middleware/                  # Request/response middleware
│   │   ├── auth.py                 # Authentication & authorization
│   │   ├── security.py             # Security utilities
│   │   └── monitoring.py           # Performance monitoring
│   └── utils/                       # Utility functions
│       └── logging.py              # Logging configuration
├── 📁 simulators/                   # Device simulation & testing
│   ├── new_mqtt_device_simulator.py # Advanced MQTT device simulator
│   ├── NEW_MQTT_SIMULATOR.md       # Detailed simulator documentation
│   └── README.md                   # Simulator usage guide
├── 📁 mqtt/                         # MQTT broker configuration
│   └── config/                     # Mosquitto configuration files
├── 📁 tests/                        # Test suites (unit & integration)
├── 🐳 docker-compose.yml            # Container orchestration
├── 🔧 docker-manage.sh              # Docker management script
├── 🔧 manage.py                     # Python management script
├── 📦 pyproject.toml                # Poetry dependencies
├── 📄 .env                          # Environment configuration
└── 📚 Documentation/                # Comprehensive docs
    ├── MANAGEMENT_GUIDE.md         # Management & deployment guide
    ├── HTTP_SIMULATION_TEST_RESULTS.md  # Testing results
    └── iotdb_integration.md        # Architecture docs
```

### Management Commands

#### Docker Management Script (`./docker-manage.sh`)

```bash
# Complete setup workflow
./docker-manage.sh start-all     # Start all services
./docker-manage.sh init-app      # Initialize environment & database
./docker-manage.sh run           # Start Flask application

# Development workflow
./docker-manage.sh status        # Check service status
./docker-manage.sh logs          # View logs
./docker-manage.sh logs iotdb # View specific service logs

# Data management
./docker-manage.sh backup        # Backup SQLite database
./docker-manage.sh restore backup_file.db  # Restore from backup
./docker-manage.sh reset         # Reset all data (CAUTION!)

# Database connections
./docker-manage.sh redis         # Connect to Redis CLI
./docker-manage.sh iotdb         # Connect to IoTDB CLI
```

#### Python Management Script (`manage.py`)

```bash
# Database operations
poetry run python manage.py init-db                    # Initialize database
poetry run python manage.py create-device "My Device" # Create test device

# Application operations  
poetry run python manage.py run                        # Start Flask app
poetry run python manage.py test                       # Run test suite
poetry run python manage.py shell                      # Interactive Python shell
```

### Testing & Simulation

#### Comprehensive Test Suite

```bash
# Run all tests
poetry run python manage.py test

# Specific test categories
poetry run pytest tests/unit/ -v           # Unit tests
poetry run pytest tests/integration/ -v    # Integration tests
poetry run pytest tests/api/ -v            # API endpoint tests
```

#### Device Simulation Options

```bash
# Advanced MQTT device simulator with profiles
poetry run python simulators/new_mqtt_device_simulator.py --name TestDevice

# Different device types and profiles
poetry run python simulators/new_mqtt_device_simulator.py \
    --name IndustrialSensor --type industrial_sensor --profile industrial --duration 600

# Monitor device activity
scripts/monitor_mqtt.sh -d TestDevice

# Send commands to devices
poetry run python scripts/send_device_command.py -d TestDevice -c get_status
```

### Configuration Management

#### Environment Variables (.env)

| Category | Variable | Description | Default |
|----------|----------|-------------|---------|
| **Flask** | `FLASK_ENV` | Environment mode | `development` |
| | `FLASK_DEBUG` | Debug mode | `True` |
| | `SECRET_KEY` | Flask secret key | Auto-generated |
| **Database** | `DATABASE_URL` | SQLite database path | `sqlite:///iotflow.db` |
| **IoTDB** | `IOTDB_HOST` | IoTDB host address | `localhost` |
| | `IOTDB_PORT` | IoTDB port | `6667` |
| | `IOTDB_USER` | IoTDB username | `root` |
| | `IOTDB_PASSWORD` | IoTDB password | `root` |
| **Redis** | `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| **MQTT** | `MQTT_HOST` | MQTT broker host | `localhost` |
| | `MQTT_PORT` | MQTT broker port | `1883` |
| | `MQTT_USERNAME` | MQTT authentication | `admin` |
| **Security** | `API_KEY_LENGTH` | Generated API key length | `32` |
| | `RATE_LIMIT_PER_MINUTE` | API rate limiting | `60` |

#### Service Configuration

**IoTDB Configuration:**
- Data retention: Configurable per storage group
- Precision: Millisecond timestamps
- Storage Groups: `root.iotflow.*`
- Compression: Configurable compression algorithms

**Redis Configuration:** 
- Memory usage: LRU eviction
- Persistence: Append-only file
- Max memory: 256MB

**MQTT Configuration:**
- Protocol: MQTT 3.1.1 & 5.0
- Authentication: Username/password
- TLS: Configurable (port 8883)
- WebSocket: Available (port 9001)

## 🚀 Production Deployment

### Container Deployment

```bash
# Production-ready deployment
docker compose -f docker-compose.prod.yml up -d

# Scale application instances
docker compose up --scale app=3

# Health checks and monitoring
docker compose ps
docker compose logs -f app
```

### Performance Tuning

#### Flask Application
```bash
# Use Gunicorn for production
poetry run gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - app:app

# With performance monitoring
poetry run gunicorn -w 4 -b 0.0.0.0:5000 --statsd-host=localhost:8125 app:app
```

#### Database Optimization
- **SQLite**: WAL mode for concurrent reads
- **IoTDB**: Appropriate storage group configuration and compression
- **Redis**: Memory optimization and persistence settings

### Security Hardening

#### API Security
- Rate limiting per device and IP
- API key rotation capabilities
- Request payload validation
- CORS configuration for web clients

#### Infrastructure Security
- TLS termination at load balancer
- Network isolation between services
- Secrets management (avoid plain text)
- Regular security updates

### Monitoring & Observability

#### Built-in Monitoring
```bash
# Application health
curl http://localhost:5000/health

# Service metrics
curl http://localhost:5000/api/v1/telemetry/status

# Admin dashboard
curl http://localhost:5000/api/v1/admin/dashboard
```

#### External Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards  
- **ELK Stack**: Log aggregation and analysis
- **Alerting**: PagerDuty, Slack integration

### System Health

```bash
# Basic health check
curl "http://localhost:5000/health"

# Detailed health check with all components
curl "http://localhost:5000/health?detailed=true"

# Check specific components
curl "http://localhost:5000/health?include=iotdb,redis,mqtt"

# Check telemetry system status
curl "http://localhost:5000/api/v1/telemetry/status"
```

## 📊 Performance Benchmarks

### Test Results (Local Development)

#### HTTP API Performance
- **Device Registration**: ~40ms average response time
- **Telemetry Storage**: ~70ms average (SQLite + IoTDB)
- **Data Retrieval**: ~50ms average
- **Concurrent Requests**: 100+ requests/second

#### Fleet Simulation Results
- **9 Device Fleet**: 20+ telemetry points/minute
- **30 Device Fleet**: 100+ telemetry points/minute  
- **Network Failure Simulation**: 5% realistic failure rate
- **Data Integrity**: 100% for successful transmissions

#### Database Performance
- **SQLite**: 1000+ device registrations/second
- **IoTDB**: 10,000+ telemetry points/second
- **Redis**: Sub-millisecond caching responses
- **Storage**: ~1KB per telemetry record

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 🚨 HTTP 500 Error on Telemetry Submission

**Symptoms:** `{"error":"Failed to store telemetry data","message":"IoTDB may not be available. Check logs for details."}`

**Diagnosis:**
```bash
# Check IoTDB service status
./docker-manage.sh status
docker logs iotflow-iotdb

# Test IoTDB connectivity
poetry run python scripts/check_iotdb_data.py

# Check Flask application logs
tail -50 logs/iotflow.log
```

**Solutions:**
1. **IoTDB Service Issues:**
   ```bash
   # Restart IoTDB service
   docker restart iotflow-iotdb
   
   # Check IoTDB initialization
   docker logs iotflow-iotdb | grep -i "error\|exception"
   ```

2. **Connection Issues:**
   ```bash
   # Verify IoTDB port accessibility
   telnet localhost 6667
   
   # Check network configuration
   docker network inspect iotflow_default
   ```

3. **Data Format Issues:**
   ```bash
   # Test with simple telemetry data
   curl -X POST http://localhost:5000/api/v1/telemetry \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"data": {"temperature": 25.0}}'
   ```

#### 🔌 Device Registration Issues

**Symptoms:** Device already exists errors, API key conflicts

**Solutions:**
```bash
# Check existing devices
curl http://localhost:5000/api/v1/admin/devices

# Use auto-suffix for testing
poetry run python simulators/new_mqtt_device_simulator.py \
    --name TestDevice --auto-suffix

# Force registration (development only)
poetry run python simulators/new_mqtt_device_simulator.py \
    --name TestDevice --force-register
```

#### 📡 MQTT Connection Problems

**Symptoms:** MQTT connection failures, authentication errors

**Diagnosis:**
```bash
# Check MQTT broker status
docker logs iotflow-mqtt

# Test MQTT connectivity
mosquitto_pub -h localhost -p 1883 -t "test/topic" -m "test message"
```

**Solutions:**
```bash
# Restart MQTT broker
docker restart iotflow-mqtt

# Check authentication
cat mqtt/config/passwd

# Verify MQTT configuration
cat mqtt/config/mosquitto.conf
```

#### 💾 Database Issues

**Symptoms:** SQLite database corruption, IoTDB storage errors

**Solutions:**
```bash
# Backup current database
./docker-manage.sh backup

# Reset database (CAUTION: destroys all data)
./docker-manage.sh reset

# Initialize fresh database
poetry run python manage.py init-db
```

### Performance Issues

#### Slow API Responses
1. **Check resource usage:**
   ```bash
   docker stats
   ```

2. **Database optimization:**
   ```bash
   # SQLite maintenance
   sqlite3 instance/iotflow.db "VACUUM;"
   
   # IoTDB compaction
   # (handled automatically)
   ```

3. **Redis cache issues:**
   ```bash
   # Clear Redis cache
   docker exec -it iotflow-redis redis-cli FLUSHALL
   ```

### Data Verification Tools

#### Check Data Flow
```bash
# Comprehensive data flow test
poetry run python scripts/check_device_data_flow.sh

# Manual data verification
poetry run python scripts/retrieve_iotdb_data.py --device 5 --latest --limit 10
```

#### Monitor Real-time Activity
```bash
# Watch device activity
poetry run python scripts/monitor_device_data.py --device TestDevice

# Monitor MQTT messages
./scripts/monitor_mqtt.sh
```

## 📚 Advanced Features

### 🔍 Data Analytics and Querying

#### IoTDB Advanced Queries
```bash
# Complex time-series analytics
poetry run python scripts/retrieve_iotdb_data.py \
    --device 5 \
    --hours 24 \
    --measurements temperature humidity \
    --export-csv device_5_analytics.csv

# Aggregated data with custom intervals
poetry run python scripts/retrieve_iotdb_data.py \
    --device 5 \
    --aggregate avg \
    --interval 1h \
    --hours 48
```

#### Data Export and Integration
```bash
# Export device data to multiple formats
poetry run python scripts/retrieve_iotdb_data.py \
    --device 5 --hours 6 --export-json device_data.json

# Batch export all devices
for device in $(curl -s http://localhost:5000/api/v1/admin/devices | jq -r '.[].id'); do
    poetry run python scripts/retrieve_iotdb_data.py \
        --device $device --hours 24 --export-csv "device_${device}_data.csv"
done
```

### 🤖 Advanced Device Simulation

#### Custom Device Profiles
Create custom simulation profiles by modifying the simulator's profile configuration:

```python
# Example: Custom IoT gateway profile
"iot_gateway": {
    "telemetry_types": ["cpu_usage", "memory_usage", "network_traffic", "connected_devices"],
    "telemetry_interval": 15,
    "heartbeat_interval": 45,
    "error_rate": 0.001,
    "battery_drain_rate": 0.0  # Powered device
}
```

#### Fleet Simulation
```bash
# Simulate multiple devices with different profiles
for i in {1..5}; do
    poetry run python simulators/new_mqtt_device_simulator.py \
        --name "FleetDevice_$i" \
        --profile $([ $((i % 2)) -eq 0 ] && echo "high_frequency" || echo "energy_efficient") \
        --duration 1800 &
done
```

### 🔐 Security and Authentication

#### API Key Management
```bash
# Generate new API key for existing device
poetry run python manage.py regenerate-api-key --device-id 5

# List all active API keys (admin only)
poetry run python manage.py list-api-keys
```

#### Advanced Rate Limiting
Configure per-device and per-endpoint rate limiting in `src/middleware/auth.py`:
- Device-specific limits
- Time-window based limiting
- Redis-backed rate limiting
- Automatic scaling based on device tier

### 📊 Monitoring and Alerting

#### Custom Metrics
```bash
# Device-specific monitoring
poetry run python scripts/monitor_device_data.py \
    --device TestDevice \
    --alert-threshold temperature:30 \
    --alert-threshold battery:20
```

#### System Health Monitoring
```bash
# Comprehensive system health check
poetry run python scripts/system_health_check.py

# Service-specific health checks
curl http://localhost:5000/health?include=iotdb,redis,mqtt
```

## 🔮 Future Roadmap

### Planned Features
- **🌐 Web Dashboard**: React-based admin interface
- **📱 Mobile API**: RESTful API optimizations for mobile apps
- **🔄 Device Firmware OTA**: Over-the-air firmware updates
- **🧠 ML Analytics**: Machine learning for predictive maintenance
- **📡 LoRaWAN Support**: Long-range, low-power device connectivity
- **🔐 OAuth2**: Enterprise authentication integration

### Architecture Evolution
- **Microservices**: Service decomposition for scalability
- **Message Queues**: Apache Kafka integration for high-throughput
- **Edge Computing**: Edge device data processing capabilities

## 🤝 Contributing

### Development Guidelines

#### Code Style
```bash
# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
poetry run pre-commit install

# Run code formatting
poetry run black .
poetry run isort .

# Run linting
poetry run flake8 .
poetry run mypy .
```

#### Testing Requirements
- Unit tests for all new features
- Integration tests for API endpoints
- End-to-end tests for device simulation
- Performance benchmarks for data operations

#### Pull Request Process
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Write tests for new functionality
4. Ensure all tests pass (`poetry run pytest`)
5. Update documentation
6. Submit pull request with detailed description

### Development Environment

```bash
# Complete development setup
git clone <repository-url>
cd IoTFlow_ConnectivityLayer

# Install dependencies
poetry install --with dev

# Set up environment
cp .env.example .env

# Start services
./docker-manage.sh start-all
./docker-manage.sh init-app

# Run in development mode
FLASK_ENV=development poetry run python app.py

# Run tests continuously
poetry run pytest --watch
```

### Code Quality

```bash
# Code formatting
poetry run black src/ simulators/
poetry run isort src/ simulators/

# Linting
poetry run flake8 src/ simulators/
poetry run mypy src/

# Testing
poetry run pytest tests/ --cov=src/
```

## 📚 Documentation

- **[Management Guide](MANAGEMENT_GUIDE.md)** - Comprehensive setup and management
- **[API Documentation](docs/api.md)** - Complete API reference
- **[Architecture Guide](docs/architecture.md)** - System design and components
- **[Testing Results](HTTP_SIMULATION_TEST_RESULTS.md)** - Performance and reliability tests
- **[IoTDB Integration](docs/iotdb_integration.md)** - Time-series database setup
- **[Device Status Cache](docs/device_status_cache.md)** - Redis-based device status caching

## ❓ Frequently Asked Questions (FAQ)

### General Questions

**Q: What's the difference between the legacy simulators and the new advanced simulator?**
A: The new advanced MQTT simulator (v2.1.0) replaces all legacy simulators with a single, production-ready tool that includes:
- Multiple simulation profiles (default, high_frequency, energy_efficient, industrial)
- Smart device registration handling (existing device detection, auto-suffix)
- Realistic device behavior with battery simulation and network jitter
- Comprehensive telemetry types and MQTT command handling
- Better error handling and logging

**Q: How do I handle the "device already exists" error during testing?**
A: Use one of these approaches:
```bash
# Option 1: Auto-suffix (recommended for testing)
--auto-suffix

# Option 2: Use a different device name
--name TestDevice_$(date +%s)

# Option 3: Force registration (development only)
--force-register
```

**Q: Why am I getting HTTP 500 errors when submitting telemetry?**
A: This usually indicates IoTDB connection issues. Check:
1. IoTDB service status: `docker logs iotflow-iotdb`
2. Network connectivity: `telnet localhost 6667`
3. Python IoTDB client: `poetry run python scripts/check_iotdb_data.py`

**Q: How can I monitor device activity in real-time?**
A: Use the monitoring tools:
```bash
# Monitor specific device
poetry run python scripts/monitor_device_data.py --device TestDevice

# Monitor MQTT messages
./scripts/monitor_mqtt.sh

# Check device logs
tail -f logs/device_TestDevice.log
```

### Technical Questions

**Q: What data types are supported for telemetry?**
A: IoTDB supports:
- **Numeric**: INT32, INT64, FLOAT, DOUBLE (for sensor readings)
- **Text**: STRING (for status messages, JSON objects)
- **Boolean**: BOOLEAN (for device states)
- **Complex**: JSON objects (automatically converted to TEXT)

**Q: How is data stored and organized?**
A: 
- **Device metadata**: SQLite database (`instance/iotflow.db`)
- **Telemetry data**: IoTDB time-series database (`root.iotflow.devices.device_{id}`)
- **Session data**: Redis cache for rate limiting and authentication
- **MQTT messages**: Real-time pub/sub (not persisted)

**Q: Can I use this in production?**
A: Yes, with proper configuration:
- Use production database settings (PostgreSQL instead of SQLite)
- Enable TLS for MQTT and HTTP
- Set up proper monitoring and alerting
- Configure rate limiting and security headers
- Use load balancing for Flask application

**Q: How do I scale the platform for more devices?**
A: Scaling strategies:
1. **Horizontal scaling**: Multiple Flask instances behind load balancer
2. **Database scaling**: PostgreSQL with read replicas
3. **IoTDB clustering**: Distributed IoTDB setup
4. **Message queuing**: Add Apache Kafka for high-throughput scenarios
5. **Microservices**: Split into device management, telemetry, and analytics services

### Development Questions

**Q: How do I add a new device type?**
A: 
1. Add device type to the allowed types in `src/routes/devices.py`
2. Update device simulator profiles if needed
3. Consider any specific telemetry requirements
4. Update documentation and tests

**Q: How do I add custom telemetry fields?**
A: Telemetry fields are flexible:
```python
# In device simulator or API call
"data": {
    "temperature": 25.0,
    "custom_field": "any_value",
    "complex_data": {"nested": "object"}
}
```
IoTDB will automatically create time series for new fields.

**Q: How do I backup and restore data?**
A: 
```bash
# Backup SQLite database
./docker-manage.sh backup

# Backup IoTDB data
docker exec iotflow-iotdb iotdb-export.sh -h localhost -p 6667 -u root -pw root -t /tmp/backup

# Restore database
./docker-manage.sh restore backup_file.db
```

## 📋 Quick Reference

### Essential Commands
```bash
# Complete setup
./docker-manage.sh start-all && ./docker-manage.sh init-app && ./docker-manage.sh run

# Test device simulation
poetry run python simulators/new_mqtt_device_simulator.py --name QuickTest --duration 60

# Check system health
curl http://localhost:5000/health

# View logs
./docker-manage.sh logs

# Reset everything (CAUTION)
./docker-manage.sh reset
```

### API Endpoints Summary
| Purpose | Method | Endpoint | Authentication |
|---------|--------|----------|----------------|
| Register device | POST | `/api/v1/devices/register` | None |
| Submit telemetry (HTTP) | POST | `/api/v1/devices/telemetry` | API Key |
| Submit telemetry (REST) | POST | `/api/v1/telemetry` | API Key |
| Submit telemetry (MQTT) | POST | `/api/v1/mqtt/telemetry/{device_id}` | API Key |
| Get latest telemetry | GET | `/api/v1/telemetry/{device_id}/latest` | API Key* |
| Get device history | GET | `/api/v1/telemetry/{device_id}?start_time=-24h&limit=100` | API Key* |
| Send heartbeat | POST | `/api/v1/devices/heartbeat` | API Key |
| Get device status | GET | `/api/v1/devices/status` | API Key |
| Update device config | PUT | `/api/v1/devices/config` | API Key |
| List all devices | GET | `/api/v1/admin/devices` | Admin |
| System statistics | GET | `/api/v1/admin/stats` | Admin |
| Health check | GET | `/health` | None |
| MQTT status | GET | `/api/v1/mqtt/status` | None |

\* API Key required if accessing own device data; Admin token required for other devices

### Common Data Formats
```bash
# Device registration
{
  "name": "MyDevice",
  "device_type": "smart_sensor",
  "location": "Office",
  "description": "Temperature and humidity sensor"
}

# Telemetry submission
{
  "data": {
    "temperature": 23.5,
    "humidity": 65.2,
    "battery_level": 87
  },
  "metadata": {
    "location": "Office",
    "sensor_status": "active"
  },
  "timestamp": "2025-07-04T10:30:00Z"
}
```

## 📞 Support and Community

### Getting Help
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive docs in `/docs` directory
- **Examples**: Working examples in `/simulators` and `/scripts`
- **Logs**: Detailed logging for troubleshooting

### Reporting Issues
When reporting issues, please include:
1. **Environment details**: OS, Python version, Docker version
2. **Steps to reproduce**: Exact commands and configuration
3. **Error messages**: Complete error output and logs
4. **Expected behavior**: What should have happened
5. **Actual behavior**: What actually happened

### Feature Requests
- Use GitHub issues with the "enhancement" label
- Provide detailed use case and requirements
- Include examples of expected API behavior
- Consider backward compatibility implications

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **IoTDB Community** for the excellent time-series database
- **Flask Community** for the robust web framework
- **Docker Community** for containerization best practices
- **MQTT.org** for the messaging protocol specifications
- **Contributors** who have helped improve this platform

---

**IoTFlow v0.2** - A modern, production-ready IoT connectivity platform.

Built with ❤️ for the IoT community.
