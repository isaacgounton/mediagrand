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
from services.v1.video.tts_captioned_video import process_tts_captioned_video
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_tts_captioned_bp = Blueprint('v1_video_tts_captioned', __name__)
logger = logging.getLogger(__name__)

@v1_video_tts_captioned_bp.route('/v1/video/tts-captioned', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "background_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of the background image"
        },
        "text": {
            "type": "string",
            "description": "Text to generate speech from (required if audio_url not provided)"
        },
        "audio_url": {
            "type": "string",
            "format": "uri",
            "description": "URL of existing audio file (required if text not provided)"
        },
        "width": {
            "type": "integer",
            "minimum": 1,
            "default": 1080,
            "description": "Width of the video (default: 1080)"
        },
        "height": {
            "type": "integer",
            "minimum": 1,
            "default": 1920,
            "description": "Height of the video (default: 1920)"
        },
        "speech_voice": {
            "type": "string",
            "default": "en-US-AriaNeural",
            "description": "Voice for text-to-speech (default: en-US-AriaNeural)"
        },
        "speech_speed": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 3.0,
            "default": 1.0,
            "description": "Speed of speech (default: 1.0)"
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["background_url"],
    "additionalProperties": False,
    "anyOf": [
        {"required": ["text"]},
        {"required": ["audio_url"]}
    ]
})
@queue_task_wrapper(bypass_queue=False)
def generate_tts_captioned_video(job_id, data):
    background_url = data['background_url']
    text = data.get('text')
    audio_url = data.get('audio_url')
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    speech_voice = data.get('speech_voice', 'en-US-AriaNeural')
    speech_speed = data.get('speech_speed', 1.0)
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received TTS captioned video request")

    try:
        output_file = process_tts_captioned_video(
            background_url=background_url,
            text=text,
            audio_url=audio_url,
            width=width,
            height=height,
            speech_voice=speech_voice,
            speech_speed=speech_speed,
            job_id=job_id
        )
        logger.info(f"Job {job_id}: TTS captioned video generation completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: TTS captioned video uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/video/tts-captioned", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during TTS captioned video generation - {str(e)}")
        return str(e), "/v1/video/tts-captioned", 500

@v1_video_tts_captioned_bp.route('/v1/video/tts-captioned', methods=['OPTIONS'])
def generate_tts_captioned_video_options():
    """Return API documentation for TTS captioned video endpoint"""
    return {
        "description": "Creates a captioned text-to-speech video from background image and text or audio",
        "methods": ["POST"],
        "parameters": {
            "background_url": {
                "type": "string",
                "required": True,
                "description": "URL of the background image",
                "example": "https://example.com/background.jpg"
            },
            "text": {
                "type": "string",
                "required": "conditional",
                "description": "Text to generate speech from (required if audio_url not provided)",
                "example": "Hello, this is a sample text for speech generation."
            },
            "audio_url": {
                "type": "string",
                "required": "conditional",
                "description": "URL of existing audio file (required if text not provided)",
                "example": "https://example.com/audio.mp3"
            },
            "width": {
                "type": "integer",
                "required": False,
                "default": 1080,
                "description": "Width of the video",
                "example": 1080
            },
            "height": {
                "type": "integer",
                "required": False,
                "default": 1920,
                "description": "Height of the video",
                "example": 1920
            },
            "speech_voice": {
                "type": "string",
                "required": False,
                "default": "en-US-AriaNeural",
                "description": "Voice for text-to-speech",
                "example": "en-US-AriaNeural"
            },
            "speech_speed": {
                "type": "number",
                "required": False,
                "default": 1.0,
                "description": "Speed of speech (0.1 to 3.0)",
                "example": 1.2
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
                "description": "Returns cloud storage URL of generated captioned video"
            },
            "error": {
                "code": 500,
                "description": "Error message if generation fails"
            }
        },
        "example_request": {
            "background_url": "https://example.com/background.jpg",
            "text": "Hello, this is a sample text for speech generation.",
            "width": 1080,
            "height": 1920,
            "speech_voice": "en-US-AriaNeural",
            "speech_speed": 1.0
        }
    }