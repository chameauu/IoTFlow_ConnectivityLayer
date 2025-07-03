# IoTDB Integration Guide

## Overview

This document provides comprehensive information about the IoTDB integration in the IoT Connectivity Layer project. Apache IoTDB is used as the time-series database for storing and querying telemetry data from IoT devices.

## Architecture

### Data Model

IoTDB uses a hierarchical data model with the following structure:

```
root.iotflow.{device_id}.{measurement}
```

**Example:**
```
root.iotflow.device_1.temperature
root.iotflow.device_1.humidity
root.iotflow.device_1.pressure
root.iotflow.device_2.temperature
```

### Storage Groups

The system creates storage groups per device to optimize data management and querying:

- **Storage Group Pattern**: `root.iotflow.device_{device_id}`
- **Time Series**: Individual measurements within each device's storage group
- **Data Types**: Automatically detected (INT32, INT64, FLOAT, DOUBLE, TEXT, BOOLEAN)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IOTDB_HOST` | IoTDB server hostname | `localhost` |
| `IOTDB_PORT` | IoTDB server port | `6667` |
| `IOTDB_USER` | IoTDB username | `root` |
| `IOTDB_PASSWORD` | IoTDB password | `root` |

### Docker Configuration

The IoTDB service is configured in `docker-compose.yml`:

```yaml
iotdb:
  image: apache/iotdb:1.3.2-standalone
  container_name: iotdb
  ports:
    - "6667:6667"   # Main service port
    - "31999:31999" # Sync service port
    - "8181:8181"   # REST service port (optional)
  volumes:
    - iotdb_data:/iotdb/data
    - iotdb_logs:/iotdb/logs
  environment:
    - IOTDB_JMX_LOCAL=false
  healthcheck:
    test: ["CMD", "nc", "-z", "localhost", "6667"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s
```

## Service Implementation

### IoTDBService Class

The `IoTDBService` class provides the following methods:

#### Connection Management
- `__init__()`: Initialize connection configuration
- `get_session()`: Get or create IoTDB session
- `close()`: Close IoTDB session

#### Data Operations
- `write_telemetry(device_id, data, timestamp=None)`: Write telemetry data
- `query_telemetry(device_id, start_time=None, end_time=None, limit=None)`: Query telemetry data
- `get_latest_telemetry(device_id)`: Get most recent telemetry
- `get_telemetry_count(device_id, hours=1)`: Count telemetry records
- `delete_device_data(device_id)`: Delete all data for a device

#### Health Monitoring
- `health_check()`: Check IoTDB connectivity and status

### Usage Examples

#### Writing Telemetry Data

```python
from src.services.iotdb import IoTDBService

iotdb_service = IoTDBService()

# Write single measurement
iotdb_service.write_telemetry(
    device_id=1,
    data={
        'temperature': 23.5,
        'humidity': 65.2,
        'pressure': 1013.25
    }
)
```

#### Querying Data

```python
# Get recent data
recent_data = iotdb_service.query_telemetry(
    device_id=1,
    start_time=datetime.now() - timedelta(hours=1),
    limit=100
)

# Get latest telemetry
latest = iotdb_service.get_latest_telemetry(device_id=1)

# Count records
count = iotdb_service.get_telemetry_count(device_id=1, hours=24)
```

## Data Management

### Storage Groups

Storage groups are automatically created when the first telemetry data is written for a device:

```sql
-- Example storage group creation
CREATE STORAGE GROUP root.iotflow.device_1;
```

### Time Series Creation

Time series are created automatically based on the telemetry data structure:

```sql
-- Example time series creation
CREATE TIMESERIES root.iotflow.device_1.temperature WITH DATATYPE=FLOAT, ENCODING=RLE;
CREATE TIMESERIES root.iotflow.device_1.humidity WITH DATATYPE=FLOAT, ENCODING=RLE;
```

### Data Retention

Configure data retention policies per storage group:

```sql
-- Set TTL (Time To Live) for a storage group
SET TTL TO root.iotflow.device_1 2592000000; -- 30 days in milliseconds
```

## Monitoring and Health Checks

### Health Check Implementation

The health check verifies:
1. IoTDB connection status
2. Session validity
3. Basic query functionality

### Monitoring Endpoints

- `GET /health`: Basic health check including IoTDB status
- `GET /health?detailed=true`: Detailed health information with IoTDB metrics
- `GET /api/v1/telemetry/status`: Telemetry system status including IoTDB statistics

### Metrics Collected

- Total devices with telemetry data
- Recent telemetry counts (last hour/day)
- IoTDB connection status
- Query performance metrics

## Performance Optimization

### Best Practices

1. **Batch Writes**: Use batch operations for multiple measurements
2. **Storage Groups**: Organize data by device for optimal querying
3. **Data Types**: Use appropriate data types for measurements
4. **Compression**: Enable compression for better storage efficiency

### Configuration Tuning

#### Memory Settings

```bash
# In IoTDB configuration (iotdb-datanode.properties)
datanode_rpc_thrift_compression_enable=true
datanode_rpc_advanced_compression_enable=true
```

#### Query Optimization

- Use time-based filtering for efficient queries
- Limit result sets with appropriate LIMIT clauses
- Index frequently queried time series

## Troubleshooting

### Common Issues

#### Connection Problems

```bash
# Check IoTDB service status
docker compose ps iotdb

# Check IoTDB logs
docker compose logs iotdb

# Test connection
nc -z localhost 6667
```

#### Query Performance

- Ensure proper time range filtering
- Use appropriate data types
- Monitor query execution time
- Consider storage group organization

#### Data Issues

```bash
# Connect to IoTDB CLI
docker compose exec iotdb /iotdb/sbin/start-cli.sh -h localhost -p 6667 -u root -pw root

# Show storage groups
SHOW STORAGE GROUP;

# Show time series
SHOW TIMESERIES;

# Count records
SELECT count(*) FROM root.iotflow.device_1.*;
```

### Error Messages

| Error | Cause | Solution |
|-------|--------|----------|
| Connection refused | IoTDB not running | Start IoTDB service |
| Session timeout | Network issues | Check connectivity |
| Storage group exists | Duplicate creation | Use IF NOT EXISTS |
| Invalid time series | Wrong data type | Check measurement types |

## Migration from InfluxDB

### Data Migration Process

1. **Export InfluxDB Data**:
   ```bash
   influx query 'SELECT * FROM device_telemetry' --format csv > export.csv
   ```

2. **Transform Data Format**:
   - Convert InfluxDB line protocol to IoTDB format
   - Map measurements to IoTDB time series
   - Handle data type conversions

3. **Import to IoTDB**:
   - Use IoTDB import tools or write custom scripts
   - Create appropriate storage groups
   - Batch insert data

### Schema Mapping

| InfluxDB Concept | IoTDB Concept |
|------------------|---------------|
| Measurement | Storage Group |
| Tags | Path segments |
| Fields | Time Series |
| Timestamp | Timestamp |

## Security

### Authentication

IoTDB supports multiple authentication modes:
- Default: username/password (root/root)
- LDAP integration (enterprise)
- Custom authentication plugins

### Access Control

```sql
-- Create user
CREATE USER 'iotflow_user' 'password123';

-- Grant privileges
GRANT READ_TIMESERIES ON root.iotflow.** TO USER 'iotflow_user';
GRANT WRITE_TIMESERIES ON root.iotflow.** TO USER 'iotflow_user';
```

### Network Security

- Use TLS encryption for production deployments
- Configure firewall rules for port 6667
- Implement network segmentation

## Backup and Recovery

### Backup Strategies

1. **Snapshot Backup**:
   ```bash
   # Stop IoTDB
   docker compose stop iotdb
   
   # Backup data directory
   docker run --rm -v iotdb_data:/data -v $(pwd):/backup alpine tar czf /backup/iotdb_backup.tar.gz -C /data .
   
   # Start IoTDB
   docker compose start iotdb
   ```

2. **Export SQL**:
   ```sql
   -- Export storage group data
   EXPORT DATA '/iotdb/export/' root.iotflow.device_1.**;
   ```

### Recovery

```bash
# Restore from backup
docker run --rm -v iotdb_data:/data -v $(pwd):/backup alpine tar xzf /backup/iotdb_backup.tar.gz -C /data
```

## References

- [Apache IoTDB Documentation](https://iotdb.apache.org/UserGuide/Master/QuickStart/QuickStart.html)
- [IoTDB Python Client](https://github.com/apache/iotdb-client-py)
- [IoTDB Best Practices](https://iotdb.apache.org/UserGuide/Master/Administration-Management/Administration.html)
