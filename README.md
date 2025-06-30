# IoT Device Connectivity Layer

A robust REST API built with Python Flask and PostgreSQL for managing IoT device connectivity and telemetry data collection.

## Features

- **Device Management**: Register, authenticate, and manage IoT devices
- **Telemetry Collection**: Secure endpoints for IoT devices to submit sensor data
- **Real-time Monitoring**: Track device status and connectivity
- **Admin Dashboard**: Comprehensive admin endpoints for device and data management
- **Secure Authentication**: API key-based authentication for devices
- **Rate Limiting**: Protect against abuse with configurable rate limits
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Architecture

```
IoT Devices → API Gateway → Flask Application → PostgreSQL Database
                ↓
        Admin Dashboard/Frontend
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- pip (Python package manager)

### 1. Clone and Setup

```bash
cd /home/chameau/Desktop/IoTFlow/connectivity_layer

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

First, create the PostgreSQL database:

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Run the database setup script
\i database_setup.sql
```

Or manually create the database:

```sql
CREATE DATABASE iotflow_db;
CREATE USER iotflow_user WITH PASSWORD 'iotflow_password';
GRANT ALL PRIVILEGES ON DATABASE iotflow_db TO iotflow_user;
```

### 3. Environment Configuration

Update the `.env` file with your database credentials:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=iotflow_db
DB_USER=iotflow_user
DB_PASSWORD=iotflow_password

# Security (change in production!)
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key
```

### 4. Initialize Database

```bash
python init_db.py
```

This will create the database tables and sample devices with API keys for testing.

### 5. Start the Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### 6. Test the API

```bash
python test_api.py
```

## API Endpoints

### Device Endpoints

| Method | Endpoint                    | Description           | Authentication |
| ------ | --------------------------- | --------------------- | -------------- |
| POST   | `/api/v1/devices/register`  | Register a new device | None           |
| GET    | `/api/v1/devices/status`    | Get device status     | API Key        |
| POST   | `/api/v1/devices/telemetry` | Submit telemetry data | API Key        |
| GET    | `/api/v1/devices/telemetry` | Get device telemetry  | API Key        |
| PUT    | `/api/v1/devices/config`    | Update device config  | API Key        |
| POST   | `/api/v1/devices/heartbeat` | Send heartbeat        | API Key        |

### Admin Endpoints

| Method | Endpoint                     | Description            |
| ------ | ---------------------------- | ---------------------- |
| GET    | `/api/v1/admin/devices`      | List all devices       |
| GET    | `/api/v1/admin/devices/{id}` | Get device details     |
| PUT    | `/api/v1/admin/devices/{id}` | Update device          |
| DELETE | `/api/v1/admin/devices/{id}` | Delete device          |
| GET    | `/api/v1/admin/dashboard`    | Get dashboard stats    |
| GET    | `/api/v1/admin/telemetry`    | Get all telemetry data |

### Health Check

| Method | Endpoint  | Description      |
| ------ | --------- | ---------------- |
| GET    | `/health` | API health check |

## Usage Examples

### Register a Device

```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature Sensor 001",
    "description": "Living room sensor",
    "device_type": "sensor",
    "location": "Living Room"
  }'
```

Response:

```json
{
  "message": "Device registered successfully",
  "device": {
    "id": 1,
    "name": "Temperature Sensor 001",
    "api_key": "abc123xyz789...",
    "status": "active",
    "created_at": "2025-06-30T10:00:00Z"
  }
}
```

### Submit Telemetry Data

```bash
curl -X POST http://localhost:5000/api/v1/devices/telemetry \
  -H "X-API-Key: your-device-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "temperature": 22.5,
      "humidity": 65,
      "pressure": 1013.25
    },
    "metadata": {
      "battery_level": 85,
      "signal_strength": -45
    },
    "type": "sensor"
  }'
```

### Get Device Status

```bash
curl -X GET http://localhost:5000/api/v1/devices/status \
  -H "X-API-Key: your-device-api-key"
```

### Admin: Get Dashboard Statistics

```bash
curl -X GET http://localhost:5000/api/v1/admin/dashboard
```

## Database Schema

### Devices Table

- `id` (Primary Key)
- `name` (Unique device name)
- `description`
- `device_type` (sensor, actuator, camera, etc.)
- `api_key` (Unique authentication key)
- `status` (active, inactive, maintenance)
- `location`
- `firmware_version`
- `hardware_version`
- `created_at`
- `updated_at`
- `last_seen`

### Telemetry Data Table

- `id` (Primary Key)
- `device_id` (Foreign Key)
- `payload` (JSON sensor data)
- `timestamp`
- `metadata` (JSON additional data)
- `data_type`

### Device Auth Table

- `id` (Primary Key)
- `device_id` (Foreign Key)
- `api_key_hash`
- `is_active`
- `expires_at`
- `created_at`
- `last_used`
- `usage_count`

## Configuration

### Environment Variables

| Variable                | Description                     | Default    |
| ----------------------- | ------------------------------- | ---------- |
| `DATABASE_URL`          | Full database connection string | -          |
| `DB_HOST`               | Database host                   | localhost  |
| `DB_PORT`               | Database port                   | 5432       |
| `DB_NAME`               | Database name                   | iotflow_db |
| `DB_USER`               | Database user                   | username   |
| `DB_PASSWORD`           | Database password               | password   |
| `SECRET_KEY`            | Flask secret key                | -          |
| `DEBUG`                 | Debug mode                      | True       |
| `LOG_LEVEL`             | Logging level                   | INFO       |
| `RATE_LIMIT_PER_MINUTE` | API rate limit                  | 60         |

### Rate Limiting

Configure rate limiting per device:

- Default: 60 requests per minute
- Telemetry endpoints: 100 requests per minute
- Can be configured via environment variables

## Security

### API Key Authentication

- Each device has a unique API key
- API keys are generated during device registration
- Include API key in `X-API-Key` header

### Data Validation

- JSON schema validation for all endpoints
- Input sanitization and type checking
- Error handling with appropriate HTTP status codes

### Rate Limiting

- Configurable rate limits per device
- Protection against API abuse
- Automatic throttling

## Monitoring and Logging

### Logging Levels

- **ERROR**: System errors and failures
- **WARNING**: Important events (auth failures, rate limits)
- **INFO**: General operations (device registration, telemetry)
- **DEBUG**: Detailed debugging information

### Log Files

- Location: `logs/iotflow.log`
- Rotation: 10MB files, 5 backups
- Format: Timestamp, level, message

### Health Monitoring

- Health check endpoint: `/health`
- Database connection monitoring
- Application status reporting

## Development

### Project Structure

```
connectivity_layer/
├── app.py                  # Main application
├── requirements.txt        # Dependencies
├── .env                   # Environment variables
├── init_db.py             # Database initialization
├── test_api.py            # API testing script
├── database_setup.sql     # Database setup script
├── src/
│   ├── config/
│   │   └── config.py      # Configuration classes
│   ├── models/
│   │   └── __init__.py    # Database models
│   ├── routes/
│   │   ├── devices.py     # Device endpoints
│   │   └── admin.py       # Admin endpoints
│   ├── middleware/
│   │   └── auth.py        # Authentication middleware
│   └── utils/
│       └── logging.py     # Logging utilities
└── logs/                  # Log files
```

### Running Tests

```bash
# Install test dependencies
pip install pytest requests

# Run API tests
python test_api.py

# Run unit tests (if implemented)
pytest tests/
```

### Database Migrations

```bash
# Initialize migrations (first time)
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Production Deployment

### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

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

1. **Database**: Use PostgreSQL with connection pooling
2. **Security**: Change all default passwords and secret keys
3. **Logging**: Configure centralized logging
4. **Monitoring**: Set up application monitoring
5. **SSL**: Enable HTTPS with proper certificates
6. **Rate Limiting**: Use Redis for distributed rate limiting

## Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Check PostgreSQL is running
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
