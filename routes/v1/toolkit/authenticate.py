# Copyright (c) 2025 Isaac Gounton

from flask import Blueprint, request, g
from utils.app_utils import queue_task_wrapper
from services.enhanced_authentication import enhanced_authenticate, require_permission

v1_toolkit_auth_bp = Blueprint('v1_toolkit_auth', __name__)

@v1_toolkit_auth_bp.route('/v1/toolkit/authenticate', methods=['GET'])
@enhanced_authenticate
@require_permission('read')
@queue_task_wrapper(bypass_queue=True)
def authenticate_endpoint(job_id=None, data=None, **kwargs):
    """Enhanced authentication endpoint that provides detailed user information"""
    
    # Get user info from the enhanced authentication
    user_info = {
        "status": "Authorized",
        "message": "Authentication successful",
        "user": {
            "id": g.user_id,
            "username": g.api_key_info.get('username', 'Unknown'),
            "permissions": g.permissions
        },
        "api_key": {
            "id": g.api_key_info.get('id'),
            "name": g.api_key_info.get('key_name'),
            "rate_limit": g.api_key_info.get('rate_limit'),
            "expires_at": g.api_key_info.get('expires_at')
        }
    }
    
    return user_info, "/v1/toolkit/authenticate", 200
