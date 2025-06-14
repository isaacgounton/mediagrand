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

import requests
import logging
import tempfile
import os
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

# AwesomeTTS API Configuration
AWESOME_TTS_BASE_URL = "https://tts.dahopevi.com/api"
AWESOME_TTS_TIMEOUT = 120  # 2 minutes timeout for TTS requests
AWESOME_TTS_VOICES_CACHE_TIMEOUT = 3600  # Cache voices for 1 hour

# Global cache for voices to avoid repeated API calls
_voices_cache = {
    'data': None,
    'timestamp': 0
}

class AwesomeTTSError(Exception):
    """Custom exception for AwesomeTTS API errors"""
    pass

def make_api_request(endpoint: str, method: str = 'GET', data: Dict = None, 
                    files: Dict = None, timeout: int = AWESOME_TTS_TIMEOUT) -> requests.Response:
    """
    Make a request to the AwesomeTTS API with proper error handling.
    
    Args:
        endpoint: API endpoint (relative to base URL)
        method: HTTP method ('GET', 'POST', etc.)
        data: Request data for POST requests
        files: Files for multipart requests
        timeout: Request timeout in seconds
        
    Returns:
        requests.Response object
        
    Raises:
        AwesomeTTSError: If the API request fails
    """
    url = f"{AWESOME_TTS_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        logger.debug(f"Making {method} request to {url}")
        
        if method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)
        else:
            response = requests.get(url, params=data, timeout=timeout)
        
        # Check for HTTP errors
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '60')
            logger.warning(f"Rate limited by AwesomeTTS API. Retry after {retry_after} seconds")
            raise AwesomeTTSError(f"Rate limited. Retry after {retry_after} seconds")
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get('error', f"HTTP {response.status_code}")
            except:
                error_message = f"HTTP {response.status_code}: {response.text[:200]}"
            
            logger.error(f"AwesomeTTS API error: {error_message}")
            raise AwesomeTTSError(f"API error: {error_message}")
        
        return response
        
    except requests.exceptions.Timeout:
        logger.error(f"AwesomeTTS API request timed out after {timeout} seconds")
        raise AwesomeTTSError(f"Request timed out after {timeout} seconds")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to AwesomeTTS API: {str(e)}")
        raise AwesomeTTSError(f"Connection error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to AwesomeTTS API: {str(e)}")
        raise AwesomeTTSError(f"Request error: {str(e)}")

def get_available_voices(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Get available voices from AwesomeTTS API with caching.
    
    Args:
        force_refresh: Force refresh of voice cache
        
    Returns:
        List of voice dictionaries
    """
    global _voices_cache
    
    # Check if cache is valid
    current_time = time.time()
    if (not force_refresh and 
        _voices_cache['data'] is not None and 
        (current_time - _voices_cache['timestamp']) < AWESOME_TTS_VOICES_CACHE_TIMEOUT):
        logger.debug("Using cached voices data")
        return _voices_cache['data']
    
    try:
        logger.info("Fetching voices from AwesomeTTS API")
        response = make_api_request('/voices', timeout=30)
        
        voices_data = response.json()
        
        # Handle different response formats
        if isinstance(voices_data, list):
            voices = voices_data
        elif isinstance(voices_data, dict):
            voices = voices_data.get('voices', voices_data.get('data', []))
        else:
            logger.warning(f"Unexpected voices response format: {type(voices_data)}")
            voices = []
        
        # Normalize voice format to ensure consistency
        normalized_voices = []
        for voice in voices:
            if isinstance(voice, dict):
                normalized_voice = {
                    'id': voice.get('id', voice.get('name', voice.get('voice_id', 'unknown'))),
                    'name': voice.get('name', voice.get('display_name', voice.get('id', 'Unknown'))),
                    'language': voice.get('language', voice.get('lang', voice.get('locale', 'en-US'))),
                    'gender': voice.get('gender', voice.get('voice_gender', 'neutral')),
                    'engine': voice.get('engine', voice.get('provider', 'awesome-tts')),
                    'description': voice.get('description', ''),
                    'sample_rate': voice.get('sample_rate', 22050),
                    'audio_format': voice.get('audio_format', 'mp3')
                }
                normalized_voices.append(normalized_voice)
            else:
                # Handle case where voice is just a string ID
                normalized_voices.append({
                    'id': str(voice),
                    'name': str(voice),
                    'language': 'en-US',
                    'gender': 'neutral',
                    'engine': 'awesome-tts',
                    'description': '',
                    'sample_rate': 22050,
                    'audio_format': 'mp3'
                })
        
        # Update cache
        _voices_cache['data'] = normalized_voices
        _voices_cache['timestamp'] = current_time
        
        logger.info(f"Successfully fetched {len(normalized_voices)} voices from AwesomeTTS API")
        return normalized_voices
        
    except AwesomeTTSError:
        # Re-raise AwesomeTTS errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching voices: {str(e)}")
        # Return cached data if available, otherwise empty list
        if _voices_cache['data'] is not None:
            logger.warning("Returning cached voices due to API error")
            return _voices_cache['data']
        
        # Return minimal fallback voices
        fallback_voices = [
            {
                'id': 'en-US-default',
                'name': 'English (US) Default',
                'language': 'en-US',
                'gender': 'neutral',
                'engine': 'awesome-tts',
                'description': 'Default English voice',
                'sample_rate': 22050,
                'audio_format': 'mp3'
            }
        ]
        logger.warning("Using fallback voices due to API unavailability")
        return fallback_voices

def get_available_engines() -> List[Dict[str, Any]]:
    """
    Get available TTS engines from AwesomeTTS API.
    
    Returns:
        List of engine dictionaries
    """
    try:
        logger.info("Fetching engines from AwesomeTTS API")
        response = make_api_request('/engines', timeout=15)
        
        engines_data = response.json()
        
        # Handle different response formats
        if isinstance(engines_data, list):
            engines = engines_data
        elif isinstance(engines_data, dict):
            engines = engines_data.get('engines', engines_data.get('data', []))
        else:
            logger.warning(f"Unexpected engines response format: {type(engines_data)}")
            engines = []
        
        logger.info(f"Successfully fetched {len(engines)} engines from AwesomeTTS API")
        return engines
        
    except Exception as e:
        logger.warning(f"Could not fetch engines from AwesomeTTS API: {str(e)}")
        # Return default engines based on typical AwesomeTTS setup
        return [
            {'id': 'edge-tts', 'name': 'Microsoft Edge TTS', 'description': 'Microsoft Edge Text-to-Speech'},
            {'id': 'openai-tts', 'name': 'OpenAI TTS', 'description': 'OpenAI Text-to-Speech'},
            {'id': 'elevenlabs', 'name': 'ElevenLabs', 'description': 'ElevenLabs AI Speech'}
        ]

def synthesize_speech(text: str, voice_id: str, engine: str = None, 
                     speed: float = 1.0, pitch: float = 0.0, volume: float = 1.0,
                     output_format: str = 'mp3', job_id: str = None) -> Tuple[str, Optional[str]]:
    """
    Synthesize speech using the AwesomeTTS API.
    
    Args:
        text: Text to synthesize
        voice_id: Voice ID to use
        engine: TTS engine to use (optional)
        speed: Speech speed (0.5 - 2.0)
        pitch: Pitch adjustment (-20.0 to 20.0)
        volume: Volume adjustment (0.0 - 2.0)
        output_format: Output audio format ('mp3', 'wav', 'ogg')
        job_id: Job ID for file naming
        
    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    if not job_id:
        job_id = f"tts_{int(time.time())}"
    
    logger.info(f"Synthesizing speech for job {job_id}: {len(text)} characters")
    
    # Prepare request data
    request_data = {
        'text': text,
        'voice': voice_id,
        'format': output_format.lower(),
        'speed': max(0.5, min(2.0, speed)),  # Clamp speed
        'pitch': max(-20.0, min(20.0, pitch)),  # Clamp pitch
        'volume': max(0.0, min(2.0, volume))  # Clamp volume
    }
    
    # Add engine if specified
    if engine:
        request_data['engine'] = engine
    
    try:
        # Make TTS request
        logger.debug(f"Sending TTS request: {request_data}")
        response = make_api_request('/synthesize', method='POST', data=request_data)
        
        # Check response content type
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            # API returned JSON (likely with URLs to audio files)
            response_data = response.json()
            
            # Check for audio URL in response
            audio_url = response_data.get('audio_url', response_data.get('url', response_data.get('file_url')))
            subtitle_url = response_data.get('subtitle_url', response_data.get('subtitles_url'))
            
            if audio_url:
                # Download audio file
                audio_path = download_file_from_url(audio_url, job_id, output_format)
                
                # Download subtitle file if available
                subtitle_path = None
                if subtitle_url:
                    subtitle_path = download_file_from_url(subtitle_url, job_id, 'srt')
                
                return audio_path, subtitle_path
            else:
                raise AwesomeTTSError("No audio URL in API response")
        
        elif 'audio/' in content_type or 'application/octet-stream' in content_type:
            # API returned audio data directly
            audio_filename = f"{job_id}.{output_format}"
            audio_path = os.path.join(LOCAL_STORAGE_PATH, audio_filename)
            
            # Save audio data
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved audio file: {audio_path} ({len(response.content)} bytes)")
            
            # Generate basic subtitle file
            subtitle_path = generate_basic_subtitle(text, job_id)
            
            return audio_path, subtitle_path
        
        else:
            raise AwesomeTTSError(f"Unexpected response content type: {content_type}")
    
    except AwesomeTTSError:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        raise AwesomeTTSError(f"Speech synthesis failed: {str(e)}")

def download_file_from_url(url: str, job_id: str, file_extension: str) -> str:
    """
    Download a file from a URL and save it locally.
    
    Args:
        url: URL to download from
        job_id: Job ID for file naming
        file_extension: File extension
        
    Returns:
        Local file path
    """
    try:
        logger.debug(f"Downloading file from {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        filename = f"{job_id}.{file_extension}"
        file_path = os.path.join(LOCAL_STORAGE_PATH, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded file: {file_path} ({len(response.content)} bytes)")
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {str(e)}")
        raise AwesomeTTSError(f"File download failed: {str(e)}")

def generate_basic_subtitle(text: str, job_id: str, format: str = 'srt') -> str:
    """
    Generate a basic subtitle file when timestamps are not available.
    
    Args:
        text: Original text
        job_id: Job ID for file naming
        format: Subtitle format ('srt' or 'vtt')
        
    Returns:
        Subtitle file path
    """
    import re
    
    subtitle_filename = f"{job_id}.{format}"
    subtitle_path = os.path.join(LOCAL_STORAGE_PATH, subtitle_filename)
    
    # Split text into reasonable chunks
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # Group sentences into subtitle chunks (max 2 sentences or 100 chars per chunk)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if (len(current_chunk) >= 2 or 
            current_length + len(sentence) > 100) and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    # If no sentences found, split by words
    if not chunks:
        words = text.split()
        chunk_size = max(5, len(words) // 10)  # 5-10 words per chunk
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
    
    # Generate subtitle file with estimated timing (3 seconds per chunk)
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        if format.lower() == 'vtt':
            f.write("WEBVTT\n\n")
            for i, chunk in enumerate(chunks, 1):
                start_time = (i - 1) * 3
                end_time = i * 3
                
                start_str = f"{start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d}.000"
                end_str = f"{end_time//3600:02d}:{(end_time%3600)//60:02d}:{end_time%60:02d}.000"
                
                f.write(f"{i}\n{start_str} --> {end_str}\n{chunk}\n\n")
        else:
            # SRT format
            for i, chunk in enumerate(chunks, 1):
                start_time = (i - 1) * 3
                end_time = i * 3
                
                start_str = f"{start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d},000"
                end_str = f"{end_time//3600:02d}:{(end_time%3600)//60:02d}:{end_time%60:02d},000"
                
                f.write(f"{i}\n{start_str} --> {end_str}\n{chunk}\n\n")
    
    logger.info(f"Generated basic subtitle file: {subtitle_path}")
    return subtitle_path

def health_check() -> bool:
    """
    Check if the AwesomeTTS API is healthy and responding.
    
    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = make_api_request('/health', timeout=10)
        return response.status_code == 200
    except:
        return False

def get_api_info() -> Dict[str, Any]:
    """
    Get information about the AwesomeTTS API.
    
    Returns:
        API information dictionary
    """
    try:
        response = make_api_request('/info', timeout=10)
        return response.json()
    except Exception as e:
        logger.warning(f"Could not get API info: {str(e)}")
        return {
            'api': 'AwesomeTTS',
            'version': 'unknown',
            'status': 'unknown',
            'base_url': AWESOME_TTS_BASE_URL
        }
