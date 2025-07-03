from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from src.services.influxdb import InfluxDBService
from src.models import Device, db

# Create blueprint for telemetry routes
telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/v1/telemetry')

# Initialize InfluxDB service
influx_service = InfluxDBService()

@telemetry_bp.route('', methods=['POST'])
def store_telemetry():
    """Store telemetry data in InfluxDB"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get API key from headers
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Find device by API key
        device = Device.query.filter_by(api_key=api_key).first()
        if not device:
            return jsonify({'error': 'Invalid API key'}), 401
        
        telemetry_data = data.get('data', {})
        metadata = data.get('metadata', {})
        timestamp_str = data.get('timestamp')
        
        if not telemetry_data:
            return jsonify({'error': 'Telemetry data is required'}), 400
        
        # Parse timestamp if provided
        timestamp = None
        if timestamp_str:
            try:
                # Handle different timestamp formats
                if timestamp_str.endswith('Z'):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format. Use ISO 8601 format.'}), 400
        
        # Store in InfluxDB
        success = influx_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_data,
            device_type=device.device_type,
            metadata=metadata,
            timestamp=timestamp
        )
        
        if success:
            # Update device last_seen
            device.update_last_seen()
            
            current_app.logger.info(f"Telemetry stored for device {device.name} (ID: {device.id})")
            
            return jsonify({
                'message': 'Telemetry data stored successfully',
                'device_id': device.id,
                'device_name': device.name,
                'timestamp': timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat()
            }), 201
        else:
            return jsonify({
                'error': 'Failed to store telemetry data',
                'message': 'InfluxDB may not be available. Check logs for details.'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error storing telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>', methods=['GET'])
def get_device_telemetry(device_id):
    """Get telemetry data for a specific device"""
    try:
        # Verify device exists
        device = Device.query.get_or_404(device_id)
        
        # Get query parameters
        start_time = request.args.get('start_time', '-1h')  # Default to last hour
        limit = min(int(request.args.get('limit', 1000)), 10000)  # Max 10k records
        
        telemetry_data = influx_service.get_device_telemetry(
            device_id=str(device_id),
            start_time=start_time,
            limit=limit
        )
        
        return jsonify({
            'device_id': device_id,
            'device_name': device.name,
            'device_type': device.device_type,
            'start_time': start_time,
            'data': telemetry_data,
            'count': len(telemetry_data),
            'influxdb_available': influx_service.is_available()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>/latest', methods=['GET'])
def get_device_latest_telemetry(device_id):
    """Get the latest telemetry data for a device"""
    try:
        # Verify device exists
        device = Device.query.get_or_404(device_id)
        
        latest_data = influx_service.get_device_latest_telemetry(str(device_id))
        
        if latest_data:
            return jsonify({
                'device_id': device_id,
                'device_name': device.name,
                'device_type': device.device_type,
                'latest_data': latest_data,
                'influxdb_available': influx_service.is_available()
            }), 200
        else:
            return jsonify({
                'device_id': device_id,
                'device_name': device.name,
                'message': 'No telemetry data found',
                'influxdb_available': influx_service.is_available()
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error getting latest telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>/aggregated', methods=['GET'])
def get_device_aggregated_telemetry(device_id):
    """Get aggregated telemetry data for a device"""
    try:
        # Verify device exists
        device = Device.query.get_or_404(device_id)
        
        field = request.args.get('field', 'temperature')
        aggregation = request.args.get('aggregation', 'mean')
        window = request.args.get('window', '1h')
        start_time = request.args.get('start_time', '-24h')
        
        # Validate aggregation function
        valid_aggregations = ['mean', 'sum', 'count', 'min', 'max', 'first', 'last', 'median']
        if aggregation not in valid_aggregations:
            return jsonify({
                'error': 'Invalid aggregation function',
                'valid_functions': valid_aggregations
            }), 400
        
        aggregated_data = influx_service.get_device_aggregated_data(
            device_id=str(device_id),
            field=field,
            aggregation=aggregation,
            window=window,
            start_time=start_time
        )
        
        return jsonify({
            'device_id': device_id,
            'device_name': device.name,
            'device_type': device.device_type,
            'field': field,
            'aggregation': aggregation,
            'window': window,
            'start_time': start_time,
            'data': aggregated_data,
            'count': len(aggregated_data),
            'influxdb_available': influx_service.is_available()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting aggregated telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device_telemetry(device_id):
    """Delete telemetry data for a device within a time range"""
    try:
        # Verify device exists
        device = Device.query.get_or_404(device_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required with start_time and stop_time'}), 400
        
        start_time = data.get('start_time')
        stop_time = data.get('stop_time')
        
        if not start_time or not stop_time:
            return jsonify({'error': 'start_time and stop_time are required'}), 400
        
        success = influx_service.delete_device_data(
            device_id=str(device_id),
            start_time=start_time,
            stop_time=stop_time
        )
        
        if success:
            current_app.logger.info(f"Telemetry data deleted for device {device.name} (ID: {device_id})")
            return jsonify({
                'message': f'Telemetry data deleted for device {device.name}',
                'device_id': device_id,
                'start_time': start_time,
                'stop_time': stop_time
            }), 200
        else:
            return jsonify({
                'error': 'Failed to delete telemetry data',
                'message': 'InfluxDB may not be available. Check logs for details.'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error deleting telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/status', methods=['GET'])
def get_telemetry_status():
    """Get InfluxDB service status and statistics"""
    try:
        influxdb_available = influx_service.is_available()
        device_count = influx_service.get_device_count() if influxdb_available else 0
        
        return jsonify({
            'influxdb_available': influxdb_available,
            'influxdb_url': influx_service.client.url if influx_service.client else 'Not configured',
            'bucket': influx_service.bucket,
            'organization': influx_service.org,
            'devices_with_telemetry': device_count,
            'status': 'healthy' if influxdb_available else 'unavailable'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry status: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
