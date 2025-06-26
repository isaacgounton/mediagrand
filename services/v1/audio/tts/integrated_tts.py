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
import logging
from typing import Dict, List, Tuple, Optional

from .tts_handler import generate_speech, get_voices, get_all_voices, VOICE_MAPPING
from .text_handler import prepare_tts_input_with_context
from .config import TTS_CONFIG

# Import LOCAL_STORAGE_PATH from the main config
try:
    from config import LOCAL_STORAGE_PATH
except ImportError:
    # Fallback if config is not available
    LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', '/tmp')

logger = logging.getLogger(__name__)

class IntegratedTTSService:
    """Integrated TTS service using edge-tts directly without external dependencies"""
    
    def __init__(self):
        self.default_voice = TTS_CONFIG["DEFAULT_VOICE"]
        self.default_format = TTS_CONFIG["DEFAULT_RESPONSE_FORMAT"]
        self.default_speed = TTS_CONFIG["DEFAULT_SPEED"]
        self.remove_filter = TTS_CONFIG["REMOVE_FILTER"]
    
    def check_health(self) -> Dict:
        """Check the health status of the integrated TTS service"""
        try:
            # Try to get voices to verify edge-tts is working
            voices = get_voices()
            if voices:
                return {
                    'status': 'healthy',
                    'available': True,
                    'service': 'integrated-edge-tts',
                    'voice_count': len(voices)
                }
            else:
                return {
                    'status': 'warning',
                    'available': True,
                    'service': 'integrated-edge-tts',
                    'message': 'No voices available'
                }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'available': False,
                'service': 'integrated-edge-tts'
            }
    
    def list_engines(self) -> List[Dict]:
        """List available TTS engines (just edge-tts in this case)"""
        return [
            {
                "id": "edge-tts", 
                "name": "Microsoft Edge TTS", 
                "description": "Microsoft Edge Text-to-Speech service"
            }
        ]
    
    def list_voices(self) -> List[Dict]:
        """List all available voices"""
        try:
            voices = get_all_voices()
            # Add provider info to each voice
            for voice in voices:
                voice['provider'] = 'edge-tts'
            return voices
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}")
            return []
    
    def list_voices_by_provider(self, provider: str) -> List[Dict]:
        """List voices by provider (only edge-tts supported)"""
        if provider != 'edge-tts':
            logger.warning(f"Unsupported provider: {provider}")
            return []
        return self.list_voices()
    
    def generate_tts(
        self,
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
            rate: Speech rate adjustment (converted to speed)
            volume: Volume adjustment (not supported by edge-tts)
            pitch: Pitch adjustment (not supported by edge-tts)
            subtitle_format: Subtitle format
            
        Returns:
            Tuple of (audio_file_path, subtitle_file_path)
        """
        try:
            logger.info(f"Generating TTS for job {job_id} using edge-tts with voice {voice}")
            
            # Prepare text if filtering is enabled
            if not self.remove_filter:
                text = prepare_tts_input_with_context(text)
            
            # Convert rate to speed if provided
            speed = self.default_speed
            if rate:
                speed = self._convert_rate_to_speed(rate)
            
            # Use default voice if none provided
            if not voice:
                voice = self.default_voice
            
            # Generate audio file path
            audio_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{output_format}")
            
            # Generate TTS audio
            generate_speech(text, voice, output_format, speed, audio_path)
            
            # Generate subtitle file
            subtitle_path = self._generate_subtitle_file(text, job_id, subtitle_format)
            
            logger.info(f"Successfully generated TTS for job {job_id}")
            return audio_path, subtitle_path
            
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}")
            raise
    
    def _convert_rate_to_speed(self, rate: str) -> float:
        """Convert rate string to speed float"""
        try:
            # Convert rate like "+50%" to speed like 1.5
            if rate.endswith('%'):
                rate_percent = int(rate.rstrip('%').replace('+', ''))
                speed = 1.0 + (rate_percent / 100.0)
            else:
                speed = float(rate)
            
            # Clamp speed to valid range
            speed = max(0.5, min(2.0, speed))
            return speed
        except (ValueError, TypeError):
            logger.warning(f"Invalid rate value: {rate}, using default speed")
            return self.default_speed
    
    def _generate_subtitle_file(self, text: str, job_id: str, subtitle_format: str) -> str:
        """Generate a simple subtitle file"""
        subtitle_path = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.{subtitle_format}")
        
        # Estimate duration (rough approximation: 150 words per minute)
        words = len(text.split())
        duration_seconds = max(1.0, words / 2.5)  # 150 words/min = 2.5 words/sec
        
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
        
        return subtitle_path

# Create a singleton instance
integrated_tts_service = IntegratedTTSService()
