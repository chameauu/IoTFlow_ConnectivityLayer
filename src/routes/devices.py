from flask import Blueprint, request, jsonify, current_app
from src.models import Device, db
from src.middleware.auth import authenticate_device, validate_json_payload, rate_limit_device
from src.middleware.monitoring import device_heartbeat_monitor, request_metrics_middleware
from src.middleware.security import security_headers_middleware, input_sanitization_middleware
from src.services.influxdb import influx_service
from datetime import datetime, timezone
import json

# Create blueprint for device routes
device_bp = Blueprint('devices', __name__, url_prefix='/api/v1/devices')

@device_bp.route('/register', methods=['POST'])
@security_headers_middleware()
@request_metrics_middleware()
@rate_limit_device(max_requests=10, window=300, per_device=False)  # 10 registrations per 5 minutes per IP
@validate_json_payload(['name', 'device_type'])
@input_sanitization_middleware()
def register_device():
    """Register a new IoT device"""
    try:
        data = request.validated_json
        
        # Check if device name already exists
        existing_device = Device.query.filter_by(name=data['name']).first()
        if existing_device:
            return jsonify({
                'error': 'Device name already exists',
                'message': 'Please choose a different device name'
            }), 409
        
        # Create new device
        device = Device(
            name=data['name'],
            description=data.get('description', ''),
            device_type=data['device_type'],
            location=data.get('location', ''),
            firmware_version=data.get('firmware_version', ''),
            hardware_version=data.get('hardware_version', '')
        )
        
        db.session.add(device)
        db.session.commit()
        
        current_app.logger.info(f"New device registered: {device.name} (ID: {device.id})")
        
        response_data = device.to_dict()
        response_data['api_key'] = device.api_key  # Include API key in registration response
        
        return jsonify({
            'message': 'Device registered successfully',
            'device': response_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering device: {str(e)}")
        return jsonify({
            'error': 'Registration failed',
            'message': 'An error occurred while registering the device'
        }), 500

@device_bp.route('/status', methods=['GET'])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
def get_device_status():
    """Get current device status"""
    try:
        device = request.device
        
        # Get latest telemetry count from InfluxDB
        telemetry_count = influx_service.get_device_telemetry_count(str(device.id))
        
        response = device.to_dict()
        response['telemetry_count'] = telemetry_count
        response['is_online'] = (
            device.last_seen and 
            (datetime.now(timezone.utc) - device.last_seen).total_seconds() < 300  # 5 minutes
        )
        
        return jsonify({
            'status': 'success',
            'device': response
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting device status: {str(e)}")
        return jsonify({
            'error': 'Status retrieval failed',
            'message': 'An error occurred while retrieving device status'
        }), 500

@device_bp.route('/telemetry', methods=['POST'])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
@rate_limit_device(max_requests=100, window=60)  # 100 telemetry submissions per minute
@validate_json_payload(['data'])
@input_sanitization_middleware()
def submit_telemetry():
    """Submit telemetry data from device"""
    try:
        device = request.device
        data = request.validated_json
        
        # Validate payload structure
        telemetry_payload = data['data']
        if not isinstance(telemetry_payload, dict):
            return jsonify({
                'error': 'Invalid data format',
                'message': 'Telemetry data must be a JSON object'
            }), 400
        
        # Store only in InfluxDB for time-series analysis
        timestamp = datetime.now(timezone.utc)
        
        # Store in InfluxDB
        influx_success = influx_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_payload,
            device_type=device.device_type,
            metadata=data.get('metadata', {}),
            timestamp=timestamp
        )
        
        if not influx_success:
            return jsonify({
                'error': 'Failed to store telemetry data',
                'message': 'InfluxDB storage failed. Check server logs.'
            }), 500
        
        # Update device last_seen in SQLite
        device.update_last_seen()
        
        current_app.logger.info(
            f"Telemetry received from device {device.name} (ID: {device.id}) - "
            f"InfluxDB: ✓"
        )
        
        return jsonify({
            'message': 'Telemetry data received successfully',
            'device_id': device.id,
            'device_name': device.name,
            'timestamp': timestamp.isoformat(),
            'data_points': len(telemetry_payload),
            'stored_in_influxdb': influx_success
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting telemetry: {str(e)}")
        return jsonify({
            'error': 'Telemetry submission failed',
            'message': 'An error occurred while processing telemetry data'
        }), 500

@device_bp.route('/telemetry', methods=['GET'])
@authenticate_device
def get_telemetry():
    """Get telemetry data for device from InfluxDB"""
    try:
        device = request.device
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 records
        start_time = request.args.get('start_time', '-1h')  # Default to last hour
        
        # Get telemetry data from InfluxDB
        telemetry_data = influx_service.get_device_telemetry(
            device_id=str(device.id),
            start_time=start_time,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'device_id': device.id,
            'device_name': device.name,
            'telemetry': telemetry_data,
            'count': len(telemetry_data),
            'start_time': start_time,
            'limit': limit
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving telemetry: {str(e)}")
        return jsonify({
            'error': 'Telemetry retrieval failed',
            'message': 'An error occurred while retrieving telemetry data'
        }), 500

@device_bp.route('/config', methods=['PUT'])
@authenticate_device
@validate_json_payload(['status'])
def update_device_config():
    """Update device configuration"""
    try:
        device = request.device
        data = request.validated_json
        
        # Update allowed fields
        if 'status' in data and data['status'] in ['active', 'inactive', 'maintenance']:
            device.status = data['status']
        
        if 'location' in data:
            device.location = data['location']
        
        if 'firmware_version' in data:
            device.firmware_version = data['firmware_version']
        
        if 'hardware_version' in data:
            device.hardware_version = data['hardware_version']
        
        device.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        current_app.logger.info(f"Device configuration updated: {device.name} (ID: {device.id})")
        
        return jsonify({
            'message': 'Device configuration updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device config: {str(e)}")
        return jsonify({
            'error': 'Configuration update failed',
            'message': 'An error occurred while updating device configuration'
        }), 500

@device_bp.route('/heartbeat', methods=['POST'])
@security_headers_middleware()
@request_metrics_middleware()
@authenticate_device
@device_heartbeat_monitor()
@rate_limit_device(max_requests=30, window=60)  # 30 heartbeats per minute
def device_heartbeat():
    """Simple heartbeat endpoint to check device connectivity"""
    try:
        device = request.device
        
        # Device last_seen is already updated by authenticate_device decorator
        
        return jsonify({
            'message': 'Heartbeat received',
            'device_id': device.id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'online'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing heartbeat: {str(e)}")
        return jsonify({
            'error': 'Heartbeat failed',
            'message': 'An error occurred while processing heartbeat'
        }), 500
