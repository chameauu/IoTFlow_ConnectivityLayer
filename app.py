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
    
    # Initialize MQTT service
    try:
        mqtt_service = create_mqtt_service(app.config.mqtt_config)
        app.mqtt_service = mqtt_service
        
        # Connect to MQTT broker
        if mqtt_service.connect():
            app.logger.info("MQTT service initialized and connected successfully")
            
            # Add telemetry callback to store data in database
            def handle_telemetry_data(telemetry_data):
                """Handle incoming telemetry data"""
                try:
                    # TODO: Store telemetry data in database
                    # This would integrate with your existing device models
                    app.logger.debug(f"Received telemetry: {telemetry_data}")
                except Exception as e:
                    app.logger.error(f"Error processing telemetry: {e}")
            
            # Add status callback to update device status
            def handle_device_status(status_data):
                """Handle device status updates"""
                try:
                    # TODO: Update device status in database
                    app.logger.debug(f"Device status update: {status_data}")
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
