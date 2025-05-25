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

from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.authentication import authenticate
from services.cloud_storage import upload_file
from services.v1.video.short.short_video_create import create_short_video
from services.v1.video.short.short_video_status import (
    create_video_status,
    mark_video_completed,
    mark_video_failed
)

v1_video_short_create_bp = Blueprint('v1_video_short_create', __name__)
logger = logging.getLogger(__name__)

@v1_video_short_create_bp.route('/v1/video/short/create', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "search_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    },
                    "bg_video_url": {"type": "string", "format": "uri"},
                    "person_image_url": {"type": "string", "format": "uri"},
                    "person_name": {"type": "string"}
                },
                "required": ["text"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "config": {
            "type": "object",
            "properties": {
                "voice": {"type": "string"},
                "orientation": {"type": "string", "enum": ["portrait", "landscape"]},
                "caption_position": {"type": "string", "enum": ["top", "center", "bottom"]},
                "caption_background_color": {"type": "string"},
                "music": {"type": "string"},
                "music_url": {"type": "string", "format": "uri"},
                "music_volume": {"type": "string", "enum": ["low", "medium", "high", "muted"]},
                "padding_back": {"type": "number", "minimum": 0}
            },
            "additionalProperties": False
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["scenes"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def create_short_video_endpoint(job_id, data):
    """Create a short video from text scenes with background videos, music, and captions."""
    scenes = data['scenes']
    config = data.get('config', {})
    webhook_url = data.get('webhook_url')
    custom_id = data.get('id')
    
    # Use custom ID if provided, otherwise use generated job_id
    if custom_id:
        job_id = custom_id

    logger.info(f"Job {job_id}: Received short video creation request with {len(scenes)} scenes")

    # Create initial status entry
    user_id = getattr(data, 'user_id', 'unknown')  # This might need adjustment based on auth system
    create_video_status(job_id, user_id, len(scenes), config)

    try:
        # Process the short video creation
        output_filename = create_short_video(
            scenes=scenes,
            config=config,
            job_id=job_id
        )

        # Upload the resulting video to cloud storage
        cloud_url = upload_file(output_filename)

        logger.info(f"Job {job_id}: Short video uploaded to cloud storage: {cloud_url}")

        # Mark video as completed
        mark_video_completed(job_id, cloud_url)

        # Return the cloud URL for the uploaded video
        return cloud_url, "/v1/video/short/create", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating short video: {str(e)}", exc_info=True)
        
        # Mark video as failed
        mark_video_failed(job_id, str(e))
        
        return str(e), "/v1/video/short/create", 500
