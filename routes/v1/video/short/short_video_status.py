# Copyright (c) 2025 Stephen G. Pope
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

from flask import Blueprint, request
from app_utils import queue_task_wrapper
import logging
from services.authentication import authenticate
from services.v1.video.short.short_video_status import (
    get_video_status,
    get_user_videos,
    get_recent_videos
)

v1_video_short_status_bp = Blueprint('v1_video_short_status', __name__)
logger = logging.getLogger(__name__)

@v1_video_short_status_bp.route('/v1/video/short/<video_id>/status', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def check_video_status(video_id, job_id, data):
    """Check the status of a short video."""
    try:
        status = get_video_status(video_id)
        if status:
            logger.info(f"Job {job_id}: Video {video_id} status retrieved")
            return status, f"/v1/video/short/{video_id}/status", 200
        else:
            logger.warning(f"Job {job_id}: Video {video_id} not found")
            return {"error": "Video not found"}, f"/v1/video/short/{video_id}/status", 404
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error checking video status: {str(e)}")
        return str(e), f"/v1/video/short/{video_id}/status", 500

@v1_video_short_status_bp.route('/v1/video/short/list', methods=['GET'])
@authenticate  
@queue_task_wrapper(bypass_queue=True)
def list_videos(job_id, data):
    """List all short videos for the user."""
    try:
        # Get user_id from authentication context (assuming it's available)
        user_id = getattr(data, 'user_id', 'unknown')  # This might need adjustment based on auth system
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        videos = get_user_videos(user_id, limit=limit, offset=offset)
        logger.info(f"Job {job_id}: Retrieved {len(videos)} videos for user {user_id}")
        return {"videos": videos, "limit": limit, "offset": offset}, "/v1/video/short/list", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error listing videos: {str(e)}")
        return str(e), "/v1/video/short/list", 500
