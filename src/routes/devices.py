from flask import Blueprint, request, jsonify, current_app
from src.models import Device, DeviceAuth, DeviceConfiguration, db
from src.middleware.auth import authenticate_device, validate_json_payload, rate_limit_device
from src.middleware.monitoring import device_heartbeat_monitor, request_metrics_middleware
from src.middleware.security import security_headers_middleware, input_sanitization_middleware
from src.services.influxdb import InfluxDBService
from datetime import datetime, timezone
import json

# Create blueprint for device routes
device_bp = Blueprint('devices', __name__, url_prefix='/api/v1/devices')

# Initialize InfluxDB service for telemetry queries
influx_service = InfluxDBService()

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
        
        # Get telemetry count from InfluxDB instead of SQLite
        telemetry_count = 0
        try:
            # Query InfluxDB for telemetry count (simplified)
            telemetry_data = influx_service.get_device_telemetry(
                device_id=str(device.id),
                start_time='-30d',  # Last 30 days
                limit=1
            )
            # This is a simplified count - in practice you might want a proper count query
            telemetry_count = len(telemetry_data) if telemetry_data else 0
        except Exception as e:
            current_app.logger.warning(f"Failed to get telemetry count from InfluxDB: {e}")
        
        response = device.to_dict()
        response['telemetry_count'] = telemetry_count
        
        # Handle timezone awareness for last_seen comparison
        is_online = False
        if device.last_seen:
            # Ensure both datetimes are timezone-aware for comparison
            now = datetime.now(timezone.utc)
            last_seen = device.last_seen
            if last_seen.tzinfo is None:
                # If last_seen is naive, assume it's UTC
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            is_online = (now - last_seen).total_seconds() < 300  # 5 minutes
        
        response['is_online'] = is_online
        
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
        
        # Store only in InfluxDB (telemetry data should not be in SQLite)
        timestamp = datetime.now(timezone.utc)
        
        # Store in InfluxDB for time-series analysis
        influx_success = influx_service.write_telemetry_data(
            device_id=str(device.id),
            data=telemetry_payload,
            device_type=device.device_type,
            metadata=data.get('metadata', {}),
            timestamp=timestamp
        )
        
        if not influx_success:
            return jsonify({
                'error': 'Telemetry storage failed',
                'message': 'Failed to store telemetry data in InfluxDB'
            }), 500
        
        # Update device last_seen
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
            'stored_in_influxdb': influx_success
        }), 201
        
    except Exception as e:
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
        start_time = request.args.get('start_time', '-24h')  # Default to last 24 hours
        data_type = request.args.get('type')
        
        # Get telemetry data from InfluxDB
        try:
            telemetry_data = influx_service.get_device_telemetry(
                device_id=str(device.id),
                start_time=start_time,
                limit=limit
            )
            
            # Filter by data type if specified (this would need to be implemented in InfluxDB service)
            if data_type and telemetry_data:
                # Simple filtering - in practice this should be done in the InfluxDB query
                telemetry_data = [record for record in telemetry_data if record.get('data_type') == data_type]
        
        except Exception as e:
            current_app.logger.error(f"Error querying InfluxDB: {str(e)}")
            telemetry_data = []
        
        return jsonify({
            'status': 'success',
            'telemetry': telemetry_data,
            'count': len(telemetry_data),
            'limit': limit,
            'start_time': start_time
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
def update_device_info():
    """Update device information (status, location, versions)"""
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

@device_bp.route('/mqtt-credentials', methods=['GET'])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
def get_mqtt_credentials():
    """Get MQTT connection details for device"""
    try:
        device = request.device
        
        # Return MQTT connection details for anonymous connection
        # Note: Authentication is handled server-side using API key
        credentials = {
            'mqtt_host': current_app.config.get('MQTT_HOST', 'localhost'),
            'mqtt_port': current_app.config.get('MQTT_PORT', 1883),
            'client_id': f"device_{device.id}_{device.name.replace(' ', '_')}",
            'api_key': device.api_key,  # API key for server-side authentication
            'anonymous_connection': True,  # MQTT broker allows anonymous connections
            'authentication_note': 'Use API key for server-side authentication, not MQTT broker auth',
            'topics': {
                'telemetry_publish': f"iotflow/devices/{device.id}/telemetry",
                'status_publish': f"iotflow/devices/{device.id}/status",
                'commands_subscribe': f"iotflow/devices/{device.id}/commands",
                'config_subscribe': f"iotflow/devices/{device.id}/config"
            }
        }
        
        return jsonify({
            'status': 'success',
            'credentials': credentials
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting MQTT credentials: {str(e)}")
        return jsonify({
            'error': 'Failed to get MQTT credentials',
            'message': 'An error occurred while retrieving MQTT credentials'
        }), 500

@device_bp.route('/config', methods=['GET'])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
def get_device_config():
    """Get device configuration"""
    try:
        device = request.device
        
        # Get all active configurations for the device
        configs = DeviceConfiguration.query.filter_by(
            device_id=device.id, 
            is_active=True
        ).all()
        
        config_dict = {}
        for config in configs:
            # Convert value based on data type
            value = config.config_value
            if config.data_type == 'integer':
                value = int(value) if value else 0
            elif config.data_type == 'float':
                value = float(value) if value else 0.0
            elif config.data_type == 'boolean':
                value = value.lower() in ('true', '1', 'yes') if value else False
            elif config.data_type == 'json':
                import json
                try:
                    value = json.loads(value) if value else {}
                except json.JSONDecodeError:
                    value = {}
            
            config_dict[config.config_key] = {
                'value': value,
                'data_type': config.data_type,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            }
        
        return jsonify({
            'status': 'success',
            'device_id': device.id,
            'configuration': config_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting device config: {str(e)}")
        return jsonify({
            'error': 'Failed to get device configuration',
            'message': 'An error occurred while retrieving device configuration'
        }), 500

@device_bp.route('/config', methods=['POST'])
@authenticate_device
@security_headers_middleware()
@request_metrics_middleware()
@validate_json_payload(['config_key', 'config_value'])
@input_sanitization_middleware()
def update_device_config():
    """Update device configuration"""
    try:
        device = request.device
        data = request.validated_json
        
        config_key = data['config_key']
        config_value = str(data['config_value'])
        data_type = data.get('data_type', 'string')
        
        # Check if configuration already exists
        existing_config = DeviceConfiguration.query.filter_by(
            device_id=device.id,
            config_key=config_key
        ).first()
        
        if existing_config:
            # Update existing configuration
            existing_config.config_value = config_value
            existing_config.data_type = data_type
            existing_config.updated_at = datetime.now(timezone.utc)
            existing_config.is_active = True
        else:
            # Create new configuration
            new_config = DeviceConfiguration(
                device_id=device.id,
                config_key=config_key,
                config_value=config_value,
                data_type=data_type
            )
            db.session.add(new_config)
        
        db.session.commit()
        
        current_app.logger.info(f"Configuration updated for device {device.name}: {config_key}")
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration updated successfully',
            'config_key': config_key,
            'config_value': config_value,
            'data_type': data_type
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating device config: {str(e)}")
        return jsonify({
            'error': 'Failed to update configuration',
            'message': 'An error occurred while updating device configuration'
        }), 500
