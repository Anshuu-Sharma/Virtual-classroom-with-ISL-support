"""
RESTful API endpoints
Organized API endpoint definitions
"""

from flask import Blueprint, jsonify, request
from functools import wraps

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def validate_json(f):
    """Decorator to validate JSON request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    }), 200

