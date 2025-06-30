# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint, render_template, request, jsonify
from models.api_keys import APIKeyManager
from services.enhanced_authentication import enhanced_authenticate, require_permission
import logging

api_keys_bp = Blueprint('api_keys', __name__)
api_manager = APIKeyManager()

@api_keys_bp.route('/admin/api-keys')
def dashboard():
    """API Key Management Dashboard - Authentication handled by frontend"""
    return render_template('admin/api_keys.html')

@api_keys_bp.route('/v1/admin/test', methods=['GET'])
def test_basic():
    """Basic test endpoint - NO AUTH"""
    return jsonify({"status": "ok", "message": "API is working"})

@api_keys_bp.route('/v1/admin/debug', methods=['GET'])
def debug_status():
    """Debug endpoint to check authentication and database status - NO AUTH for testing"""
    from config import API_KEY as LEGACY_KEY
    api_key = request.headers.get('X-API-Key')
    
    try:
        users = api_manager.get_all_users()
        return jsonify({
            "status": "ok",
            "database_connected": True,
            "user_count": len(users),
            "users": users[:5],  # First 5 users for debugging
            "auth_info": {
                "api_key_provided": bool(api_key),
                "api_key_length": len(api_key) if api_key else 0,
                "legacy_key_available": bool(LEGACY_KEY),
                "legacy_key_matches": api_key == LEGACY_KEY if api_key and LEGACY_KEY else False
            }
        })
    except Exception as e:
        logging.error(f"Debug error: {e}")
        return jsonify({
            "status": "error",
            "database_connected": False,
            "error": str(e),
            "auth_info": {
                "api_key_provided": bool(api_key),
                "api_key_length": len(api_key) if api_key else 0,
                "legacy_key_available": bool(LEGACY_KEY) if 'LEGACY_KEY' in locals() else False
            }
        }), 500

@api_keys_bp.route('/v1/admin/users', methods=['GET'])
@enhanced_authenticate
def get_users():
    """Get all users"""
    try:
        users = api_manager.get_all_users()
        return jsonify({"users": users})
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

@api_keys_bp.route('/v1/admin/users', methods=['POST'])
@enhanced_authenticate
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return jsonify({"error": "Username and email are required"}), 400
        
        user_id = api_manager.create_user(username, email)
        return jsonify({"user_id": user_id, "message": "User created successfully"})
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return jsonify({"error": "Failed to create user"}), 500

@api_keys_bp.route('/v1/admin/users/<int:user_id>/api-keys', methods=['GET'])
@enhanced_authenticate
def get_user_api_keys(user_id):
    """Get API keys for a specific user"""
    try:
        api_keys = api_manager.get_user_api_keys(user_id)
        return jsonify({"api_keys": api_keys})
    except Exception as e:
        logging.error(f"Error fetching API keys: {e}")
        return jsonify({"error": "Failed to fetch API keys"}), 500

@api_keys_bp.route('/v1/admin/users/<int:user_id>/api-keys', methods=['POST'])
@enhanced_authenticate
def create_api_key(user_id):
    """Create a new API key for a user"""
    try:
        data = request.get_json()
        key_name = data.get('key_name')
        permissions = data.get('permissions', 'read,write')
        rate_limit = data.get('rate_limit', 1000)
        expires_days = data.get('expires_days')
        
        if not key_name:
            return jsonify({"error": "Key name is required"}), 400
        
        full_key = api_manager.create_api_key(
            user_id=user_id,
            key_name=key_name,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_days=expires_days
        )
        
        return jsonify({
            "api_key": full_key,
            "message": "API key created successfully",
            "warning": "Save this key securely - it won't be shown again"
        })
    except Exception as e:
        logging.error(f"Error creating API key: {e}")
        return jsonify({"error": "Failed to create API key"}), 500

@api_keys_bp.route('/v1/admin/users/<int:user_id>/api-keys/<int:key_id>', methods=['DELETE'])
@enhanced_authenticate
def revoke_api_key(user_id, key_id):
    """Revoke an API key"""
    try:
        success = api_manager.revoke_api_key(key_id, user_id)
        if success:
            return jsonify({"message": "API key revoked successfully"})
        else:
            return jsonify({"error": "API key not found"}), 404
    except Exception as e:
        logging.error(f"Error revoking API key: {e}")
        return jsonify({"error": "Failed to revoke API key"}), 500

@api_keys_bp.route('/v1/admin/api-keys/<int:key_id>/usage', methods=['GET'])
@enhanced_authenticate
def get_api_key_usage(key_id):
    """Get usage statistics for an API key"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = api_manager.get_usage_stats(key_id, days)
        return jsonify({"stats": stats})
    except Exception as e:
        logging.error(f"Error fetching usage stats: {e}")
        return jsonify({"error": "Failed to fetch usage statistics"}), 500