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

import os
import json
import logging
import requests
from typing import Dict, List, Tuple, Optional
from config import LOCAL_STORAGE_PATH, TTS_SERVER_URL

logger = logging.getLogger(__name__)

def _make_request(endpoint: str, method: str = "GET", **kwargs) -> Dict:
    """Make a request to the TTS API"""
    url = TTS_SERVER_URL.rstrip("/") + "/" + endpoint.lstrip("/")
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"TTS API request failed: {str(e)}")
        raise

def check_tts_health() -> Dict:
    """Check the health status of the TTS API"""
    try:
        return _make_request("health")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'available': False
        }

def list_engines() -> List[Dict]:
    """List available TTS engines from the API"""
    try:
        response = _make_request("models")
        return response.get('data', [])
    except Exception as e:
        logger.error(f"Error listing engines: {str(e)}")
        return []

def list_voices() -> List[Dict]:
    """List available voices from the API"""
    try:
        response = _make_request("voices")
        return response.get('voices', [])
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return []

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
    Generate TTS using the remote API
    
    Args:
        tts: TTS engine to use
        text: Text to convert to speech
        voice: Voice ID to use
        job_id: Unique job identifier
        output_format: Output audio format
        rate: Speech rate adjustment
        volume: Volume adjustment
        pitch: Pitch adjustment
        subtitle_format: Subtitle format
        
    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    try:
        logger.info(f"Generating TTS for job {job_id}")
        
        # Prepare request payload
        payload = {
            "tts": tts,
            "text": text,
            "voice": voice,
            "output_format": output_format,
            "subtitle_format": subtitle_format
        }
        
        # Add optional parameters if provided
        if rate:
            payload["rate"] = rate
        if volume:
            payload["volume"] = volume
        if pitch:
            payload["pitch"] = pitch
            
        # Generate TTS
        result = _make_request("speech", method="POST", json=payload)
        
        # Download the generated files
        audio_url = result['audio_url']
        subtitle_url = result['subtitle_url']
        
        audio_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{output_format}")
        subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{subtitle_format}")
        
        # Download audio file
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()
        with open(audio_path, 'wb') as f:
            f.write(audio_response.content)
        
        # Download subtitle file
        subtitle_response = requests.get(subtitle_url)
        subtitle_response.raise_for_status()
        with open(subtitle_path, 'wb') as f:
            f.write(subtitle_response.content)
        
        logger.info(f"Successfully generated TTS for job {job_id}")
        return audio_path, subtitle_path
        
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise
