from functools import wraps
from flask import request, jsonify, current_app
import hashlib
import time
from src.models import Device, DeviceAuth, db

def hash_api_key(api_key):
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def authenticate_device(f):
    """Decorator to authenticate device using API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header'
            }), 401
        
        # Find device by API key
        device = Device.query.filter_by(api_key=api_key).first()
        
        if not device:
            current_app.logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
        
        if device.status != 'active':
            return jsonify({
                'error': 'Device inactive',
                'message': f'Device is currently {device.status}'
            }), 403
        
        # Update last seen timestamp
        device.update_last_seen()
        
        # Add device to request context
        request.device = device
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit_device(max_requests=60, window=60):
    """Rate limiting decorator for device endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'device'):
                return jsonify({'error': 'Authentication required'}), 401
            
            device_id = request.device.id
            current_time = int(time.time())
            window_start = current_time - window
            
            # Simple in-memory rate limiting (in production, use Redis)
            cache_key = f"rate_limit_{device_id}_{current_time // window}"
            
            # For now, we'll skip the actual rate limiting implementation
            # In production, implement with Redis or similar
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json_payload(required_fields=None):
    """Decorator to validate JSON payload"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Invalid content type',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Invalid JSON',
                    'message': 'Request body must contain valid JSON'
                }), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'message': f'Required fields: {", ".join(missing_fields)}'
                    }), 400
            
            request.validated_json = data
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_request_middleware():
    """Middleware to log all requests"""
    def middleware(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Log request
            current_app.logger.info(
                f"Request: {request.method} {request.path} from {request.remote_addr}"
            )
            
            # Execute the request
            response = f(*args, **kwargs)
            
            # Log response time
            execution_time = time.time() - start_time
            current_app.logger.info(
                f"Response: {request.method} {request.path} completed in {execution_time:.3f}s"
            )
            
            return response
        
        return decorated_function
    return middleware
