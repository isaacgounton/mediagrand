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

from flask import Blueprint
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.video.merge_videos import process_video_merge
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_merge_bp = Blueprint('v1_video_merge', __name__)
logger = logging.getLogger(__name__)

@v1_video_merge_bp.route('/v1/video/merge', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_urls": {
            "type": "array",
            "items": {
                "type": "string",
                "format": "uri"
            },
            "minItems": 1,
            "description": "List of video URLs to merge"
        },
        "background_music_url": {
            "type": "string", 
            "format": "uri",
            "description": "Optional background music URL"
        },
        "background_music_volume": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "default": 0.5,
            "description": "Volume for background music (0.0 to 1.0)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_urls"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def merge_videos(job_id, data):
    video_urls = data['video_urls']
    background_music_url = data.get('background_music_url')
    background_music_volume = data.get('background_music_volume', 0.5)
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received video merge request for {len(video_urls)} videos")

    try:
        output_file = process_video_merge(
            video_urls=video_urls,
            background_music_url=background_music_url,
            background_music_volume=background_music_volume,
            job_id=job_id
        )
        logger.info(f"Job {job_id}: Video merge process completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Merged video uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/video/merge", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during video merge process - {str(e)}")
        return str(e), "/v1/video/merge", 500

@v1_video_merge_bp.route('/v1/video/merge', methods=['OPTIONS'])
def merge_videos_options():
    """Return API documentation for video merge endpoint"""
    return {
        "description": "Merges multiple videos together, optionally adding a background audio track",
        "methods": ["POST"],
        "parameters": {
            "video_urls": {
                "type": "array",
                "required": True,
                "description": "Array of video URLs to merge",
                "example": ["https://example.com/video1.mp4", "https://example.com/video2.mp4"]
            },
            "background_music_url": {
                "type": "string",
                "required": False,
                "description": "Optional background music URL",
                "example": "https://example.com/music.mp3"
            },
            "background_music_volume": {
                "type": "number",
                "required": False,
                "default": 0.5,
                "description": "Volume for background music (0.0 to 1.0)",
                "example": 0.3
            },
            "webhook_url": {
                "type": "string",
                "required": False,
                "description": "Optional webhook URL for job completion notification"
            }
        },
        "response": {
            "success": {
                "code": 200,
                "description": "Returns cloud storage URL of merged video"
            },
            "error": {
                "code": 500,
                "description": "Error message if merge fails"
            }
        },
        "example_request": {
            "video_urls": [
                "https://example.com/video1.mp4",
                "https://example.com/video2.mp4"
            ],
            "background_music_url": "https://example.com/music.mp3",
            "background_music_volume": 0.3
        }
    }