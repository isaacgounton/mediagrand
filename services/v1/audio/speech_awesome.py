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
import os
from typing import List, Dict, Any, Tuple, Optional
from services.awesome_tts import (
    get_available_voices,
    get_available_engines,
    synthesize_speech,
    health_check,
    get_api_info,
    AwesomeTTSError
)

logger = logging.getLogger(__name__)

def list_voices() -> List[Dict[str, Any]]:
    """
    List all available voices from the AwesomeTTS backend.
    
    Returns:
        List of voice dictionaries with standardized format
    """
    try:
        logger.info("Fetching voices from AwesomeTTS backend")
        voices = get_available_voices()
        
        # Convert to the format expected by the existing API
        standardized_voices = []
        for voice in voices:
            standardized_voice = {
                'name': voice.get('id', voice.get('name', 'unknown')),
                'display_name': voice.get('name', voice.get('display_name', voice.get('id', 'Unknown'))),
                'gender': voice.get('gender', 'neutral'),
                'locale': voice.get('language', voice.get('locale', 'en-US')),
                'language': voice.get('language', voice.get('locale', 'en-US')),
                'engine': 'awesome-tts',
                'provider': voice.get('engine', 'awesome-tts'),
                'description': voice.get('description', ''),
                'sample_rate': voice.get('sample_rate', 22050),
                'audio_format': voice.get('audio_format', 'mp3')
            }
            standardized_voices.append(standardized_voice)
        
        logger.info(f"Successfully retrieved {len(standardized_voices)} voices from AwesomeTTS")
        return standardized_voices
        
    except Exception as e:
        logger.error(f"Error listing voices from AwesomeTTS: {str(e)}")
        # Return minimal fallback
        return [
            {
                'name': 'en-US-default',
                'display_name': 'English (US) Default',
                'gender': 'neutral',
                'locale': 'en-US',
                'language': 'en-US',
                'engine': 'awesome-tts',
                'provider': 'awesome-tts',
                'description': 'Default English voice',
                'sample_rate': 22050,
                'audio_format': 'mp3'
            }
        ]

def list_engines() -> List[Dict[str, Any]]:
    """
    List all available TTS engines from the AwesomeTTS backend.
    
    Returns:
        List of engine dictionaries
    """
    try:
        logger.info("Fetching engines from AwesomeTTS backend")
        return get_available_engines()
    except Exception as e:
        logger.error(f"Error listing engines from AwesomeTTS: {str(e)}")
        # Return fallback engines
        return [
            {'id': 'edge-tts', 'name': 'Microsoft Edge TTS', 'description': 'Microsoft Edge Text-to-Speech'},
            {'id': 'openai-tts', 'name': 'OpenAI TTS', 'description': 'OpenAI Text-to-Speech'},
            {'id': 'elevenlabs', 'name': 'ElevenLabs', 'description': 'ElevenLabs AI Speech'}
        ]

def generate_tts(tts: str, text: str, voice: str, job_id: str,
                 output_format: str = "mp3",
                 rate: str = None, volume: str = None, pitch: str = None,
                 subtitle_format: str = "srt") -> Tuple[str, str]:
    """
    Generate TTS audio using the AwesomeTTS backend.
    
    This function maintains compatibility with the existing speech.py interface
    while using the new AwesomeTTS backend.
    
    Args:
        tts: TTS engine identifier (maintained for compatibility, but AwesomeTTS handles engine selection)
        text: Text to convert to speech
        voice: Voice ID to use
        job_id: Unique job identifier
        output_format: Output audio format ('mp3' or 'wav')
        rate: Speech rate adjustment (e.g., "+10%", "1.2")
        volume: Volume adjustment (e.g., "+10%", "1.1")
        pitch: Pitch adjustment (e.g., "+5Hz", "1.0")
        subtitle_format: Subtitle format ('srt' or 'vtt')
        
    Returns:
        Tuple of (audio_file_path, subtitle_file_path)
    """
    logger.info(f"Generating TTS using AwesomeTTS for job {job_id}: {len(text)} characters")
    
    try:
        # Parse rate parameter
        speed = 1.0
        if rate:
            try:
                if rate.endswith('%'):
                    rate_percent = int(rate.replace('%', '').replace('+', ''))
                    speed = 1.0 + (rate_percent / 100.0)
                else:
                    speed = float(rate)
            except (ValueError, TypeError):
                logger.warning(f"Invalid rate format '{rate}', using default speed 1.0")
        
        # Parse volume parameter
        volume_multiplier = 1.0
        if volume:
            try:
                if volume.endswith('%'):
                    volume_percent = int(volume.replace('%', '').replace('+', ''))
                    volume_multiplier = 1.0 + (volume_percent / 100.0)
                else:
                    volume_multiplier = float(volume)
            except (ValueError, TypeError):
                logger.warning(f"Invalid volume format '{volume}', using default volume 1.0")
        
        # Parse pitch parameter
        pitch_adjustment = 0.0
        if pitch:
            try:
                if pitch.endswith('Hz'):
                    pitch_adjustment = float(pitch.replace('Hz', ''))
                else:
                    pitch_adjustment = float(pitch)
            except (ValueError, TypeError):
                logger.warning(f"Invalid pitch format '{pitch}', using default pitch 0.0")
        
        # Set default voice if none provided
        if not voice:
            # Try to get a default voice from available voices
            try:
                voices = list_voices()
                if voices:
                    voice = voices[0]['name']
                    logger.info(f"Using default voice: {voice}")
                else:
                    voice = 'en-US-default'
                    logger.warning(f"No voices available, using fallback: {voice}")
            except:
                voice = 'en-US-default'
                logger.warning(f"Error getting voices, using fallback: {voice}")
        
        # Map old TTS engine names to potential engine preferences
        engine_preference = None
        if tts:
            engine_mapping = {
                'edge-tts': 'edge-tts',
                'openai-edge-tts': 'openai-tts', 
                'streamlabs-polly': 'edge-tts',  # Fallback to edge-tts
                'kokoro': 'edge-tts'  # Fallback to edge-tts
            }
            engine_preference = engine_mapping.get(tts.lower())
            if engine_preference:
                logger.info(f"Mapped TTS engine '{tts}' to '{engine_preference}'")
        
        # Call AwesomeTTS synthesis
        audio_path, subtitle_path = synthesize_speech(
            text=text,
            voice_id=voice,
            engine=engine_preference,
            speed=speed,
            pitch=pitch_adjustment,
            volume=volume_multiplier,
            output_format=output_format.lower(),
            job_id=job_id
        )
        
        # If subtitle_path is None, generate a basic one
        if not subtitle_path:
            from services.awesome_tts import generate_basic_subtitle
            subtitle_path = generate_basic_subtitle(text, job_id, subtitle_format)
        
        # Verify files exist
        if not os.path.exists(audio_path):
            raise AwesomeTTSError(f"Audio file was not created: {audio_path}")
        
        if not os.path.exists(subtitle_path):
            logger.warning(f"Subtitle file not found: {subtitle_path}")
            # Generate a basic subtitle as fallback
            from services.awesome_tts import generate_basic_subtitle
            subtitle_path = generate_basic_subtitle(text, job_id, subtitle_format)
        
        logger.info(f"Successfully generated TTS for job {job_id}")
        logger.info(f"Audio file: {audio_path} ({os.path.getsize(audio_path)} bytes)")
        logger.info(f"Subtitle file: {subtitle_path} ({os.path.getsize(subtitle_path)} bytes)")
        
        return audio_path, subtitle_path
        
    except AwesomeTTSError as e:
        logger.error(f"AwesomeTTS error for job {job_id}: {str(e)}")
        raise Exception(f"TTS generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error generating TTS for job {job_id}: {str(e)}")
        raise Exception(f"TTS generation failed: {str(e)}")

def check_tts_health() -> Dict[str, Any]:
    """
    Check the health of the AwesomeTTS backend.
    
    Returns:
        Health status dictionary
    """
    try:
        is_healthy = health_check()
        api_info = get_api_info()
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'backend': 'AwesomeTTS',
            'api_info': api_info,
            'available': is_healthy
        }
    except Exception as e:
        logger.error(f"Error checking TTS health: {str(e)}")
        return {
            'status': 'error',
            'backend': 'AwesomeTTS',
            'error': str(e),
            'available': False
        }

# Backward compatibility functions
def handle_edge_tts(*args, **kwargs):
    """Backward compatibility wrapper for edge-tts"""
    logger.warning("handle_edge_tts is deprecated, use generate_tts with tts='edge-tts'")
    return generate_tts(tts='edge-tts', *args, **kwargs)

def handle_streamlabs_polly_tts(*args, **kwargs):
    """Backward compatibility wrapper for streamlabs-polly"""
    logger.warning("handle_streamlabs_polly_tts is deprecated, use generate_tts with tts='streamlabs-polly'")
    return generate_tts(tts='streamlabs-polly', *args, **kwargs)

def handle_kokoro_tts(*args, **kwargs):
    """Backward compatibility wrapper for kokoro"""
    logger.warning("handle_kokoro_tts is deprecated, use generate_tts with tts='kokoro'")
    return generate_tts(tts='kokoro', *args, **kwargs)

def handle_openai_edge_tts(*args, **kwargs):
    """Backward compatibility wrapper for openai-edge-tts"""
    logger.warning("handle_openai_edge_tts is deprecated, use generate_tts with tts='openai-edge-tts'")
    return generate_tts(tts='openai-edge-tts', *args, **kwargs)
