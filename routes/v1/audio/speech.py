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

###########################################################################

# Author: Refactored for AwesomeTTS Backend Integration
# Date: June 2025
# Updated route: /v1/audio/speech - Now uses AwesomeTTS backend

from flask import Blueprint, request
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.authentication import authenticate
from services.cloud_storage import upload_file
from services.v1.audio.speech_awesome import generate_tts, list_voices, list_engines, check_tts_health
import os

v1_audio_speech_bp = Blueprint("v1_audio_speech", __name__)
logger = logging.getLogger(__name__)

@v1_audio_speech_bp.route("/v1/models", methods=["GET", "POST"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def list_models(job_id=None, data=None):
    """List available TTS models (OpenAI TTS API compatibility)"""
    try:
        # Get engines from AwesomeTTS and format as OpenAI-compatible models
        engines = list_engines()
        
        models = []
        for engine in engines:
            # Add standard OpenAI model names for compatibility
            models.append({
                "id": engine.get('id', 'tts-1'),
                "name": engine.get('name', 'Text-to-speech'),
                "description": engine.get('description', ''),
                "provider": "AwesomeTTS"
            })
        
        # Ensure we have at least the standard OpenAI models for compatibility
        if not any(model['id'] in ['tts-1', 'tts-1-hd'] for model in models):
            models.extend([
                {"id": "tts-1", "name": "Text-to-speech v1", "provider": "AwesomeTTS"},
                {"id": "tts-1-hd", "name": "Text-to-speech v1 HD", "provider": "AwesomeTTS"}
            ])
        
        logger.info(f"Successfully retrieved {len(models)} TTS models from AwesomeTTS")
        return {"data": models}, "/v1/models", 200
    except Exception as e:
        logger.error(f"Error listing TTS models: {str(e)}")
        return str(e), "/v1/models", 500

@v1_audio_speech_bp.route("/v1/voices", methods=["GET", "POST"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def list_voices_openai_compatible(job_id=None, data=None):
    """List voices with OpenAI API compatibility using AwesomeTTS backend"""
    try:
        # Get language parameter from query string or request body
        specific_language = None
        if request.method == 'GET':
            specific_language = request.args.get('language') or request.args.get('locale')
        else:  # POST
            data = request.get_json() or {}
            specific_language = data.get('language') or data.get('locale')
        
        voices = list_voices()
        
        # Filter by language if specified
        if specific_language and specific_language.lower() != 'all':
            filtered_voices = [
                voice for voice in voices 
                if voice.get('locale', '').lower().startswith(specific_language.lower()) or
                   voice.get('language', '').lower().startswith(specific_language.lower())
            ]
        else:
            filtered_voices = voices
        
        logger.info(f"Successfully retrieved {len(filtered_voices)} voices from AwesomeTTS (filtered from {len(voices)} total)")
        return {"voices": filtered_voices}, "/v1/voices", 200
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return str(e), "/v1/voices", 500

@v1_audio_speech_bp.route("/v1/audio/speech/voices", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def get_voices(job_id=None, data=None):
    """List available voices for text-to-speech with optional language filtering"""
    try:
        # Get query parameters for filtering
        language = request.args.get('language')
        locale = request.args.get('locale')
        engine = request.args.get('engine')
        
        # Use language or locale for filtering
        filter_language = language or locale
        
        voices = list_voices()
        
        # Apply filters if provided
        if filter_language:
            if filter_language.lower() == 'all':
                # Return all voices without filtering
                filtered_voices = voices
            else:
                # Filter by language/locale
                filtered_voices = [
                    voice for voice in voices 
                    if voice.get('locale', '').lower().startswith(filter_language.lower()) or
                       voice.get('language', '').lower().startswith(filter_language.lower())
                ]
        else:
            filtered_voices = voices
        
        # Apply engine filter if provided
        if engine:
            filtered_voices = [
                voice for voice in filtered_voices
                if voice.get('engine', '').lower() == engine.lower() or
                   voice.get('provider', '').lower() == engine.lower()
            ]
        
        logger.info(f"Successfully retrieved {len(filtered_voices)} TTS voices from AwesomeTTS (filtered from {len(voices)} total)")
        return {'voices': filtered_voices}, "/v1/audio/speech/voices", 200
    except Exception as e:
        logger.error(f"Error listing TTS voices: {str(e)}")
        return str(e), "/v1/audio/speech/voices", 500

@v1_audio_speech_bp.route("/v1/audio/speech/health", methods=["GET"])
@queue_task_wrapper(bypass_queue=True)
@authenticate
def tts_health_check(job_id=None, data=None):
    """Check the health of the AwesomeTTS backend"""
    try:
        health_status = check_tts_health()
        
        status_code = 200 if health_status.get('available', False) else 503
        
        logger.info(f"TTS health check: {health_status['status']}")
        return health_status, "/v1/audio/speech/health", status_code
    except Exception as e:
        logger.error(f"Error checking TTS health: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'available': False
        }, "/v1/audio/speech/health", 500

@v1_audio_speech_bp.route("/v1/audio/speech", methods=["POST"])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "tts": {"type": "string", "enum": ["kokoro", "chatterbox", "openai-edge-tts", "awesome-tts"]},
        "text": {"type": "string"},
        "voice": {"type": "string"},
        "engine": {"type": "string"},  # New: allow explicit engine selection
        "rate": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "volume": {"type": "string", "pattern": "^[+-]?\\d+%?$|^\\d*\\.?\\d+$"},
        "pitch": {"type": "string", "pattern": "^[+-]?\\d+Hz?$|^\\d*\\.?\\d+$"},
        "speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},  # New: direct speed control
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg"], "default": "mp3"},
        "subtitle_format": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"}
    },
    "required": ["text"],
    "additionalProperties": False
})
def text_to_speech(job_id, data):
    """Generate text-to-speech using AwesomeTTS backend"""
    tts = data.get("tts", "awesome-tts")  # Default to awesome-tts
    text = data["text"]
    voice = data.get("voice")
    engine = data.get("engine")  # Explicit engine selection
    output_format = data.get("output_format", "mp3")
    subtitle_format = data.get("subtitle_format", "srt")
    rate = data.get("rate")
    volume = data.get("volume")
    pitch = data.get("pitch")
    speed = data.get("speed")  # Direct speed control
    webhook_url = data.get("webhook_url")
    id = data.get("id")

    logger.info(f"Job {job_id}: Received AwesomeTTS request for text length {len(text)}")
    if rate or volume or pitch or speed:
        logger.info(f"Job {job_id}: Using adjustments - rate: {rate}, volume: {volume}, pitch: {pitch}, speed: {speed}")

    # Initialize variables to ensure they exist in finally block
    audio_file = None
    subtitle_file = None
    
    try:
        # Convert speed parameter to rate if provided
        if speed and not rate:
            # Convert speed number to rate percentage string
            rate_percent = int((speed - 1.0) * 100)
            rate = f"{rate_percent:+d}%"
            logger.info(f"Job {job_id}: Converted speed {speed} to rate {rate}")
        
        # If engine is explicitly specified, use it instead of deriving from tts
        effective_tts = engine if engine else tts
        
        audio_file, subtitle_file = generate_tts(
            tts=effective_tts,
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
        
        logger.info(f"Job {job_id}: Files uploaded to cloud storage using AwesomeTTS")
        return {
            'audio_url': audio_url,
            'subtitle_url': subtitle_url,
            'backend': 'AwesomeTTS',
            'voice_used': voice,
            'engine_used': effective_tts,
            'format': output_format
        }, "/v1/audio/speech", 200
    except Exception as e:
        logger.error(f"Job {job_id}: Error during AwesomeTTS process - {str(e)}")
        return str(e), "/v1/audio/speech", 500
    finally:
        try:
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
            if subtitle_file and os.path.exists(subtitle_file):
                os.remove(subtitle_file)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup failed: {cleanup_error}")

# Backward compatibility endpoint
@v1_audio_speech_bp.route("/v1/audio/speech/legacy", methods=["POST"])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "tts": {"type": "string", "enum": ["kokoro", "chatterbox", "openai-edge-tts"]},
        "text": {"type": "string"},
        "voice": {"type": "string"},
        "rate": {"type": "string", "pattern": "^[+-]\\d+%$"},
        "volume": {"type": "string", "pattern": "^[+-]\\d+%$"},
        "pitch": {"type": "string", "pattern": "^[+-]\\d+Hz$"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "output_format": {"type": "string", "enum": ["mp3", "wav"], "default": "mp3"}
    },
    "required": ["text"],
    "additionalProperties": False
})
def legacy_text_to_speech(job_id, data):
    """Legacy endpoint for backward compatibility - routes to AwesomeTTS"""
    logger.warning(f"Job {job_id}: Using legacy TTS endpoint, consider migrating to /v1/audio/speech")
    
    # Map legacy parameters to new format
    new_data = {
        'text': data['text'],
        'voice': data.get('voice'),
        'tts': data.get('tts', 'kokoro'),  # Default to kokoro for legacy
        'rate': data.get('rate'),
        'volume': data.get('volume'),
        'pitch': data.get('pitch'),
        'output_format': data.get('output_format', 'mp3'),
        'webhook_url': data.get('webhook_url'),
        'id': data.get('id')
    }
    
    # Call the main TTS function
    return text_to_speech(job_id, new_data)
