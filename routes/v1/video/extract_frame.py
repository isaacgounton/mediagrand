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
from utils.app_utils import validate_payload, queue_task_wrapper
import logging
import re
from services.v1.video.extract_frame import process_extract_frame
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_extract_frame_bp = Blueprint('v1_video_extract_frame', __name__)
logger = logging.getLogger(__name__)

def parse_time_to_seconds(time_input):
    """
    Parse various time formats to seconds.
    Supports:
    - Numbers: 6, 6.5
    - String numbers: "6", "6.5"
    - Time formats: "00:06", "0:06", "1:30", "01:30:45", "1:30:45.5"
    """
    if isinstance(time_input, (int, float)):
        return float(time_input)
    
    if isinstance(time_input, str):
        # Try to parse as a simple number first
        try:
            return float(time_input)
        except ValueError:
            pass
        
        # Parse time format (HH:MM:SS, MM:SS, or H:M:S variations)
        time_pattern = r'^(\d{1,2}):(\d{1,2})(?::(\d{1,2}(?:\.\d+)?))?$'
        match = re.match(time_pattern, time_input.strip())
        
        if match:
            hours_or_minutes = int(match.group(1))
            minutes_or_seconds = int(match.group(2))
            seconds_or_fraction = match.group(3)
            
            if seconds_or_fraction is not None:
                # Format: HH:MM:SS
                hours = hours_or_minutes
                minutes = minutes_or_seconds
                seconds = float(seconds_or_fraction)
                return hours * 3600 + minutes * 60 + seconds
            else:
                # Format: MM:SS
                minutes = hours_or_minutes
                seconds = minutes_or_seconds
                return minutes * 60 + seconds
        
        raise ValueError(f"Invalid time format: {time_input}")
    
    raise ValueError(f"Unsupported time input type: {type(time_input)}")

@v1_video_extract_frame_bp.route('/v1/video/extract-frame', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of the video to extract frame from"
        },
        "seconds": {
            "oneOf": [
                {"type": "number", "minimum": 0},
                {"type": "string"}
            ],
            "default": 0,
            "description": "Time in seconds to extract the frame from. Accepts numbers (6, 6.5) or time strings ('00:06', '1:30', '01:30:45')"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def extract_frame(job_id, data):
    video_url = data['video_url']
    seconds_input = data.get('seconds', 0)
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    # Parse the seconds input to handle various formats
    try:
        seconds = parse_time_to_seconds(seconds_input)
        if seconds < 0:
            raise ValueError("Seconds cannot be negative")
    except ValueError as e:
        logger.error(f"Job {job_id}: Invalid seconds parameter - {str(e)}")
        return f"Invalid seconds parameter: {str(e)}", "/v1/video/extract-frame", 400

    logger.info(f"Job {job_id}: Received extract frame request for video at {seconds} seconds (parsed from {seconds_input})")

    try:
        output_file = process_extract_frame(
            video_url=video_url,
            seconds=seconds,
            job_id=job_id
        )
        logger.info(f"Job {job_id}: Frame extraction process completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Extracted frame uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/video/extract-frame", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during frame extraction process - {str(e)}")
        return str(e), "/v1/video/extract-frame", 500

@v1_video_extract_frame_bp.route('/v1/video/extract-frame', methods=['OPTIONS'])
def extract_frame_options():
    """Return API documentation for extract frame endpoint"""
    return {
        "description": "Extracts an image frame from a video at a specified time",
        "methods": ["POST"],
        "parameters": {
            "video_url": {
                "type": "string",
                "required": True,
                "description": "URL of the video to extract frame from",
                "example": "https://example.com/video.mp4"
            },
            "seconds": {
                "type": "number",
                "required": False,
                "default": 0,
                "description": "Time in seconds to extract the frame from",
                "example": 30.5
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
                "description": "Returns cloud storage URL of extracted frame image"
            },
            "error": {
                "code": 500,
                "description": "Error message if extraction fails"
            }
        },
        "example_request": {
            "video_url": "https://example.com/video.mp4",
            "seconds": 30.5
        }
    }