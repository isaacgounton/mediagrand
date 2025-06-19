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
    """Make a request to the Awesome-TTS API"""
    url = TTS_SERVER_URL.rstrip("/") + "/" + endpoint.lstrip("/")
    try:
        logger.info(f"Making {method} request to: {url}")
        response = requests.request(method, url, timeout=10, **kwargs)
        logger.info(f"Response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Awesome-TTS API request failed for {url}: {str(e)}")
        raise

def check_tts_health() -> Dict:
    """Check the health status of the Awesome-TTS API"""
    try:
        # Try multiple possible health endpoints
        health_endpoints = ["status", "health", ""]
        
        for endpoint in health_endpoints:
            try:
                result = _make_request(endpoint)
                logger.info(f"Health check successful via /{endpoint}")
                return {
                    'status': 'healthy',
                    'available': True,
                    'endpoint': endpoint,
                    'server_url': TTS_SERVER_URL
                }
            except Exception as e:
                logger.warning(f"Health check failed for /{endpoint}: {str(e)}")
                continue
        
        # If all endpoints fail
        return {
            'status': 'error',
            'error': 'All health endpoints failed',
            'available': False,
            'server_url': TTS_SERVER_URL
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'available': False,
            'server_url': TTS_SERVER_URL
        }

def list_engines() -> List[Dict]:
    """List available TTS providers from Awesome-TTS"""
    try:
        # Try to get from API first
        try:
            result = _make_request("engines")
            if 'engines' in result:
                return result['engines']
        except Exception as e:
            logger.warning(f"Failed to get engines from API: {str(e)}")
        
        # Return the known providers - these should match what's available in the TTS service
        return [
            {"id": "kokoro", "name": "Kokoro ONNX", "description": "High-quality neural TTS"},
            {"id": "chatterbox", "name": "Chatterbox TTS", "description": "Voice cloning capabilities"},
            {"id": "openai-edge-tts", "name": "OpenAI Edge TTS", "description": "Microsoft Edge TTS backend"}
        ]
    except Exception as e:
        logger.error(f"Error listing engines: {str(e)}")
        return []

def list_voices() -> List[Dict]:
    """List available voices from all Awesome-TTS providers"""
    try:
        all_voices = []
        providers = ["kokoro", "chatterbox", "openai-edge-tts"]
        
        for provider in providers:
            try:
                logger.info(f"Fetching voices for provider: {provider}")
                response = _make_request(f"voices/{provider}")
                
                # Handle different possible response formats
                if 'voices' in response:
                    provider_voices = response['voices']
                elif isinstance(response, list):
                    provider_voices = response
                else:
                    logger.warning(f"Unexpected response format for {provider}: {response}")
                    provider_voices = []
                
                # Add provider info to each voice if not already present
                for voice in provider_voices:
                    if 'provider' not in voice:
                        voice['provider'] = provider
                    
                all_voices.extend(provider_voices)
                logger.info(f"Found {len(provider_voices)} voices for {provider}")
                
            except Exception as e:
                logger.warning(f"Failed to get voices for {provider}: {str(e)}")
                continue
        
        return all_voices
        
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return []

def list_voices_by_provider(provider: str) -> List[Dict]:
    """List available voices for a specific TTS provider"""
    try:
        logger.info(f"Fetching voices for provider: {provider}")
        response = _make_request(f"voices/{provider}")
        
        # Handle different possible response formats
        if 'voices' in response:
            voices = response['voices']
        elif isinstance(response, list):
            voices = response
        else:
            logger.warning(f"Unexpected response format for {provider}: {response}")
            voices = []
        
        # Add provider info to each voice if not already present
        for voice in voices:
            if 'provider' not in voice:
                voice['provider'] = provider
            
        logger.info(f"Found {len(voices)} voices for {provider}")
        return voices
        
    except Exception as e:
        logger.error(f"Error listing voices for provider {provider}: {str(e)}")
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
    Generate TTS using the Awesome-TTS API
    
    Args:
        tts: TTS provider to use (kokoro, chatterbox, openai-edge-tts)
        text: Text to convert to speech
        voice: Voice ID to use
        job_id: Unique job identifier
        output_format: Output audio format (wav/mp3)
        rate: Speech rate adjustment
        volume: Volume adjustment
        pitch: Pitch adjustment
        subtitle_format: Subtitle format (not used by Awesome-TTS)
        
    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    try:
        logger.info(f"Generating TTS for job {job_id} using {tts} provider with voice {voice}")
        
        # Convert rate to speed if provided (Awesome-TTS uses speed, not rate)
        speed = 1.0
        if rate:
            # Convert rate like "+50%" to speed like 1.5
            if rate.endswith('%'):
                rate_percent = int(rate.rstrip('%').replace('+', ''))
                speed = 1.0 + (rate_percent / 100.0)
            else:
                try:
                    speed = float(rate)
                except ValueError:
                    speed = 1.0
        
        # Prepare request payload for Awesome-TTS API
        payload = {
            "text": text,
            "provider": tts,
            "voice": voice,
            "speed": speed,
            "format": output_format.lower()
        }
        
        # Add pitch if provided (only supported by some providers)
        if pitch:
            try:
                # Convert pitch like "+50Hz" to numeric value
                pitch_value = float(pitch.rstrip('Hz').replace('+', ''))
                payload["pitch"] = pitch_value
            except ValueError:
                logger.warning(f"Invalid pitch value: {pitch}")
        
        logger.info(f"Sending request to Awesome-TTS: {payload}")
        
        # Generate TTS using Awesome-TTS API
        result = _make_request("tts", method="POST", json=payload)
        
        if not result.get('success', False):
            raise Exception(f"TTS generation failed: {result.get('error', 'Unknown error')}")
        
        # Get the audio URL from Awesome-TTS response
        audio_url = result.get('audio_url')
        if not audio_url:
            raise Exception("No audio URL returned from TTS service")
        
        # If it's a relative URL, make it absolute
        if audio_url.startswith('/'):
            audio_url = TTS_SERVER_URL.rstrip('/') + audio_url
        
        audio_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{output_format}")
        
        # Download audio file
        logger.info(f"Downloading audio from: {audio_url}")
        audio_response = requests.get(audio_url, timeout=30)
        audio_response.raise_for_status()
        with open(audio_path, 'wb') as f:
            f.write(audio_response.content)
        
        # Create a simple SRT subtitle file (Awesome-TTS doesn't generate subtitles)
        subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{subtitle_format}")
        duration = result.get('duration', 5000)  # Default 5 seconds if not provided
        duration_seconds = duration / 1000.0 if duration > 100 else duration  # Convert ms to seconds if needed
        
        # Generate simple subtitle
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            if subtitle_format == 'srt':
                f.write("1\n")
                f.write("00:00:00,000 --> ")
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                milliseconds = int((duration_seconds % 1) * 1000)
                f.write(f"{minutes:02d}:{seconds:02d},{milliseconds:03d}\n")
                f.write(f"{text}\n")
            else:  # vtt format
                f.write("WEBVTT\n\n")
                f.write("00:00:00.000 --> ")
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                milliseconds = int((duration_seconds % 1) * 1000)
                f.write(f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}\n")
                f.write(f"{text}\n")
        
        logger.info(f"Successfully generated TTS for job {job_id}")
        return audio_path, subtitle_path
        
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        raise
