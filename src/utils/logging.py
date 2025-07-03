import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set logging level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger to capture all loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Configure werkzeug logger (Flask's built-in server)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.addHandler(file_handler)
    
    # Configure MQTT logger specifically
    mqtt_logger = logging.getLogger('src.mqtt.client')
    mqtt_logger.setLevel(log_level)
    mqtt_logger.addHandler(file_handler)
    mqtt_logger.addHandler(console_handler)
    
    return app.logger

def get_logger(name):
    """Get a logger instance for the given name"""
    return logging.getLogger(name)

def log_request(request, response_status=None, execution_time=None):
    """Log HTTP request details"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'method': request.method,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if response_status:
        log_data['status'] = response_status
    
    if execution_time:
        log_data['execution_time'] = f"{execution_time:.3f}s"
    
    logger.info(f"Request: {log_data}")

def log_device_activity(device_id, activity_type, details=None):
    """Log device-specific activities"""
    logger = logging.getLogger('device_activity')
    
    log_data = {
        'device_id': device_id,
        'activity_type': activity_type,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if details:
        log_data['details'] = details
    
    logger.info(f"Device Activity: {log_data}")
