"""
Comprehensive error handling and security middleware
"""

import re
import html
import json
import traceback
from flask import current_app, request, jsonify, g
from functools import wraps
from datetime import datetime


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_validation_error(error_msg, field=None):
        """Handle validation errors with structured response"""
        response = {
            'error': 'Validation Error',
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path
        }
        
        if field:
            response['field'] = field
        
        return jsonify(response), 400
    
    @staticmethod
    def handle_authentication_error(error_msg='Authentication required'):
        """Handle authentication errors"""
        response = {
            'error': 'Authentication Error',
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path
        }
        
        return jsonify(response), 401
    
    @staticmethod
    def handle_authorization_error(error_msg='Access denied'):
        """Handle authorization errors"""
        response = {
            'error': 'Authorization Error',
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path
        }
        
        return jsonify(response), 403
    
    @staticmethod
    def handle_not_found_error(resource='Resource'):
        """Handle not found errors"""
        response = {
            'error': 'Not Found',
            'message': f'{resource} not found',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path
        }
        
        return jsonify(response), 404
    
    @staticmethod
    def handle_server_error(error_msg='Internal server error', include_trace=False):
        """Handle server errors"""
        response = {
            'error': 'Server Error',
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path,
            'request_id': getattr(g, 'request_id', None)
        }
        
        if include_trace and current_app.debug:
            response['trace'] = traceback.format_exc()
        
        return jsonify(response), 500


class InputSanitizer:
    """Input sanitization and validation"""
    
    # Dangerous patterns that could indicate injection attempts
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
        r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
        r"(--|\/\*|\*\/)",
        r"(\b(EXEC|EXECUTE|sp_|xp_)\b)",
        r"(;|\||&)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
    ]
    
    @staticmethod
    def sanitize_string(value, max_length=1000):
        """Sanitize string input"""
        if not isinstance(value, str):
            return value
        
        # Trim whitespace
        value = value.strip()
        
        # Limit length
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # HTML encode to prevent XSS
        value = html.escape(value)
        
        # Check for dangerous patterns
        InputSanitizer._check_sql_injection(value)
        InputSanitizer._check_xss(value)
        
        return value
    
    @staticmethod
    def _check_sql_injection(value):
        """Check for SQL injection patterns"""
        value_upper = value.upper()
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                current_app.logger.warning(
                    f"Potential SQL injection attempt: {value[:100]} from {request.remote_addr}"
                )
                raise ValueError("Invalid input detected")
    
    @staticmethod
    def _check_xss(value):
        """Check for XSS patterns"""
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                current_app.logger.warning(
                    f"Potential XSS attempt: {value[:100]} from {request.remote_addr}"
                )
                raise ValueError("Invalid input detected")
    
    @staticmethod
    def sanitize_json_payload(data):
        """Recursively sanitize JSON payload"""
        if isinstance(data, dict):
            return {key: InputSanitizer.sanitize_json_payload(value) 
                   for key, value in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_json_payload(item) for item in data]
        elif isinstance(data, str):
            return InputSanitizer.sanitize_string(data)
        else:
            return data


def security_headers_middleware():
    """Add security headers to responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers (similar to Helmet.js)
            if hasattr(response, 'headers'):
                # Prevent clickjacking
                response.headers['X-Frame-Options'] = 'DENY'
                
                # XSS protection
                response.headers['X-XSS-Protection'] = '1; mode=block'
                
                # Content type sniffing protection
                response.headers['X-Content-Type-Options'] = 'nosniff'
                
                # Referrer policy
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
                # Content Security Policy
                response.headers['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data:; "
                    "connect-src 'self';"
                )
                
                # HSTS (if HTTPS)
                if request.is_secure:
                    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                
                # Remove server information
                response.headers.pop('Server', None)
            
            return response
        
        return decorated_function
    return decorator


def input_sanitization_middleware():
    """Sanitize all input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Sanitize JSON payload if present
            if request.is_json and hasattr(request, 'validated_json'):
                try:
                    request.validated_json = InputSanitizer.sanitize_json_payload(
                        request.validated_json
                    )
                except ValueError as e:
                    return ErrorHandler.handle_validation_error(str(e))
            
            # Sanitize query parameters
            try:
                sanitized_args = {}
                for key, value in request.args.items():
                    sanitized_args[key] = InputSanitizer.sanitize_string(value, max_length=500)
                # Note: Flask's request.args is immutable, so we store in g
                g.sanitized_args = sanitized_args
            except ValueError as e:
                return ErrorHandler.handle_validation_error(str(e))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def request_id_middleware():
    """Add unique request ID for tracking"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import uuid
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            
            # Add to response headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-Request-ID'] = request_id
            
            return response
        
        return decorated_function
    return decorator


def comprehensive_error_handler(app):
    """Register comprehensive error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return ErrorHandler.handle_validation_error("Bad request")
    
    @app.errorhandler(401)
    def unauthorized(error):
        return ErrorHandler.handle_authentication_error()
    
    @app.errorhandler(403)
    def forbidden(error):
        return ErrorHandler.handle_authorization_error()
    
    @app.errorhandler(404)
    def not_found(error):
        return ErrorHandler.handle_not_found_error()
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests',
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {str(error)}", exc_info=True)
        return ErrorHandler.handle_server_error(
            include_trace=app.debug
        )
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return ErrorHandler.handle_server_error(
            f"An unexpected error occurred: {str(error)}", 
            include_trace=app.debug
        )
