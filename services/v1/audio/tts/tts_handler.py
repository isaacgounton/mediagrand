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

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    edge_tts = None

import asyncio
import tempfile
import subprocess
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# OpenAI voice names mapped to edge-tts equivalents
VOICE_MAPPING = {
    'alloy': 'en-US-AvaNeural',
    'echo': 'en-US-AndrewNeural',
    'fable': 'en-GB-SoniaNeural',
    'onyx': 'en-US-EricNeural',
    'nova': 'en-US-SteffanNeural',
    'shimmer': 'en-US-EmmaNeural'
}

# Default configurations
DEFAULT_VOICE = 'en-US-AvaNeural'
DEFAULT_LANGUAGE = 'en-US'

def is_ffmpeg_installed():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def speed_to_rate(speed: float) -> str:
    """
    Converts a multiplicative speed value to the edge-tts "rate" format.
    
    Args:
        speed (float): The multiplicative speed value (e.g., 1.5 for +50%, 0.5 for -50%).
    
    Returns:
        str: The formatted "rate" string (e.g., "+50%" or "-50%").
    """
    if speed < 0 or speed > 2:
        raise ValueError("Speed must be between 0 and 2 (inclusive).")

    # Convert speed to percentage change
    percentage_change = (speed - 1) * 100

    # Format with a leading "+" or "-" as required
    return f"{percentage_change:+.0f}%"

async def _generate_audio(text: str, voice: str, response_format: str, speed: float, output_path: str):
    """Generate TTS audio and optionally convert to a different format."""
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("edge-tts package is not installed. Please install it with: pip install edge-tts")

    # Determine if the voice is an OpenAI-compatible voice or a direct edge-tts voice
    edge_tts_voice = VOICE_MAPPING.get(voice, voice)  # Use mapping if in OpenAI names, otherwise use as-is

    # Generate the TTS output in mp3 format first
    temp_mp3_file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_mp3_path = temp_mp3_file_obj.name

    # Convert speed to SSML rate format
    try:
        speed_rate = speed_to_rate(speed)  # Convert speed value to "+X%" or "-X%"
    except Exception as e:
        logger.warning(f"Error converting speed: {e}. Defaulting to +0%.")
        speed_rate = "+0%"

    # Generate the MP3 file
    communicator = edge_tts.Communicate(text=text, voice=edge_tts_voice, rate=speed_rate)
    await communicator.save(temp_mp3_path)
    temp_mp3_file_obj.close()  # Explicitly close our file object for the initial mp3

    # If the requested format is mp3, move the generated file to the output path
    if response_format == "mp3":
        os.rename(temp_mp3_path, output_path)
        return output_path

    # Check if FFmpeg is installed
    if not is_ffmpeg_installed():
        logger.warning("FFmpeg is not available. Returning unmodified mp3 file.")
        os.rename(temp_mp3_path, output_path)
        return output_path

    # Build the FFmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-i", temp_mp3_path,  # Input file path
        "-c:a", {
            "aac": "aac",
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "opus": "libopus",
            "flac": "flac"
        }.get(response_format, "aac"),  # Default to AAC if unknown
    ]

    if response_format != "wav":
        ffmpeg_command.extend(["-b:a", "192k"])

    ffmpeg_command.extend([
        "-f", {
            "aac": "mp4",  # AAC in MP4 container
            "mp3": "mp3",
            "wav": "wav",
            "opus": "ogg",
            "flac": "flac"
        }.get(response_format, response_format),  # Default to matching format
        "-y",  # Overwrite without prompt
        output_path  # Output file path
    ])

    try:
        # Run FFmpeg command and ensure no errors occur
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        # Clean up potentially created (but incomplete) converted file
        Path(output_path).unlink(missing_ok=True)
        # Clean up the original mp3 file as well, since conversion failed
        Path(temp_mp3_path).unlink(missing_ok=True)
        
        error_message = f"FFmpeg error during audio conversion. Command: '{' '.join(e.cmd)}'. Stderr: {e.stderr.decode('utf-8', 'ignore')}"
        logger.error(error_message)
        raise RuntimeError(f"FFmpeg error during audio conversion: {e}")

    # Clean up the original temporary file (original mp3) as it's now converted
    Path(temp_mp3_path).unlink(missing_ok=True)

    return output_path

def generate_speech(text: str, voice: str, response_format: str, speed: float, output_path: str) -> str:
    """
    Generate speech using edge-tts.
    
    Args:
        text: Text to convert to speech
        voice: Voice ID to use
        response_format: Output audio format (mp3, wav, etc.)
        speed: Speech speed multiplier (0.5 to 2.0)
        output_path: Path where the audio file should be saved
        
    Returns:
        str: Path to the generated audio file
    """
    return asyncio.run(_generate_audio(text, voice, response_format, speed, output_path))

async def _get_voices(language: Optional[str] = None) -> List[Dict]:
    """List all voices, filter by language if specified"""
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("edge-tts package is not installed. Please install it with: pip install edge-tts")

    all_voices = await edge_tts.list_voices()
    language = language or DEFAULT_LANGUAGE  # Use default if no language specified
    filtered_voices = [
        {"name": v['ShortName'], "gender": v['Gender'], "language": v['Locale'], "id": v['ShortName']}
        for v in all_voices if language == 'all' or language is None or v['Locale'] == language
    ]
    return filtered_voices

def get_voices(language: Optional[str] = None) -> List[Dict]:
    """Get available voices for TTS"""
    return asyncio.run(_get_voices(language))

def get_all_voices() -> List[Dict]:
    """Get all available voices"""
    return get_voices('all')
