# IoTFlow Connectivity Layer - Management Guide

This guide covers the management scripts that have been updated to work with Poetry and the new hybrid SQLite + InfluxDB architecture.

## Prerequisites

- Docker and Docker Compose
- Poetry (Python dependency management)
- Python 3.8+

## Management Scripts

### 1. Docker Management Script (`docker-manage.sh`)

Updated to work with the new hybrid architecture (SQLite + InfluxDB + Redis + MQTT).

**Key Commands:**

```bash
# Start all services (recommended for development)
./docker-manage.sh start-all

# Initialize Python environment and database (first time setup)
./docker-manage.sh init-app

# Run Flask application using Poetry
./docker-manage.sh run

# Run tests using Poetry
./docker-manage.sh test

# Show service status
./docker-manage.sh status

# View logs
./docker-manage.sh logs
./docker-manage.sh logs influxdb

# Connect to database tools
./docker-manage.sh redis      # Redis CLI
./docker-manage.sh influxdb   # InfluxDB CLI

# Backup and restore SQLite database
./docker-manage.sh backup
./docker-manage.sh restore backup_20250702_120000.db

# Reset all data (DANGEROUS!)
./docker-manage.sh reset
```

### 2. Python Management Script (`manage.py`)

Updated to ensure all commands use Poetry properly.

**Usage:**
```bash
# All commands should be run with Poetry
poetry run python manage.py <command>
```

**Available Commands:**

```bash
# Initialize SQLite database
poetry run python manage.py init-db

# Create a new device
poetry run python manage.py create-device "My Device"

# Run Flask development server
poetry run python manage.py run

# Run tests
poetry run python manage.py test

# Start interactive Python shell with app context
poetry run python manage.py shell
```

## Quick Start Workflow

1. **First Time Setup:**
   ```bash
   ./docker-manage.sh start-all    # Start all services
   ./docker-manage.sh init-app     # Install deps and init database
   ```

2. **Daily Development:**
   ```bash
   ./docker-manage.sh start-all    # Start services
   ./docker-manage.sh run          # Start Flask app
   ```

3. **Testing:**
   ```bash
   ./docker-manage.sh test         # Run all tests
   ```

4. **Create Test Device:**
   ```bash
   poetry run python manage.py create-device "Test Device"
   ```

## Architecture Notes

- **SQLite**: Used for device management, stored as `iotflow.db`
- **InfluxDB**: Used for time-series telemetry data
- **Redis**: Used for caching and metrics
- **MQTT**: Message broker for device communication

## Service URLs

- Flask Application: http://localhost:5000
- InfluxDB UI: http://localhost:8086
- MQTT Broker: 
  - TCP: localhost:1883
  - TLS: localhost:8883
  - WebSocket: localhost:9001

## Environment Configuration

All configuration is managed through Poetry and the `.env` file. Key variables:

```bash
# Database
DATABASE_URL=sqlite:///iotflow.db

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-super-secret-token
INFLUXDB_ORG=iotflow
INFLUXDB_BUCKET=telemetry

# Redis
REDIS_URL=redis://localhost:6379/0

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883
```

## Poetry Integration Benefits

- **Dependency Management**: All Python dependencies are managed through `pyproject.toml`
- **Virtual Environment**: Poetry automatically manages virtual environments
- **Consistent Commands**: All Python commands are prefixed with `poetry run`
- **Lock File**: `poetry.lock` ensures reproducible builds
- **Development Dependencies**: Test and development tools are properly separated

## Troubleshooting

**Poetry not found:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Services not starting:**
```bash
./docker-manage.sh status
./docker-manage.sh logs
```

**Database issues:**
```bash
./docker-manage.sh reset     # Reset everything
./docker-manage.sh init-app  # Reinitialize
```

**MQTT connection issues:**
```bash
./docker-manage.sh logs mqtt
# Check if MQTT broker is running
docker compose ps mqtt
```
