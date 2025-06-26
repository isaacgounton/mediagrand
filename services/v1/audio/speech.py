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

import logging
from typing import Dict, List, Tuple, Optional

from .tts.integrated_tts import integrated_tts_service

logger = logging.getLogger(__name__)

def check_tts_health() -> Dict:
    """Check the health status of the integrated TTS service"""
    return integrated_tts_service.check_health()

def get_models() -> List[Dict]:
    """Get available TTS models"""
    return [
        {"id": "tts-1", "name": "Text-to-speech v1", "description": "Standard quality text-to-speech"},
        {"id": "tts-1-hd", "name": "Text-to-speech v1 HD", "description": "High definition text-to-speech"}
    ]



def list_voices() -> List[Dict]:
    """List available voices from the integrated TTS service"""
    return integrated_tts_service.list_voices()

def list_voices_with_filter(language: Optional[str] = None) -> List[Dict]:
    """List available voices with optional language filtering"""
    from .tts.tts_handler import get_voices
    if language:
        return get_voices(language)
    else:
        return get_voices('all')

def generate_tts(
    tts: str,
    text: str,
    voice: str,
    job_id: str,
    output_format: str = "mp3",
    rate: Optional[str] = None,
    volume: Optional[str] = None,
    pitch: Optional[str] = None,
    subtitle_format: str = "srt"
) -> Tuple[str, str]:
    """
    Generate TTS using the integrated edge-tts service

    Args:
        tts: TTS provider (ignored, always uses edge-tts)
        text: Text to convert to speech
        voice: Voice ID to use
        job_id: Unique job identifier
        output_format: Output audio format (wav/mp3)
        rate: Speech rate adjustment
        volume: Volume adjustment (not supported)
        pitch: Pitch adjustment (not supported)
        subtitle_format: Subtitle format

    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    return integrated_tts_service.generate_tts(
        tts=tts,
        text=text,
        voice=voice,
        job_id=job_id,
        output_format=output_format,
        rate=rate,
        volume=volume,
        pitch=pitch,
        subtitle_format=subtitle_format
    )
