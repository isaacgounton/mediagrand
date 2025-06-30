# Copyright (c) 2025 Isaac Gounton

from functools import wraps
from flask import request, jsonify, has_request_context, g
from config import API_KEY
from models.api_keys import APIKeyManager
import logging
import time
from collections import defaultdict, deque
from threading import Lock

api_manager = APIKeyManager()

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.lock = Lock()
    
    def is_allowed(self, key: str, limit: int, window: int = 3600) -> bool:
        """Check if request is within rate limit (requests per window in seconds)"""
        with self.lock:
            now = time.time()
            window_start = now - window
            
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()
            
            # Check if under limit
            if len(self.requests[key]) >= limit:
                return False
            
            # Record this request
            self.requests[key].append(now)
            return True

rate_limiter = RateLimiter()

def enhanced_authenticate(func):
    """Enhanced authentication supporting both legacy and new API key systems"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we're in a Flask request context
        if not has_request_context():
            # We're in a worker context (no request context)
            # Authentication was already performed when the task was queued
            return func(*args, **kwargs)
        
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                "error": "Missing API key",
                "message": "X-API-Key header is required"
            }), 401
        
        # Try enhanced authentication first (new system)
        try:
            key_info = api_manager.validate_api_key(api_key)
            if key_info:
                # Check rate limiting
                if not rate_limiter.is_allowed(f"key_{key_info['id']}", key_info['rate_limit']):
                    return jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Rate limit of {key_info['rate_limit']} requests/hour exceeded"
                    }), 429
                
                # Store key info in Flask's g object for use in the route
                g.api_key_info = key_info
                g.user_id = key_info['user_id']
                g.permissions = key_info['permissions'].split(',')
                
                # Log usage
                try:
                    api_manager.log_api_usage(
                        key_info['id'],
                        request.endpoint or request.path,
                        request.method,
                        200  # Will be updated after response if needed
                    )
                except Exception as e:
                    logging.warning(f"Failed to log API usage: {e}")
                
                return func(*args, **kwargs)
        except Exception as e:
            logging.warning(f"Enhanced authentication failed, trying legacy: {e}")
            # Continue to legacy authentication
        
        # Fallback to legacy authentication (single API key)
        if api_key == API_KEY:
            # Store legacy info in g object
            g.api_key_info = {
                'id': None,
                'user_id': None,
                'username': 'legacy_user',
                'permissions': 'admin'
            }
            g.user_id = None
            g.permissions = ['admin']
            return func(*args, **kwargs)
        
        # Authentication failed
        return jsonify({
            "error": "Invalid API key",
            "message": "The provided API key is invalid or expired"
        }), 401
    
    return wrapper

def require_permission(permission: str):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'permissions'):
                return jsonify({
                    "error": "Authentication required",
                    "message": "This endpoint requires authentication"
                }), 401
            
            # Admin permission allows everything
            if 'admin' in g.permissions:
                return func(*args, **kwargs)
            
            # Check specific permission
            if permission not in g.permissions:
                return jsonify({
                    "error": "Insufficient permissions",
                    "message": f"This endpoint requires '{permission}' permission"
                }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_api_response(response):
    """Log API response status (to be called after request)"""
    if hasattr(g, 'api_key_info') and g.api_key_info and g.api_key_info.get('id'):
        try:
            api_manager.log_api_usage(
                g.api_key_info['id'],
                request.endpoint or request.path,
                request.method,
                response.status_code
            )
        except Exception as e:
            logging.warning(f"Failed to log API response: {e}")
    return response