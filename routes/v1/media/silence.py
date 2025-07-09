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
from app_utils import *
import logging
from services.v1.media.silence import detect_silence, detect_silence_segments, analyze_audio_characteristics
from services.authentication import authenticate

v1_media_silence_bp = Blueprint('v1_media_silence', __name__)
logger = logging.getLogger(__name__)

@v1_media_silence_bp.route('/v1/media/silence', methods=['POST'])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "start": {"type": "string"},
        "end": {"type": "string"},
        "noise": {"type": "string"},
        "duration": {"type": "number", "minimum": 0.1},
        "mono": {"type": "boolean"},
        "volume_threshold": {"type": ["number", "string"], "minimum": 0, "maximum": 100},
        "use_advanced_vad": {"type": ["boolean", "string"]},
        "min_speech_duration": {"type": ["number", "string"], "minimum": 0.1},
        "speech_padding_ms": {"type": ["integer", "string"], "minimum": 0},
        "silence_padding_ms": {"type": ["integer", "string"], "minimum": 0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
def silence(job_id, data):
    """Enhanced silence/speech detection with VAD support."""
    media_url = data['media_url']
    
    # Enhanced parameters with type conversion
    try:
        volume_threshold = float(data.get('volume_threshold', 40.0))
        
        # Handle boolean conversion for use_advanced_vad
        use_advanced_vad_raw = data.get('use_advanced_vad', True)
        if isinstance(use_advanced_vad_raw, str):
            use_advanced_vad = use_advanced_vad_raw.lower() in ('true', '1', 'yes', 'on')
        else:
            use_advanced_vad = bool(use_advanced_vad_raw)
        
        min_speech_duration = float(data.get('min_speech_duration', 0.5))
        speech_padding_ms = int(float(data.get('speech_padding_ms', 50)))
        silence_padding_ms = int(float(data.get('silence_padding_ms', 450)))
    except (ValueError, TypeError) as e:
        logger.error(f"Job {job_id}: Parameter conversion error - {str(e)}")
        return f"Invalid parameter values: {str(e)}", "/v1/media/silence", 400
    
    # Legacy parameters (for backwards compatibility)
    start_time = data.get('start', None)
    end_time = data.get('end', None)
    noise_threshold = data.get('noise', '-30dB')
    min_duration = data.get('duration', min_speech_duration)
    mono = data.get('mono', True)
    
    logger.info(f"Job {job_id}: Enhanced silence detection for {media_url} (VAD: {use_advanced_vad})")
    
    try:
        if use_advanced_vad:
            # Use enhanced VAD method
            segments = detect_silence_segments(
                media_url=media_url,
                volume_threshold=volume_threshold,
                use_advanced_vad=True,
                min_speech_duration=min_speech_duration,
                speech_padding_ms=speech_padding_ms,
                silence_padding_ms=silence_padding_ms,
                job_id=job_id
            )
            result_type = "speech_segments"
        else:
            # Use legacy FFmpeg method
            segments = detect_silence(
                media_url=media_url,
                start_time=start_time,
                end_time=end_time,
                noise_threshold=noise_threshold,
                min_duration=min_duration,
                mono=mono,
                job_id=job_id
            )
            result_type = "silence_intervals"
        
        result = {
            "type": result_type,
            "method": "advanced_vad" if use_advanced_vad else "ffmpeg_silencedetect",
            "segments": segments,
            "total_segments": len(segments),
            "parameters": {
                "volume_threshold": volume_threshold,
                "min_duration": min_speech_duration if use_advanced_vad else min_duration,
                "speech_padding_ms": speech_padding_ms,
                "silence_padding_ms": silence_padding_ms
            }
        }
        
        logger.info(f"Job {job_id}: Detection completed - {len(segments)} {result_type} found")
        return result, "/v1/media/silence", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during detection process - {str(e)}")
        return str(e), "/v1/media/silence", 500


@v1_media_silence_bp.route('/v1/media/silence/analyze', methods=['POST'])
@queue_task_wrapper(bypass_queue=False)
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
def analyze_audio(job_id, data):
    """Analyze audio characteristics and recommend optimal processing parameters."""
    media_url = data['media_url']
    
    logger.info(f"Job {job_id}: Audio analysis request for {media_url}")
    
    try:
        analysis = analyze_audio_characteristics(
            media_url=media_url,
            job_id=job_id
        )
        
        logger.info(f"Job {job_id}: Audio analysis completed successfully")
        return analysis, "/v1/media/silence/analyze", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during audio analysis - {str(e)}")
        return str(e), "/v1/media/silence/analyze", 500