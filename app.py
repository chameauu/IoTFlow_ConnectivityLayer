import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from src.config.config import config
from src.models import db
from src.routes.devices import device_bp
from src.routes.admin import admin_bp
from src.utils.logging import setup_logging

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
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])  # Allow frontend
    migrate = Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(device_bp)
    app.register_blueprint(admin_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'message': 'IoT Connectivity Layer is running',
            'version': '1.0.0'
        }), 200
    
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
                'admin': '/api/v1/admin'
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
