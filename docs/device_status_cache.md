# Device Status Cache

The IoTFlow platform uses Redis to cache device status information, improving performance and reducing database load. This document explains the caching system and how to use it.

## Overview

The device status cache system stores two main types of information:
1. **Device Status** - Online/offline status of devices
2. **Last Seen Timestamps** - When a device was last active

This information is updated automatically when:
- Devices send telemetry data
- Devices connect or disconnect
- Devices explicitly send status updates

## Benefits

- **Improved API Response Time** - Status queries are served from memory instead of database
- **Reduced Database Load** - Fewer queries to the database for frequently accessed data
- **Real-time Status Updates** - Device status changes are immediately reflected
- **Scalability** - Distributes load across services

## Implementation

The device status cache is implemented in the `DeviceStatusCache` service class in `src/services/device_status_cache.py`.

Key components:
- Redis keys use prefixes: `device:status:<id>` and `device:lastseen:<id>`
- TTL of 24 hours by default
- Automatic updates from MQTT handlers and device events
- Fallback to database if Redis is unavailable

## API Endpoints

### Get Device Status

**Endpoint:** `GET /api/v1/devices/{device_id}/status`

Returns detailed device status information, prioritizing Redis cache data when available.

**Response:**
```json
{
  "status": "success",
  "device": {
    "id": 1,
    "name": "TempSensor01",
    "device_type": "sensor",
    "status": "active",
    "is_online": true,
    "last_seen": "2023-07-04T15:32:21.456789Z",
    "status_source": "redis_cache",
    "last_seen_source": "redis_cache"
  }
}
```

### Get All Device Statuses

**Endpoint:** `GET /api/v1/devices/statuses`

Returns condensed status information for multiple devices efficiently.

**Response:**
```json
{
  "status": "success",
  "devices": [
    {
      "id": 1,
      "name": "TempSensor01",
      "device_type": "sensor",
      "status": "active",
      "is_online": true
    },
    {
      "id": 2,
      "name": "HumiditySensor02",
      "device_type": "sensor",
      "status": "active",
      "is_online": false
    }
  ],
  "meta": {
    "total": 2,
    "limit": 100,
    "offset": 0,
    "cache_used": true
  }
}
```

## Admin Endpoints

### Clear All Device Status Caches

**Endpoint:** `DELETE /api/v1/admin/cache/device-status`

Clears all device status and last seen information from Redis.

**Response:**
```json
{
  "status": "success",
  "message": "All device status caches cleared successfully"
}
```

### Clear Specific Device Cache

**Endpoint:** `DELETE /api/v1/admin/cache/devices/{device_id}`

Clears cache for a specific device.

**Response:**
```json
{
  "status": "success",
  "message": "Cache cleared for device 1"
}
```

### Get Cache Statistics

**Endpoint:** `GET /api/v1/admin/cache/device-status`

Returns statistics about the device status cache.

**Response:**
```json
{
  "status": "success",
  "cache_stats": {
    "device_status_count": 24,
    "device_lastseen_count": 22,
    "redis_memory_used": "1.2M",
    "redis_uptime": 86400,
    "redis_version": "6.2.6"
  }
}
```

## Testing

A test script is provided to verify the device status cache functionality:

```bash
./scripts/test_device_status_cache.py
```

This script simulates device connections, status updates, and telemetry messages, then verifies that the cache is updated correctly.

## Troubleshooting

If device status information is incorrect or outdated:

1. Check Redis connection with: `redis-cli ping`
2. Verify Redis contains device data: `redis-cli keys "device:status:*"`
3. Clear cache if needed: `curl -X DELETE http://localhost:5000/api/v1/admin/cache/device-status`
