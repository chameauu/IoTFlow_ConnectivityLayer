"""
InfluxDB management and telemetry API routes
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from src.influxdb.client import get_influxdb_service, TelemetryPoint
from src.middleware.auth import authenticate_device

logger = logging.getLogger(__name__)

# Create blueprint
influxdb_bp = Blueprint('influxdb', __name__, url_prefix='/api/v1/influxdb')


@influxdb_bp.route('/health', methods=['GET'])
def influxdb_health():
    """Get InfluxDB health status"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service:
            return jsonify({
                'error': 'InfluxDB service not initialized'
            }), 503
        
        health_status = influxdb_service.health_check()
        
        return jsonify({
            'influxdb': health_status,
            'connected': influxdb_service.is_connected()
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking InfluxDB health: {e}")
        return jsonify({'error': 'Failed to check InfluxDB health'}), 500


@influxdb_bp.route('/telemetry', methods=['POST'])
@authenticate_device
def write_telemetry():
    """Write telemetry data to InfluxDB"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['device_id', 'measurement', 'fields']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse timestamp
        timestamp = None
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create telemetry point
        telemetry_point = TelemetryPoint(
            measurement=data['measurement'],
            device_id=data['device_id'],
            timestamp=timestamp,
            fields=data['fields'],
            tags=data.get('tags', {})
        )
        
        # Write to InfluxDB
        success = influxdb_service.write_telemetry_point(telemetry_point)
        
        if success:
            return jsonify({
                'message': 'Telemetry data written successfully',
                'device_id': data['device_id'],
                'measurement': data['measurement'],
                'timestamp': timestamp.isoformat()
            }), 201
        else:
            return jsonify({'error': 'Failed to write telemetry data'}), 500
            
    except Exception as e:
        logger.error(f"Error writing telemetry data: {e}")
        return jsonify({'error': 'Failed to write telemetry data'}), 500


@influxdb_bp.route('/telemetry/batch', methods=['POST'])
@authenticate_device
def write_telemetry_batch():
    """Write multiple telemetry data points to InfluxDB"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        data = request.get_json()
        if not data or 'points' not in data:
            return jsonify({'error': 'No telemetry points provided'}), 400
        
        points = data['points']
        if not isinstance(points, list):
            return jsonify({'error': 'Points must be a list'}), 400
        
        telemetry_points = []
        
        for i, point_data in enumerate(points):
            # Validate required fields
            required_fields = ['device_id', 'measurement', 'fields']
            for field in required_fields:
                if field not in point_data:
                    return jsonify({
                        'error': f'Missing required field "{field}" in point {i}'
                    }), 400
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in point_data:
                try:
                    timestamp = datetime.fromisoformat(point_data['timestamp'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Create telemetry point
            telemetry_point = TelemetryPoint(
                measurement=point_data['measurement'],
                device_id=point_data['device_id'],
                timestamp=timestamp,
                fields=point_data['fields'],
                tags=point_data.get('tags', {})
            )
            
            telemetry_points.append(telemetry_point)
        
        # Write to InfluxDB
        success = influxdb_service.write_telemetry_batch(telemetry_points)
        
        if success:
            return jsonify({
                'message': f'Successfully written {len(telemetry_points)} telemetry points',
                'count': len(telemetry_points)
            }), 201
        else:
            return jsonify({'error': 'Failed to write telemetry batch'}), 500
            
    except Exception as e:
        logger.error(f"Error writing telemetry batch: {e}")
        return jsonify({'error': 'Failed to write telemetry batch'}), 500


@influxdb_bp.route('/device/<device_id>/data', methods=['GET'])
@authenticate_device
def get_device_data(device_id):
    """Get telemetry data for a specific device"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        # Get query parameters
        measurement = request.args.get('measurement')
        start_time = request.args.get('start', '-1h')
        stop_time = request.args.get('stop', 'now()')
        
        # Query data
        data_points = influxdb_service.query_device_data(
            device_id=device_id,
            measurement=measurement,
            start_time=start_time,
            stop_time=stop_time
        )
        
        return jsonify({
            'device_id': device_id,
            'measurement': measurement,
            'start_time': start_time,
            'stop_time': stop_time,
            'data_points': data_points,
            'count': len(data_points)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting device data: {e}")
        return jsonify({'error': 'Failed to get device data'}), 500


@influxdb_bp.route('/device/<device_id>/latest', methods=['GET'])
@authenticate_device
def get_device_latest_data(device_id):
    """Get latest telemetry data for a specific device"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        # Get query parameters
        measurement = request.args.get('measurement')
        
        # Query latest data
        latest_data = influxdb_service.get_device_latest_data(
            device_id=device_id,
            measurement=measurement
        )
        
        if latest_data:
            return jsonify({
                'device_id': device_id,
                'measurement': measurement,
                'latest_data': latest_data
            }), 200
        else:
            return jsonify({
                'device_id': device_id,
                'measurement': measurement,
                'latest_data': None,
                'message': 'No data found'
            }), 404
        
    except Exception as e:
        logger.error(f"Error getting latest device data: {e}")
        return jsonify({'error': 'Failed to get latest device data'}), 500


@influxdb_bp.route('/device/<device_id>/data', methods=['DELETE'])
@authenticate_device
def delete_device_data(device_id):
    """Delete telemetry data for a specific device"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        # Get query parameters
        start_time = request.args.get('start', '1970-01-01T00:00:00Z')
        stop_time = request.args.get('stop', 'now()')
        
        # Delete data
        success = influxdb_service.delete_device_data(
            device_id=device_id,
            start_time=start_time,
            stop_time=stop_time
        )
        
        if success:
            return jsonify({
                'message': f'Successfully deleted telemetry data for device {device_id}',
                'device_id': device_id,
                'start_time': start_time,
                'stop_time': stop_time
            }), 200
        else:
            return jsonify({'error': 'Failed to delete device data'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting device data: {e}")
        return jsonify({'error': 'Failed to delete device data'}), 500


@influxdb_bp.route('/buckets', methods=['GET'])
@authenticate_device
def list_buckets():
    """List available InfluxDB buckets"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        # Get buckets API
        buckets_api = influxdb_service.client.buckets_api()
        buckets = buckets_api.find_buckets()
        
        bucket_list = []
        for bucket in buckets.buckets:
            bucket_list.append({
                'id': bucket.id,
                'name': bucket.name,
                'org_id': bucket.org_id,
                'retention_rules': [
                    {
                        'type': rule.type,
                        'every_seconds': rule.every_seconds
                    } for rule in bucket.retention_rules
                ] if bucket.retention_rules else []
            })
        
        return jsonify({
            'buckets': bucket_list,
            'count': len(bucket_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return jsonify({'error': 'Failed to list buckets'}), 500


@influxdb_bp.route('/stats', methods=['GET'])
@authenticate_device
def get_stats():
    """Get InfluxDB statistics"""
    try:
        influxdb_service = get_influxdb_service()
        if not influxdb_service or not influxdb_service.is_connected():
            return jsonify({
                'error': 'InfluxDB service not available'
            }), 503
        
        # Get basic statistics
        stats = {
            'connected': influxdb_service.is_connected(),
            'url': influxdb_service.url,
            'org': influxdb_service.org,
            'bucket': influxdb_service.bucket,
            'timeout': influxdb_service.timeout
        }
        
        # Try to get health status
        try:
            health = influxdb_service.health_check()
            stats['health'] = health
        except Exception as e:
            stats['health'] = {'status': 'error', 'message': str(e)}
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting InfluxDB stats: {e}")
        return jsonify({'error': 'Failed to get InfluxDB stats'}), 500
