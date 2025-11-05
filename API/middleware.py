"""
API Middleware
CORS, authentication, and other middleware
"""

from flask import request
from functools import wraps


def cors_headers(response):
    """Add CORS headers to response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def validate_request_json(required_fields=None):
    """Decorator to validate request JSON with required fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return {'error': 'Content-Type must be application/json'}, 400
            
            data = request.get_json()
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return {'error': f'Missing required fields: {", ".join(missing)}'}, 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

