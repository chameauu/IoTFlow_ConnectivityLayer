from flask import Blueprint, request, jsonify, current_app
from src.models import Device, TelemetryData, db
from src.middleware.auth import authenticate_device, validate_json_payload, rate_limit_device
from datetime import datetime, timezone
import json

# Create blueprint for device routes
device_bp = Blueprint('devices', __name__, url_prefix='/api/v1/devices')

@device_bp.route('/register', methods=['POST'])
@validate_json_payload(['name', 'device_type'])
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
@authenticate_device
def get_device_status():
    """Get current device status"""
    try:
        device = request.device
        
        # Get latest telemetry count
        telemetry_count = TelemetryData.query.filter_by(device_id=device.id).count()
        
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
@authenticate_device
@rate_limit_device(max_requests=100, window=60)
@validate_json_payload(['data'])
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
        
        # Create telemetry record
        telemetry = TelemetryData(
            device_id=device.id,
            payload=telemetry_payload,
            device_metadata=data.get('metadata', {}),
            data_type=data.get('type', 'sensor'),
            timestamp=datetime.now(timezone.utc)
        )
        
        db.session.add(telemetry)
        db.session.commit()
        
        current_app.logger.info(
            f"Telemetry received from device {device.name} (ID: {device.id})"
        )
        
        return jsonify({
            'message': 'Telemetry data received successfully',
            'telemetry_id': telemetry.id,
            'timestamp': telemetry.timestamp.isoformat()
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
    """Get telemetry data for device"""
    try:
        device = request.device
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 records
        offset = int(request.args.get('offset', 0))
        data_type = request.args.get('type')
        
        # Build query
        query = TelemetryData.query.filter_by(device_id=device.id)
        
        if data_type:
            query = query.filter_by(data_type=data_type)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(TelemetryData.timestamp.desc())
        
        # Apply pagination
        telemetry_records = query.offset(offset).limit(limit).all()
        
        # Convert to dict
        telemetry_data = [record.to_dict() for record in telemetry_records]
        
        return jsonify({
            'status': 'success',
            'telemetry': telemetry_data,
            'count': len(telemetry_data),
            'limit': limit,
            'offset': offset
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
@authenticate_device
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
