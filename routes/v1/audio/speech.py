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

from flask import Blueprint, request, jsonify
from utils.app_utils import validate_payload, queue_task_wrapper
import logging
from services.authentication import authenticate
from services.cloud_storage import upload_file
from services.v1.audio.speech import generate_tts, list_voices, list_voices_with_filter, check_tts_health, get_models
import os

v1_audio_speech_bp = Blueprint("v1_audio_speech", __name__)
logger = logging.getLogger(__name__)

@v1_audio_speech_bp.route("/v1/audio/speech", methods=["POST"])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "model": {"type": "string", "enum": ["tts-1", "tts-1-hd"], "default": "tts-1"},
        "input": {"type": "string"},  # OpenAI uses 'input' instead of 'text'
        "text": {"type": "string"},   # Keep 'text' for backward compatibility
        "voice": {"type": "string"},
        "rate": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "volume": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "pitch": {"type": "string", "pattern": "^[+-]?\\d+Hz?$|^\\d*\\.?\\d+$"},
        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},
        "response_format": {"type": "string", "enum": ["mp3", "opus", "aac", "flac", "wav", "pcm"], "default": "mp3"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "default": "mp3"},  # Keep for backward compatibility
        "subtitle_format": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"}
    },
    "required": [],  # Make text/input required in the function logic
    "additionalProperties": False
})
def text_to_speech(job_id, data):
    """Generate text-to-speech using the integrated edge-tts service"""
    # Handle both OpenAI 'input' and legacy 'text' parameters
    text = data.get("input") or data.get("text")
    if not text:
        return "Missing required parameter: 'input' or 'text'", "/v1/audio/speech", 400

    model = data.get("model", "tts-1")
    voice = data.get("voice", "en-US-AvaNeural")  # Default voice if none provided

    # Validate voice parameter
    if not voice:
        return "Missing required parameter: 'voice'", "/v1/audio/speech", 400

    # Handle both OpenAI 'response_format' and legacy 'output_format'
    output_format = data.get("response_format") or data.get("output_format", "mp3")
    subtitle_format = data.get("subtitle_format", "srt")

    rate = data.get("rate")
    volume = data.get("volume")
    pitch = data.get("pitch")
    speed = data.get("speed")

    logger.info(f"Job {job_id}: Received TTS request for text length {len(text)} using model {model} and voice {voice}")

    # Convert speed to rate if provided
    if speed and not rate:
        try:
            speed_float = float(speed)
            rate_percent = int((speed_float - 1.0) * 100)
            rate = f"{rate_percent:+d}%"
            logger.info(f"Job {job_id}: Converted speed {speed} to rate {rate}")
        except (ValueError, TypeError):
            logger.warning(f"Job {job_id}: Invalid speed value {speed}, ignoring")
            speed = None

    try:
        # Generate audio and subtitles using integrated edge-tts
        audio_file, subtitle_file = generate_tts(
            tts="edge-tts",  # Always use edge-tts
            text=text,
            voice=voice,
            job_id=job_id,
            output_format=output_format,
            rate=rate,
            volume=volume,
            pitch=pitch,
            subtitle_format=subtitle_format
        )

        # Upload files to cloud storage
        audio_url = upload_file(audio_file)
        subtitle_url = upload_file(subtitle_file)

        # Clean up local files
        os.remove(audio_file)
        os.remove(subtitle_file)

        return {
            'audio_url': audio_url,
            'subtitle_url': subtitle_url,
            'model': model,
            'voice': voice,
            'format': output_format
        }, "/v1/audio/speech", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error generating TTS - {str(e)}")
        return str(e), "/v1/audio/speech", 500

@v1_audio_speech_bp.route("/v1/audio/speech/voices", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_voices(job_id=None, data=None):
    """List available voices for text-to-speech with optional language filtering"""
    try:
        language = request.args.get('language')
        voices = list_voices_with_filter(language)
        return {'voices': voices}, "/v1/audio/speech/voices", 200
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return str(e), "/v1/audio/speech/voices", 500

@v1_audio_speech_bp.route("/v1/audio/speech/voices/all", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_all_voices(job_id=None, data=None):
    """List all available voices"""
    try:
        voices = list_voices()
        return {'voices': voices}, "/v1/audio/speech/voices/all", 200
    except Exception as e:
        logger.error(f"Error listing all voices: {str(e)}")
        return str(e), "/v1/audio/speech/voices/all", 500

@v1_audio_speech_bp.route("/v1/audio/speech/health", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def health_check(job_id=None, data=None):
    """Check TTS service health"""
    try:
        health_status = check_tts_health()
        status_code = 200 if health_status.get('available', False) else 503
        return health_status, "/v1/audio/speech/health", status_code
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'available': False
        }, "/v1/audio/speech/health", 500

@v1_audio_speech_bp.route("/v1/models", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_tts_models(job_id=None, data=None):
    """List available TTS models"""
    try:
        models = get_models()
        return {'data': models}, "/v1/models", 200
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return str(e), "/v1/models", 500


