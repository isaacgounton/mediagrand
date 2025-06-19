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
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.authentication import authenticate
from services.cloud_storage import upload_file
from services.v1.audio.speech import generate_tts, list_voices, list_voices_by_provider, list_engines, check_tts_health
import os

v1_audio_speech_bp = Blueprint("v1_audio_speech", __name__)
logger = logging.getLogger(__name__)

@v1_audio_speech_bp.route("/v1/audio/speech", methods=["POST"])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "tts": {"type": "string"},
        "provider": {"type": "string"},  # Accept both tts and provider
        "text": {"type": "string"},
        "voice": {"type": "string"},
        "rate": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "volume": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "pitch": {"type": "string", "pattern": "^[+-]?\\d+Hz?$|^\\d*\\.?\\d+$"},
        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "default": "mp3"},
        "subtitle_format": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"}
    },
    "required": ["text"],
    "additionalProperties": False
})
def text_to_speech(job_id, data):
    """Generate text-to-speech using the Awesome-TTS API"""
    text = data["text"]
    # Accept both 'tts' and 'provider' for backward compatibility
    provider = data.get("provider") or data.get("tts", "kokoro")  # Default to kokoro
    voice = data.get("voice")
    output_format = data.get("output_format", "mp3")
    subtitle_format = data.get("subtitle_format", "srt")
    rate = data.get("rate")
    volume = data.get("volume")
    pitch = data.get("pitch")
    speed = data.get("speed")

    logger.info(f"Job {job_id}: Received TTS request for text length {len(text)} using provider {provider}")

    # Convert speed to rate if provided
    if speed and not rate:
        rate_percent = int((speed - 1.0) * 100)
        rate = f"{rate_percent:+d}%"
        logger.info(f"Job {job_id}: Converted speed {speed} to rate {rate}")

    try:
        # Generate audio and subtitles using Awesome-TTS
        audio_file, subtitle_file = generate_tts(
            tts=provider,
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
            'engine': provider,
            'provider': provider,
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
    """List available voices for text-to-speech"""
    try:
        voices = list_voices()
        return {'voices': voices}, "/v1/audio/speech/voices", 200
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return str(e), "/v1/audio/speech/voices", 500

@v1_audio_speech_bp.route("/v1/audio/speech/voices/<provider>", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_voices_by_provider(provider, job_id=None, data=None):
    """List available voices for a specific TTS provider"""
    try:
        # Validate provider
        valid_providers = ["kokoro", "chatterbox", "openai-edge-tts"]
        if provider not in valid_providers:
            return f"Invalid provider '{provider}'. Valid providers: {', '.join(valid_providers)}", "/v1/audio/speech/voices", 400
        
        voices = list_voices_by_provider(provider)
        return {'voices': voices, 'provider': provider}, f"/v1/audio/speech/voices/{provider}", 200
    except Exception as e:
        logger.error(f"Error listing voices for provider {provider}: {str(e)}")
        return str(e), f"/v1/audio/speech/voices/{provider}", 500

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

@v1_audio_speech_bp.route("/v1/audio/speech/providers", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_providers(job_id=None, data=None):
    """List available TTS providers"""
    try:
        providers = list_engines()  # Keep using list_engines internally for now
        return {'providers': providers}, "/v1/audio/speech/providers", 200
    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        return str(e), "/v1/audio/speech/providers", 500
