# Copyright (c) 2025 Isaac Gounton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import logging
from flask import Blueprint, jsonify
from config.config import LOCAL_STORAGE_PATH
from config.version import BUILD_NUMBER

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint that validates the application is running correctly.
    Returns detailed status information for monitoring and troubleshooting.
    """
    try:
        health_status = {
            "status": "healthy",
            "version": BUILD_NUMBER,
            "services": {
                "api": "healthy",
                "storage": "healthy",
                "video_apis": "healthy"
            },
            "configuration": {
                "local_storage_path": LOCAL_STORAGE_PATH,
                "video_apis_available": [],
                "cloud_storage": "none"
            },
            "warnings": []
        }
        
        # Check storage directories
        required_dirs = [
            LOCAL_STORAGE_PATH,
            f"{LOCAL_STORAGE_PATH}/assets",
            f"{LOCAL_STORAGE_PATH}/music",
            f"{LOCAL_STORAGE_PATH}/jobs"
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                health_status["services"]["storage"] = "degraded"
                health_status["warnings"].append(f"Directory missing: {dir_path}")
            elif not os.access(dir_path, os.W_OK):
                health_status["services"]["storage"] = "degraded"
                health_status["warnings"].append(f"Directory not writable: {dir_path}")
        
        # Check video API configuration
        pexels_configured = bool(os.getenv('PEXELS_API_KEY'))
        pixabay_configured = bool(os.getenv('PIXABAY_API_KEY'))
        
        if pexels_configured:
            health_status["configuration"]["video_apis_available"].append("pexels")
        if pixabay_configured:
            health_status["configuration"]["video_apis_available"].append("pixabay")
        
        if not pexels_configured and not pixabay_configured:
            health_status["services"]["video_apis"] = "degraded"
            health_status["warnings"].append("No video search APIs configured - using default videos only")
        
        # Check cloud storage configuration
        gcp_configured = bool(os.getenv('GCP_BUCKET_NAME')) and bool(os.getenv('GCP_SA_CREDENTIALS'))
        s3_configured = bool(os.getenv('S3_ENDPOINT_URL')) and bool(os.getenv('S3_ACCESS_KEY'))
        
        if gcp_configured:
            health_status["configuration"]["cloud_storage"] = "gcp"
        elif s3_configured:
            health_status["configuration"]["cloud_storage"] = "s3"
        else:
            health_status["warnings"].append("No cloud storage configured - using local storage only")
        
        # Check placeholder assets
        placeholder_video = os.getenv('DEFAULT_PLACEHOLDER_VIDEO', f'{LOCAL_STORAGE_PATH}/assets/placeholder.mp4')
        placeholder_music = os.getenv('DEFAULT_BACKGROUND_MUSIC', f'{LOCAL_STORAGE_PATH}/music/default.wav')
        
        if not os.path.exists(placeholder_video):
            health_status["warnings"].append(f"Placeholder video missing: {placeholder_video}")
        if not os.path.exists(placeholder_music):
            health_status["warnings"].append(f"Placeholder music missing: {placeholder_music}")
        
        # Overall status
        if health_status["services"]["storage"] == "degraded":
            health_status["status"] = "degraded"
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "version": BUILD_NUMBER
        }), 500

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 if the application is ready to serve requests.
    """
    try:
        # Basic readiness checks
        from config.config import API_KEY
        
        if not API_KEY:
            return jsonify({"status": "not ready", "reason": "API_KEY not configured"}), 503
        
        if not os.path.exists(LOCAL_STORAGE_PATH):
            return jsonify({"status": "not ready", "reason": "Storage path not available"}), 503
        
        return jsonify({"status": "ready"})
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({"status": "not ready", "error": str(e)}), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if the application process is alive.
    """
    return jsonify({"status": "alive", "version": BUILD_NUMBER})
