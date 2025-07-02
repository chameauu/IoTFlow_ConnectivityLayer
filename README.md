# IoTFlow - IoT Device Connectivity Layer

A modern, scalable REST API built with Python Flask for comprehensive IoT device connectivity, telemetry data collection, and real-time analytics.

## 🚀 Features

### Core Capabilities
- **🔌 Device Management**: Register, authenticate, and manage IoT devices with secure API keys
- **📊 Hybrid Data Storage**: SQLite for device management + InfluxDB for time-series telemetry
- **📡 Multi-Protocol Support**: HTTP REST API + MQTT pub/sub messaging
- **⚡ Real-time Analytics**: Time-series data queries, aggregations, and dashboards
- **🛡️ Security First**: API key authentication, rate limiting, and secure endpoints
- **📈 Scalable Architecture**: Redis caching, background processing, containerized services
- **🧪 Comprehensive Testing**: Built-in device simulators and testing framework

### Advanced Features
- **🔍 Time-Series Queries**: Advanced InfluxDB queries with filtering and aggregation
- **🤖 Device Simulation**: Fleet simulators for development and testing
- **📋 Admin Dashboard**: Complete device and data management interface
- **📚 Poetry Integration**: Modern dependency management and development workflow
- **🐳 Docker Compose**: Full containerized development environment
- **📊 Monitoring**: Comprehensive logging, metrics, and health checks

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
    │   SQLite    │   │  InfluxDB    │
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
# Start all services (Redis, InfluxDB, MQTT)
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

### Single Device Test
```bash
# Basic sensor simulation (60s, telemetry every 15s)
poetry run python simulators/basic_device_simulator.py --duration 60 --telemetry-interval 15

# Specific device types
poetry run python simulators/device_types.py --device-type temperature --duration 120
```

### Fleet Simulation
```bash
# Home setup (9 devices: sensors, locks, cameras)
poetry run python simulators/fleet_simulator.py --preset home --duration 300

# Office setup (16 devices)
poetry run python simulators/fleet_simulator.py --preset office --duration 300

# Interactive simulation control
poetry run python simulators/simulate.py --interactive
```

### Automated Testing
```bash
# Run all tests
poetry run python manage.py test

# Specific test suites
poetry run pytest tests/ -v
```
## 📡 API Endpoints

### 🔌 Device Management

| Method | Endpoint                    | Description                    | Auth Required |
|--------|----------------------------|--------------------------------|---------------|
| POST   | `/api/v1/devices/register` | Register new device            | None          |
| GET    | `/api/v1/devices/status`   | Get device status & health     | API Key       |
| POST   | `/api/v1/devices/heartbeat`| Send device heartbeat          | API Key       |
| PUT    | `/api/v1/devices/config`   | Update device configuration    | API Key       |

### 📊 Telemetry & Data

| Method | Endpoint                           | Description                    | Auth Required |
|--------|------------------------------------|--------------------------------|---------------|
| POST   | `/api/v1/devices/telemetry`       | Submit telemetry data          | API Key       |
| GET    | `/api/v1/telemetry/{device_id}`   | Get device telemetry history   | None          |
| GET    | `/api/v1/telemetry/{device_id}/latest` | Get latest telemetry      | None          |
| GET    | `/api/v1/telemetry/{device_id}/aggregated` | Get aggregated data   | None          |
| DELETE | `/api/v1/telemetry/{device_id}`   | Delete device telemetry        | Admin         |

### 🛠️ Administration

| Method | Endpoint                      | Description                 | Auth Required |
|--------|-------------------------------|-----------------------------|--------------| 
| GET    | `/api/v1/admin/devices`       | List all devices            | Admin         |
| GET    | `/api/v1/admin/devices/{id}`  | Get device details          | Admin         |
| PUT    | `/api/v1/admin/devices/{id}`  | Update device               | Admin         |
| DELETE | `/api/v1/admin/devices/{id}`  | Delete device               | Admin         |
| GET    | `/api/v1/admin/dashboard`     | Get dashboard statistics    | Admin         |

### 🔍 System Health

| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| GET    | `/health`             | API health check         |
| GET    | `/api/v1/telemetry/status` | Telemetry system status |

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
curl "http://localhost:5000/api/v1/telemetry/1/latest"

# Get historical data with filters
curl "http://localhost:5000/api/v1/telemetry/1?start_time=-1h&limit=100"

# Get aggregated data (hourly averages)
curl "http://localhost:5000/api/v1/telemetry/1/aggregated?window=1h&start_time=-24h"
```

### Device Heartbeat

```bash
curl -X POST http://localhost:5000/api/v1/devices/heartbeat \
  -H "X-API-Key: rnby0SIR2kF8mN3Q7vX9L1cE6tA5Y4pB"
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

### InfluxDB (Time-Series Telemetry)

**Measurement Structure:**
- **Measurement**: `device_telemetry`
- **Tags**: `device_id`, `device_type`, `location`
- **Fields**: All telemetry data (temperature, humidity, etc.)
- **Timestamp**: Precise time-series indexing

## 🛠️ Development & Management

### Project Structure

```
IoTFlow_ConnectivityLayer/
├── 📁 src/                          # Core application code
│   ├── config/                      # Configuration management
│   │   ├── config.py               # Flask & database config
│   │   └── influxdb_config.py      # InfluxDB configuration
│   ├── models/                      # SQLAlchemy database models
│   ├── routes/                      # API route handlers
│   │   ├── devices.py              # Device management endpoints
│   │   ├── telemetry.py            # Telemetry data endpoints
│   │   └── admin.py                # Administrative endpoints
│   ├── services/                    # Business logic services
│   │   └── influxdb.py             # InfluxDB service layer
│   ├── middleware/                  # Request/response middleware
│   │   ├── auth.py                 # Authentication & authorization
│   │   ├── security.py             # Security utilities
│   │   └── monitoring.py           # Performance monitoring
│   └── utils/                       # Utility functions
│       └── logging.py              # Logging configuration
├── 📁 simulators/                   # Device simulation & testing
│   ├── basic_device_simulator.py   # Single device simulator
│   ├── fleet_simulator.py          # Multi-device fleet simulator
│   ├── device_types.py             # Specialized device simulators
│   └── simulate.py                 # Interactive simulation control
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
    └── INFLUXDB_INTEGRATION_COMPLETE.md # Architecture docs
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
./docker-manage.sh logs influxdb # View specific service logs

# Data management
./docker-manage.sh backup        # Backup SQLite database
./docker-manage.sh restore backup_file.db  # Restore from backup
./docker-manage.sh reset         # Reset all data (CAUTION!)

# Database connections
./docker-manage.sh redis         # Connect to Redis CLI
./docker-manage.sh influxdb      # Connect to InfluxDB CLI
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
# Interactive simulation (recommended for development)
poetry run python simulators/simulate.py --interactive

# Single device tests
poetry run python simulators/basic_device_simulator.py --duration 300
poetry run python simulators/device_types.py --device-type temperature

# Fleet simulations for load testing
poetry run python simulators/fleet_simulator.py --preset home     # 9 devices
poetry run python simulators/fleet_simulator.py --preset office   # 16 devices
poetry run python simulators/fleet_simulator.py --preset factory  # 30 devices
```

### Configuration Management

#### Environment Variables (.env)

| Category | Variable | Description | Default |
|----------|----------|-------------|---------|
| **Flask** | `FLASK_ENV` | Environment mode | `development` |
| | `FLASK_DEBUG` | Debug mode | `True` |
| | `SECRET_KEY` | Flask secret key | Auto-generated |
| **Database** | `DATABASE_URL` | SQLite database path | `sqlite:///iotflow.db` |
| **InfluxDB** | `INFLUXDB_URL` | InfluxDB connection URL | `http://localhost:8086` |
| | `INFLUXDB_TOKEN` | Authentication token | Auto-configured |
| | `INFLUXDB_ORG` | Organization name | `iotflow` |
| | `INFLUXDB_BUCKET` | Data bucket name | `telemetry` |
| **Redis** | `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| **MQTT** | `MQTT_HOST` | MQTT broker host | `localhost` |
| | `MQTT_PORT` | MQTT broker port | `1883` |
| | `MQTT_USERNAME` | MQTT authentication | `admin` |
| **Security** | `API_KEY_LENGTH` | Generated API key length | `32` |
| | `RATE_LIMIT_PER_MINUTE` | API rate limiting | `60` |

#### Service Configuration

**InfluxDB Configuration:**
- Data retention: 30 days (configurable)
- Precision: nanosecond timestamps
- Organization: `iotflow`
- Bucket: `telemetry`

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
- **InfluxDB**: Appropriate shard duration and retention policies
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

## 📊 Performance Benchmarks

### Test Results (Local Development)

#### HTTP API Performance
- **Device Registration**: ~40ms average response time
- **Telemetry Storage**: ~70ms average (SQLite + InfluxDB)
- **Data Retrieval**: ~50ms average
- **Concurrent Requests**: 100+ requests/second

#### Fleet Simulation Results
- **9 Device Fleet**: 20+ telemetry points/minute
- **30 Device Fleet**: 100+ telemetry points/minute  
- **Network Failure Simulation**: 5% realistic failure rate
- **Data Integrity**: 100% for successful transmissions

#### Database Performance
- **SQLite**: 1000+ device registrations/second
- **InfluxDB**: 10,000+ telemetry points/second
- **Redis**: Sub-millisecond caching responses
- **Storage**: ~1KB per telemetry record

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone repository
git clone <your-fork-url>
cd IoTFlow_ConnectivityLayer

# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
poetry run pre-commit install

# Run development server
./docker-manage.sh start-all
./docker-manage.sh init-app
./docker-manage.sh run
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
- **[InfluxDB Integration](INFLUXDB_INTEGRATION_COMPLETE.md)** - Time-series database setup

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the comprehensive guides in `/docs`
- **Issues**: Open GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for general questions

### Troubleshooting

**Common Issues:**
- **Service Connection**: Check `./docker-manage.sh status`
- **Database Issues**: Run `./docker-manage.sh reset` and reinitialize
- **Port Conflicts**: Check that ports 5000, 6379, 8086, 1883 are available
- **Poetry Issues**: Update with `poetry install --sync`

**Log Locations:**
- Application: `logs/iotflow.log`
- Docker services: `docker-compose logs [service]`
- System: Check with `./docker-manage.sh logs`

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Setup for Production

1. **Database**: For production, consider using PostgreSQL or MySQL with connection pooling
2. **Security**: Change all default passwords and secret keys
3. **Logging**: Configure centralized logging
4. **Monitoring**: Set up application monitoring
5. **SSL**: Enable HTTPS with proper certificates
6. **Rate Limiting**: Use Redis for distributed rate limiting

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Check database file permissions and disk space
   - Verify credentials in `.env`
   - Ensure database exists

2. **API Key Authentication Failed**

   - Verify API key in `X-API-Key` header
   - Check device is active
   - Ensure API key hasn't expired

3. **Telemetry Submission Failed**
   - Validate JSON payload structure
   - Check rate limiting
   - Verify device authentication

### Debug Mode

Enable debug mode for development:

```bash
export FLASK_ENV=development
export DEBUG=True
python app.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs in `logs/iotflow.log`
3. Run the test script: `python test_api.py`
4. Verify database connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
