import os
import subprocess
import logging
import tempfile
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LongFormAudioMixer:
    """
    Audio mixing service specialized for long-form content
    Provides different mixing strategies optimized for educational/commentary videos
    """
    
    def __init__(self):
        pass
    
    def mix_long_form_audio(self, 
                          video_path: str, 
                          commentary_audio_path: str, 
                          output_path: str,
                          mixing_strategy: str = "commentary_focused",
                          fade_transitions: bool = True) -> str:
        """
        Mix commentary audio with original video audio for long-form content
        
        Args:
            video_path: Path to input video file
            commentary_audio_path: Path to commentary audio file 
            output_path: Path for output video file
            mixing_strategy: Audio mixing approach ("commentary_focused", "balanced", "background_only")
            fade_transitions: Whether to add fade transitions between sections
            
        Returns:
            Path to output video file
        """
        try:
            logger.info(f"Long-form audio mixing: strategy={mixing_strategy}, fades={fade_transitions}")
            
            # Get mixing levels based on strategy
            original_volume, commentary_volume = self._get_mixing_levels(mixing_strategy)
            
            # Build FFmpeg command based on strategy
            if mixing_strategy == "background_only":
                # No original audio, just commentary
                ffmpeg_command = [
                    "ffmpeg",
                    "-i", video_path,  # Input video
                    "-i", commentary_audio_path,  # Input commentary audio
                    "-map", "0:v",  # Map video from first input
                    "-map", "1:a",  # Map audio from second input (commentary only)
                    "-c:v", "copy",  # Copy video codec
                    "-c:a", "aac",  # Encode audio as AAC
                    "-y",  # Overwrite output file
                    output_path
                ]
            else:
                # Mix original and commentary audio
                filter_complex = f"[0:a]volume={original_volume}[a0];[1:a]volume={commentary_volume}[a1];[a0][a1]amix=inputs=2:duration=longest[a]"
                
                if fade_transitions:
                    # Add fade in/out for smoother transitions (first 2 seconds, last 2 seconds)
                    filter_complex = f"[0:a]volume={original_volume}[a0];[1:a]volume={commentary_volume},afade=t=in:st=0:d=2,afade=t=out:st=-2:d=2[a1];[a0][a1]amix=inputs=2:duration=longest[a]"
                
                ffmpeg_command = [
                    "ffmpeg",
                    "-i", video_path,  # Input video
                    "-i", commentary_audio_path,  # Input commentary audio
                    "-filter_complex", filter_complex,
                    "-map", "0:v",  # Map video from first input
                    "-map", "[a]",  # Map mixed audio
                    "-c:v", "copy",  # Copy video codec
                    "-c:a", "aac",  # Encode audio as AAC
                    "-y",  # Overwrite output file
                    output_path
                ]
            
            logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_command)}")
            
            # Run FFmpeg command
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Long-form audio mixing completed successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg long-form audio mixing failed: {e.stderr}")
            raise Exception(f"Long-form audio mixing failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Long-form audio mixing error: {e}")
            raise Exception(f"Long-form audio mixing error: {e}")
    
    def _get_mixing_levels(self, mixing_strategy: str) -> tuple:
        """Get audio mixing levels based on strategy"""
        strategies = {
            "commentary_focused": (0.2, 1.2),    # Original: 20%, Commentary: 120%
            "balanced": (0.5, 1.0),              # Original: 50%, Commentary: 100%
            "original_focused": (0.8, 0.6),      # Original: 80%, Commentary: 60%
            "background_only": (0.0, 1.0),       # No original, commentary only
        }
        
        return strategies.get(mixing_strategy, strategies["commentary_focused"])
    
    def create_sectioned_audio(self, 
                             video_path: str, 
                             script_data: Dict[str, Any],
                             commentary_audio_path: str,
                             output_path: str,
                             mixing_strategy: str = "commentary_focused") -> str:
        """
        Create audio with different mixing for introduction, main sections, and conclusion
        This allows for dynamic audio treatment throughout the long-form video
        """
        try:
            logger.info("Creating sectioned audio for long-form content")
            
            # Calculate section timings based on script data
            sections = self._calculate_section_timings(script_data)
            
            # Build complex FFmpeg filter for sectioned audio
            filter_parts = []
            audio_maps = []
            
            original_volume, commentary_volume = self._get_mixing_levels(mixing_strategy)
            
            # Create time-based volume adjustments for original audio
            volume_filters = []
            for i, section in enumerate(sections):
                start_time = section['start_time']
                end_time = section['end_time']
                section_volume = section.get('original_volume', original_volume)
                
                volume_filters.append(f"volume={section_volume}:enable='between(t,{start_time},{end_time})'")
            
            # Combine volume filters
            original_filter = f"[0:a]{','.join(volume_filters)}[original_adjusted]"
            commentary_filter = f"[1:a]volume={commentary_volume}[commentary_adjusted]"
            mix_filter = "[original_adjusted][commentary_adjusted]amix=inputs=2:duration=longest[mixed_audio]"
            
            filter_complex = f"{original_filter};{commentary_filter};{mix_filter}"
            
            ffmpeg_command = [
                "ffmpeg",
                "-i", video_path,
                "-i", commentary_audio_path,
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[mixed_audio]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-y",
                output_path
            ]
            
            logger.info(f"Running sectioned audio FFmpeg: {' '.join(ffmpeg_command[:10])}...")
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Sectioned audio creation completed successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg sectioned audio failed: {e.stderr}")
            raise Exception(f"Sectioned audio creation failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Sectioned audio creation error: {e}")
            raise Exception(f"Sectioned audio creation error: {e}")
    
    def _calculate_section_timings(self, script_data: Dict[str, Any]) -> list:
        """Calculate timing for each section based on script data"""
        sections = []
        current_time = 0
        
        # Introduction section
        intro_duration = script_data.get('introduction_duration', 30)  # Default 30 seconds
        sections.append({
            'name': 'introduction',
            'start_time': current_time,
            'end_time': current_time + intro_duration,
            'original_volume': 0.3  # Lower original volume for intro
        })
        current_time += intro_duration
        
        # Main sections
        for i, section in enumerate(script_data.get('main_sections', [])):
            section_duration = section.get('duration_estimate', 120)  # Default 2 minutes per section
            sections.append({
                'name': f'main_section_{i+1}',
                'start_time': current_time,
                'end_time': current_time + section_duration,
                'original_volume': 0.2  # Even lower for main content sections
            })
            current_time += section_duration
        
        # Conclusion section
        conclusion_duration = script_data.get('conclusion_duration', 30)  # Default 30 seconds
        sections.append({
            'name': 'conclusion',
            'start_time': current_time,
            'end_time': current_time + conclusion_duration,
            'original_volume': 0.3  # Slightly higher for conclusion
        })
        
        return sections
    
    def add_background_music(self, 
                           video_path: str, 
                           background_music_path: str,
                           output_path: str,
                           music_volume: float = 0.1,
                           fade_duration: float = 5.0) -> str:
        """
        Add subtle background music to long-form content
        """
        try:
            logger.info(f"Adding background music with volume {music_volume}")
            
            # Create filter for background music with loop and fade
            filter_complex = (
                f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume},"
                f"afade=t=in:st=0:d={fade_duration},afade=t=out:st=-{fade_duration}:d={fade_duration}[bg_music];"
                f"[0:a][bg_music]amix=inputs=2:duration=first[mixed_audio]"
            )
            
            ffmpeg_command = [
                "ffmpeg",
                "-i", video_path,
                "-i", background_music_path,
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[mixed_audio]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Background music added successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg background music failed: {e.stderr}")
            raise Exception(f"Background music addition failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Background music error: {e}")
            raise Exception(f"Background music error: {e}")
    
    def normalize_audio_levels(self, video_path: str, output_path: str) -> str:
        """
        Normalize audio levels for consistent volume throughout long-form content
        """
        try:
            logger.info("Normalizing audio levels for long-form content")
            
            # Use FFmpeg's loudnorm filter for broadcast-standard audio levels
            ffmpeg_command = [
                "ffmpeg",
                "-i", video_path,
                "-af", "loudnorm=I=-23:TP=-2:LRA=7",
                "-c:v", "copy",
                "-c:a", "aac",
                "-y",
                output_path
            ]
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Audio normalization completed successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio normalization failed: {e.stderr}")
            raise Exception(f"Audio normalization failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Audio normalization error: {e}")
            raise Exception(f"Audio normalization error: {e}")