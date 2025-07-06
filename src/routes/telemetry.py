from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from src.services.iotdb import IoTDBService
from src.models import Device, db

# Create blueprint for telemetry routes
telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/v1/telemetry')

# Initialize IoTDB service
iotdb_service = IoTDBService()

# Helper to get device by API key and check access
def get_authenticated_device(device_id=None):
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return None, jsonify({'error': 'API key required'}), 401
    device = Device.query.filter_by(api_key=api_key).first()
    if not device:
        return None, jsonify({'error': 'Invalid API key'}), 401
    if device_id is not None and int(device.id) != int(device_id):
        return None, jsonify({'error': 'Forbidden: device mismatch'}), 403
    return device, None, None

@telemetry_bp.route('', methods=['POST'])
def store_telemetry():
    """Store telemetry data in IoTDB"""
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
        
        # Store in IoTDB
        success = iotdb_service.write_telemetry_data(
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
                'message': 'IoTDB may not be available. Check logs for details.'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error storing telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>', methods=['GET'])
def get_device_telemetry(device_id):
    """Get telemetry data for a specific device"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        telemetry_data = iotdb_service.get_device_telemetry(
            device_id=str(device_id),
            start_time=request.args.get('start_time', '-1h'),
            limit=min(int(request.args.get('limit', 1000)), 10000)
        )
        return jsonify({
            'device_id': device_id,
            'device_name': device.name,
            'device_type': device.device_type,
            'start_time': request.args.get('start_time', '-1h'),
            'data': telemetry_data,
            'count': len(telemetry_data),
            'iotdb_available': iotdb_service.is_available()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>/latest', methods=['GET'])
def get_device_latest_telemetry(device_id):
    """Get the latest telemetry data for a device"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        latest_data = iotdb_service.get_device_latest_telemetry(str(device_id))
        if latest_data:
            return jsonify({
                'device_id': device_id,
                'device_name': device.name,
                'device_type': device.device_type,
                'latest_data': latest_data,
                'iotdb_available': iotdb_service.is_available()
            }), 200
        else:
            return jsonify({
                'device_id': device_id,
                'device_name': device.name,
                'message': 'No telemetry data found',
                'iotdb_available': iotdb_service.is_available()
            }), 404
    except Exception as e:
        current_app.logger.error(f"Error getting latest telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>/aggregated', methods=['GET'])
def get_device_aggregated_telemetry(device_id):
    """Get aggregated telemetry data for a device"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        field = request.args.get('field', 'temperature')
        aggregation = request.args.get('aggregation', 'mean')
        window = request.args.get('window', '1h')
        start_time = request.args.get('start_time', '-24h')
        valid_aggregations = ['mean', 'sum', 'count', 'min', 'max', 'first', 'last', 'median']
        if aggregation not in valid_aggregations:
            return jsonify({
                'error': 'Invalid aggregation function',
                'valid_functions': valid_aggregations
            }), 400
        aggregated_data = iotdb_service.get_device_aggregated_data(
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
            'iotdb_available': iotdb_service.is_available()
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting aggregated telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device_telemetry(device_id):
    """Delete telemetry data for a device within a time range"""
    device, err, code = get_authenticated_device(device_id)
    if err:
        return err, code
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required with start_time and stop_time'}), 400
        start_time = data.get('start_time')
        stop_time = data.get('stop_time')
        if not start_time or not stop_time:
            return jsonify({'error': 'start_time and stop_time are required'}), 400
        success = iotdb_service.delete_device_data(
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
                'message': 'IoTDB may not be available. Check logs for details.'
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error deleting telemetry: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@telemetry_bp.route('/status', methods=['GET'])
def get_telemetry_status():
    """Get IoTDB service status and statistics"""
    try:
        from src.config.iotdb_config import iotdb_config
        
        iotdb_available = iotdb_service.is_available()
        
        # Get basic statistics
        total_devices = Device.query.count()
        
        return jsonify({
            'iotdb_available': iotdb_available,
            'iotdb_host': iotdb_config.host,
            'iotdb_port': iotdb_config.port,
            'iotdb_database': iotdb_config.database,
            'total_devices': total_devices,
            'status': 'healthy' if iotdb_available else 'unavailable'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting telemetry status: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
