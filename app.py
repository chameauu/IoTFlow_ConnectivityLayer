import os
import redis
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from src.config.config import config
from src.models import db
from src.routes.devices import device_bp
from src.routes.admin import admin_bp
from src.routes.mqtt import mqtt_bp
from src.routes.telemetry import telemetry_bp
from src.utils.logging import setup_logging
from src.middleware.monitoring import HealthMonitor
from src.middleware.security import comprehensive_error_handler, security_headers_middleware
from src.mqtt.client import create_mqtt_service

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Enhanced CORS configuration
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-API-Key"],
         expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )
    
    migrate = Migrate(app, db)
    
    # Initialize Redis client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()  # Test connection
        app.redis_client = redis_client
        app.logger.info("Redis connection established")
    except Exception as e:
        app.logger.warning(f"Redis connection failed: {str(e)}")
        app.redis_client = None
    
    # Register error handlers
    comprehensive_error_handler(app)
    
    # Register blueprints
    app.register_blueprint(device_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mqtt_bp)
    app.register_blueprint(telemetry_bp)
    
    # Initialize MQTT service
    try:
        # Get MQTT config from the config object
        config_obj = config[config_name or 'development']()
        mqtt_service = create_mqtt_service(config_obj.mqtt_config)
        app.mqtt_service = mqtt_service
        
        # Connect to MQTT broker
        if mqtt_service.connect():
            app.logger.info("MQTT service initialized and connected successfully")
            
            # Add telemetry callback to store data in database
            def handle_telemetry_data(telemetry_data):
                """Handle incoming telemetry data with authentication"""
                try:
                    app.logger.info(f"Received MQTT telemetry: {telemetry_data}")
                    
                    # Check if data is in nested format (from MQTT client handler)
                    if 'data' in telemetry_data and isinstance(telemetry_data['data'], dict):
                        # Extract from nested structure
                        payload = telemetry_data['data']
                        device_id = payload.get('device_id') or telemetry_data.get('device_id')
                        device_type = payload.get('device_type', 'unknown')
                        measurements = payload.get('measurements', {})
                        status = payload.get('status', {})
                        metadata = payload.get('metadata', {})
                        timestamp = payload.get('timestamp') or telemetry_data.get('timestamp')
                        api_key = payload.get('api_key') or telemetry_data.get('api_key')
                        
                        app.logger.info(f"Processing nested MQTT payload: {payload}")
                    else:
                        # Extract data directly from telemetry payload
                        device_id = telemetry_data.get('device_id')
                        device_type = telemetry_data.get('device_type', 'unknown')
                        measurements = telemetry_data.get('measurements', {})
                        status = telemetry_data.get('status', {})
                        metadata = telemetry_data.get('metadata', {})
                        timestamp = telemetry_data.get('timestamp')
                        api_key = telemetry_data.get('api_key')
                    
                    # Validate required fields
                    if not device_id or not measurements:
                        app.logger.warning("Invalid MQTT telemetry data: missing device_id or measurements")
                        return
                    
                    # SECURITY CHECK: Validate device is registered and API key is correct
                    with app.app_context():
                        from src.models import Device
                        
                        # Method 1: If API key is provided, authenticate with it
                        if api_key:
                            device = Device.query.filter_by(api_key=api_key).first()
                            if not device:
                                app.logger.warning(f"MQTT Authentication failed: Invalid API key for device_id {device_id}")
                                return
                            if device.status != 'active':
                                app.logger.warning(f"MQTT Authentication failed: Device {device_id} is {device.status}")
                                return
                            # Ensure device_id matches
                            if str(device.id) != str(device_id):
                                app.logger.warning(f"MQTT Authentication failed: Device ID mismatch. API key belongs to device {device.id}, but device_id {device_id} was provided")
                                return
                        
                        # Method 2: If no API key, check if device_id exists and is registered
                        else:
                            device = Device.query.filter_by(id=device_id).first()
                            if not device:
                                app.logger.warning(f"MQTT Authentication failed: Device {device_id} not registered in database")
                                return
                            if device.status != 'active':
                                app.logger.warning(f"MQTT Authentication failed: Device {device_id} is {device.status}")
                                return
                        
                        # Update device last_seen timestamp
                        device.update_last_seen()
                        app.logger.info(f"MQTT Authentication successful for device {device.name} (ID: {device.id})")
                    
                    # Store in InfluxDB
                    if not device_id or not measurements:
                        app.logger.warning("Invalid MQTT telemetry data: missing device_id or measurements")
                        return
                    
                    # Store in InfluxDB
                    from src.services.influxdb import InfluxDBService
                    influx_service = InfluxDBService()
                    
                    # Store measurements
                    influx_success = influx_service.write_telemetry_data(
                        device_id=device_id,
                        data=measurements,
                        device_type=device_type,
                        metadata=metadata,
                        timestamp=timestamp
                    )
                    
                    # Store status data if present
                    if status and isinstance(status, dict):
                        influx_service.write_telemetry_data(
                            device_id=device_id,
                            data=status,
                            device_type=device_type,
                            metadata={"data_type": "status", **metadata} if metadata else {"data_type": "status"},
                            timestamp=timestamp
                        )
                    
                    if influx_success:
                        app.logger.info(f"MQTT telemetry data for {device_id} stored in InfluxDB")
                    else:
                        app.logger.warning(f"Failed to store MQTT telemetry for {device_id} in InfluxDB")
                        
                except Exception as e:
                    app.logger.error(f"Error processing MQTT telemetry: {e}")
            
            # Add status callback to update device status
            def handle_device_status(status_data):
                """Handle device status updates with authentication"""
                try:
                    app.logger.info(f"Received device status update: {status_data}")
                    
                    # Extract data
                    device_id = status_data.get('device_id')
                    status = status_data.get('status')
                    api_key = status_data.get('api_key')
                    
                    if not device_id or not status:
                        app.logger.warning("Invalid status update: missing device_id or status")
                        return
                    
                    # SECURITY CHECK: Validate device is registered
                    with app.app_context():
                        from src.models import Device
                        
                        # Method 1: If API key is provided, authenticate with it
                        if api_key:
                            device = Device.query.filter_by(api_key=api_key).first()
                            if not device:
                                app.logger.warning(f"MQTT Status Authentication failed: Invalid API key for device_id {device_id}")
                                return
                            if str(device.id) != str(device_id):
                                app.logger.warning(f"MQTT Status Authentication failed: Device ID mismatch")
                                return
                        
                        # Method 2: If no API key, check if device_id exists and is registered
                        else:
                            device = Device.query.filter_by(id=device_id).first()
                            if not device:
                                app.logger.warning(f"MQTT Status Authentication failed: Device {device_id} not registered")
                                return
                        
                        # Update device last_seen timestamp
                        device.update_last_seen()
                        app.logger.info(f"MQTT Status Authentication successful for device {device.name}")
                    
                    # Store status in InfluxDB
                    from src.services.influxdb import InfluxDBService
                    influx_service = InfluxDBService()
                    
                    # Create a data point for the status
                    from datetime import datetime
                    status_data = {
                        "status": status,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    influx_success = influx_service.write_telemetry_data(
                        device_id=device_id,
                        data=status_data,
                        device_type="device_status",
                        metadata={"data_type": "device_status"},
                    )
                    
                    if influx_success:
                        app.logger.info(f"Device status for {device_id} updated to {status}")
                    else:
                        app.logger.warning(f"Failed to update status for device {device_id}")
                        
                except Exception as e:
                    app.logger.error(f"Error processing device status: {e}")
            
            # Register callbacks
            mqtt_service.add_telemetry_callback(handle_telemetry_data)
            mqtt_service.add_status_callback(handle_device_status)
            
        else:
            app.logger.warning("Failed to connect to MQTT broker")
            
    except Exception as e:
        app.logger.error(f"Failed to initialize MQTT service: {str(e)}")
        app.mqtt_service = None
    
    # Enhanced health check endpoint
    @app.route('/health', methods=['GET'])
    @security_headers_middleware()
    def health_check():
        """Comprehensive health check endpoint"""
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        if detailed:
            return jsonify(HealthMonitor.get_system_health())
        else:
            return jsonify({
                'status': 'healthy',
                'message': 'IoT Connectivity Layer is running',
                'version': '1.0.0'
            }), 200
    
    # Detailed system status endpoint
    @app.route('/status', methods=['GET'])
    @security_headers_middleware()
    def system_status():
        """Detailed system status and metrics"""
        return jsonify(HealthMonitor.get_system_health())
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'name': 'IoT Device Connectivity Layer',
            'version': '1.0.0',
            'description': 'REST API for IoT device connectivity and telemetry data management',
            'endpoints': {
                'health': '/health',
                'devices': '/api/v1/devices',
                'admin': '/api/v1/admin',
                'mqtt': '/api/v1/mqtt'
            },
            'documentation': 'See README.md for API documentation'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid'
        }), 400
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.logger.info(f"Starting IoT Connectivity Layer on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
