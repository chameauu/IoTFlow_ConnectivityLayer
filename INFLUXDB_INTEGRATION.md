# InfluxDB Integration for IoTFlow Connectivity Layer

## Overview

The IoTFlow Connectivity Layer now includes comprehensive InfluxDB integration for real-time telemetry data storage, retrieval, and analysis. This integration provides:

- **Real-time telemetry storage**: Automatic storage of device telemetry in InfluxDB time-series database
- **Dual ingestion methods**: Support for both MQTT and HTTP telemetry submission
- **RESTful API endpoints**: Complete API for telemetry management and querying
- **Grafana visualization**: Ready for dashboard creation and real-time monitoring
- **Production-ready**: Batched writes, error handling, and performance optimization

## Architecture

```
IoT Devices → MQTT/HTTP → Flask Application → InfluxDB → Grafana
                ↓
          PostgreSQL (Device Registry)
```

### Data Flow

1. **Device Registration**: Devices register via HTTP API, stored in PostgreSQL
2. **Telemetry Submission**: 
   - **MQTT**: Real-time streaming via MQTT broker
   - **HTTP**: Direct REST API calls
3. **Data Processing**: Flask middleware processes and validates telemetry
4. **Storage**: 
   - **PostgreSQL**: Device metadata and structured telemetry records
   - **InfluxDB**: Time-series telemetry data for analytics
5. **Visualization**: Grafana dashboards for real-time monitoring

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# InfluxDB Configuration
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token-here
INFLUXDB_ORG=iotflow
INFLUXDB_BUCKET=telemetry
INFLUXDB_TIMEOUT=10000
INFLUXDB_BATCH_SIZE=5000
INFLUXDB_FLUSH_INTERVAL=10000

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_SECRET_KEY=grafana-secret-key
```

### Docker Services

The following services are configured in `docker-compose.yml`:

- **InfluxDB**: Time-series database on port 8086
- **Grafana**: Visualization platform on port 3000
- **Mosquitto**: MQTT broker on ports 1883/8883/9001

## API Endpoints

### InfluxDB Management

#### Health Check
```http
GET /api/v1/influxdb/health
```

Response:
```json
{
  "influxdb": {
    "status": "pass",
    "message": "OK",
    "version": "2.7.0"
  },
  "connected": true
}
```

#### Write Telemetry Data
```http
POST /api/v1/influxdb/telemetry
Content-Type: application/json
X-API-Key: your-api-key

{
  "device_id": "esp32_001",
  "measurement": "temperature",
  "fields": {
    "value": 23.5,
    "humidity": 45.0
  },
  "tags": {
    "location": "office",
    "sensor_type": "dht22"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Batch Write Telemetry
```http
POST /api/v1/influxdb/telemetry/batch
Content-Type: application/json
X-API-Key: your-api-key

{
  "points": [
    {
      "device_id": "esp32_001",
      "measurement": "temperature",
      "fields": {"value": 23.5},
      "tags": {"location": "office"}
    },
    {
      "device_id": "esp32_002",
      "measurement": "humidity", 
      "fields": {"value": 55.0},
      "tags": {"location": "kitchen"}
    }
  ]
}
```

#### Query Device Data
```http
GET /api/v1/influxdb/device/{device_id}/data?start=-1h&stop=now()&measurement=temperature
X-API-Key: your-api-key
```

Response:
```json
{
  "device_id": "esp32_001",
  "measurement": "temperature",
  "start_time": "-1h",
  "stop_time": "now()",
  "data_points": [
    {
      "time": "2024-01-01T12:00:00Z",
      "measurement": "temperature",
      "device_id": "esp32_001",
      "field": "value",
      "value": 23.5,
      "location": "office"
    }
  ],
  "count": 1
}
```

#### Get Latest Data
```http
GET /api/v1/influxdb/device/{device_id}/latest?measurement=temperature
X-API-Key: your-api-key
```

#### Delete Device Data
```http
DELETE /api/v1/influxdb/device/{device_id}/data?start=2024-01-01T00:00:00Z&stop=2024-01-02T00:00:00Z
X-API-Key: your-api-key
```

### Device Telemetry (with InfluxDB Integration)

#### Submit Telemetry via HTTP
```http
POST /api/v1/devices/telemetry
Content-Type: application/json
X-API-Key: device-api-key

{
  "data": {
    "temperature": 24.5,
    "humidity": 60.0,
    "battery_level": 85.0
  },
  "type": "environmental",
  "metadata": {
    "location": "sensor_room_1"
  }
}
```

This endpoint now automatically:
1. Stores data in PostgreSQL (structured)
2. Writes to InfluxDB (time-series)

## MQTT Integration

### Topic Structure

```
iotflow/devices/{device_id}/telemetry/{measurement_type}
iotflow/devices/{device_id}/status/{status_type}
iotflow/devices/{device_id}/commands/{command_type}
```

### Example MQTT Telemetry

```bash
# Publish temperature data
mosquitto_pub -h localhost -p 1883 \
  -u device_001 -P device_password \
  -t "iotflow/devices/esp32_001/telemetry/temperature" \
  -m '{"temperature": 25.5, "humidity": 60.0, "timestamp": "2024-01-01T12:00:00Z"}'
```

The MQTT service automatically writes telemetry to InfluxDB using the `TelemetryMessageHandler`.

## Data Schema

### InfluxDB Data Model

```
measurement: temperature, humidity, pressure, etc.
tags:
  - device_id: unique device identifier
  - device_name: human-readable device name
  - device_type: type of device (sensor, actuator, etc.)
  - location: physical location
  - topic: original MQTT topic (for MQTT data)
fields:
  - value: primary measurement value
  - [additional fields]: any additional numeric/boolean data
timestamp: RFC3339 timestamp
```

### Example Data Point

```json
{
  "measurement": "temperature",
  "tags": {
    "device_id": "esp32_001",
    "device_name": "Office Temperature Sensor",
    "device_type": "environmental",
    "location": "office",
    "topic": "iotflow/devices/esp32_001/telemetry/temperature"
  },
  "fields": {
    "value": 23.5,
    "humidity": 45.0,
    "battery_level": 85.0
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Setup Instructions

### 1. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 2. Initialize InfluxDB

```bash
# Run the initialization script
python init_influxdb.py
```

This script will:
- Wait for InfluxDB to be ready
- Create organization and bucket
- Generate API token
- Create sample data (optional)

### 3. Update Configuration

Update your `.env` file with the generated InfluxDB token:

```bash
INFLUXDB_TOKEN=generated-token-from-init-script
```

### 4. Start Application

```bash
# Using Poetry
poetry run python app.py

# Or directly
python app.py
```

### 5. Verify Integration

```bash
# Test InfluxDB health
curl -X GET "http://localhost:5000/api/v1/influxdb/health" \
  -H "X-API-Key: your-api-key"

# Test system integration
python test_influxdb.py
python test_system_integration.py
```

## Grafana Dashboard Setup

### 1. Access Grafana

- URL: http://localhost:3000
- Username: admin
- Password: admin123

### 2. Add InfluxDB Data Source

1. Go to Configuration → Data Sources
2. Add InfluxDB data source
3. Configure:
   - **URL**: http://influxdb:8086
   - **Organization**: iotflow
   - **Token**: your-influxdb-token
   - **Default Bucket**: telemetry

### 3. Create Dashboard

Example queries for dashboard panels:

#### Temperature Over Time
```flux
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "temperature")
  |> filter(fn: (r) => r["_field"] == "value")
```

#### Device Status Overview
```flux
from(bucket: "telemetry")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "status")
  |> last()
```

#### Multi-Device Comparison
```flux
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "temperature")
  |> group(columns: ["device_id"])
```

## Testing

### Unit Tests

```bash
# Test InfluxDB integration
python test_influxdb.py
```

### Integration Tests

```bash
# Test full system integration
python test_system_integration.py
```

### Manual Testing

```bash
# Test MQTT telemetry
python simulate_devices.py

# Test HTTP telemetry
curl -X POST "http://localhost:5000/api/v1/devices/telemetry" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: device-api-key" \
  -d '{
    "data": {"temperature": 25.0, "humidity": 60.0},
    "type": "environmental"
  }'
```

## Performance Optimization

### Batch Writing

The InfluxDB client uses batched writes with the following configuration:

- **Batch Size**: 5000 points
- **Flush Interval**: 10 seconds
- **Retry Logic**: Exponential backoff with max 5 retries

### Query Optimization

- Use appropriate time ranges for queries
- Leverage tags for filtering
- Use `last()` function for latest values
- Consider data retention policies

### Monitoring

Monitor the following metrics:

- **Write Performance**: Points per second
- **Query Performance**: Query execution time
- **Storage Usage**: Disk space and memory
- **Error Rates**: Failed writes/queries

## Troubleshooting

### Common Issues

#### InfluxDB Connection Failed
```bash
# Check InfluxDB status
docker-compose logs influxdb

# Verify network connectivity
curl http://localhost:8086/health
```

#### Authentication Errors
```bash
# Verify token in .env file
echo $INFLUXDB_TOKEN

# Test token with InfluxDB CLI
influx auth list --token $INFLUXDB_TOKEN
```

#### No Data in Grafana
1. Check InfluxDB data source configuration
2. Verify bucket and organization names
3. Check query syntax (Flux vs InfluxQL)
4. Ensure data is actually being written

### Debug Mode

Enable debug logging in your application:

```python
import logging
logging.getLogger('src.influxdb').setLevel(logging.DEBUG)
```

### Logs

Check application logs for InfluxDB-related messages:

```bash
tail -f logs/iotflow.log | grep -i influx
```

## ESP32 Integration

### Example Arduino Code

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* ssid = "your-wifi-ssid";
const char* password = "your-wifi-password";
const char* mqtt_server = "your-server-ip";
const char* mqtt_user = "device_001";
const char* mqtt_password = "device_password";

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(2, DHT22);

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Send telemetry every 30 seconds
  static unsigned long lastMsg = 0;
  unsigned long now = millis();
  if (now - lastMsg > 30000) {
    lastMsg = now;
    sendTelemetry();
  }
}

void sendTelemetry() {
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temp) && !isnan(humidity)) {
    DynamicJsonDocument doc(1024);
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["battery_level"] = 85.0;
    doc["timestamp"] = WiFi.getTime();
    
    String payload;
    serializeJson(doc, payload);
    
    client.publish("iotflow/devices/esp32_001/telemetry/environmental", payload.c_str());
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  // Handle incoming commands
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32Client", mqtt_user, mqtt_password)) {
      client.subscribe("iotflow/devices/esp32_001/commands/+");
    } else {
      delay(5000);
    }
  }
}
```

## Next Steps

1. **Real Device Integration**: Connect actual ESP32/Arduino devices
2. **Advanced Analytics**: Implement complex queries and aggregations
3. **Alerting**: Set up alerts based on telemetry thresholds
4. **Data Retention**: Configure appropriate retention policies
5. **Scaling**: Implement clustering for high-throughput scenarios

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review application logs
3. Consult InfluxDB and Grafana documentation
4. Check GitHub issues for similar problems

---

**Note**: This integration provides a production-ready foundation for IoT telemetry management with InfluxDB. Customize the configuration and schema according to your specific use case requirements.
