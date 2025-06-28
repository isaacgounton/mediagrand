import os
import subprocess
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

class IntelligentAudioMixer:
    """
    Intelligent audio mixing service that blends original video audio with commentary
    Based on viral-shorts-creator approach: original audio at 30%, commentary at 150%
    """
    
    def __init__(self):
        pass
    
    def mix_audio_with_video(self, 
                           video_path: str, 
                           commentary_audio_path: str, 
                           output_path: str,
                           original_volume: float = 0.3,
                           commentary_volume: float = 1.5,
                           commentary_start_delay: float = 0.0) -> str:
        """
        Mix commentary audio with original video audio using FFmpeg
        
        Args:
            video_path: Path to input video file
            commentary_audio_path: Path to commentary audio file 
            output_path: Path for output video file
            original_volume: Volume level for original video audio (0.3 = 30%)
            commentary_volume: Volume level for commentary audio (1.5 = 150%)
            commentary_start_delay: Delay before commentary starts (seconds)
            
        Returns:
            Path to output video file
        """
        try:
            logger.info(f"Mixing audio: video={video_path}, commentary={commentary_audio_path}")
            logger.info(f"Audio levels: original={original_volume}, commentary={commentary_volume}")
            
            # Build FFmpeg command for intelligent audio mixing
            # This replicates the viral-shorts-creator approach
            ffmpeg_command = [
                "ffmpeg",
                "-i", video_path,  # Input video
                "-i", commentary_audio_path,  # Input commentary audio
                "-filter_complex",
                f"[0:a]volume={original_volume}[a0];[1:a]volume={commentary_volume},adelay={int(commentary_start_delay * 1000)}|{int(commentary_start_delay * 1000)}[a1];[a0][a1]amix=inputs=2:duration=first[a]",
                "-map", "0:v",  # Map video from first input
                "-map", "[a]",  # Map mixed audio
                "-c:v", "copy",  # Copy video codec (no re-encoding)
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
            
            logger.info("Audio mixing completed successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio mixing failed: {e.stderr}")
            raise Exception(f"Audio mixing failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Audio mixing error: {e}")
            raise Exception(f"Audio mixing error: {e}")
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            ffprobe_command = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                audio_path
            ]
            
            result = subprocess.run(
                ffprobe_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            duration = float(result.stdout.strip())
            logger.info(f"Audio duration: {duration} seconds")
            return duration
            
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Failed to get audio duration: {e}")
            raise Exception(f"Failed to get audio duration: {e}")
    
    def adjust_video_audio_levels(self, 
                                video_path: str, 
                                output_path: str,
                                commentary_duration: float,
                                pre_commentary_volume: float = 0.1,
                                post_commentary_volume: float = 0.7) -> str:
        """
        Adjust video audio levels based on commentary timing
        Lower volume during commentary, normal volume before/after
        This replicates the editVideo function from viral-shorts-creator
        
        Args:
            video_path: Input video path
            output_path: Output video path  
            commentary_duration: Duration of commentary in seconds
            pre_commentary_volume: Volume during commentary (0.1 = 10%)
            post_commentary_volume: Volume after commentary (0.7 = 70%)
        """
        try:
            logger.info(f"Adjusting video audio levels: commentary_duration={commentary_duration}s")
            
            # Build FFmpeg command to adjust audio levels over time
            ffmpeg_command = [
                "ffmpeg",
                "-i", video_path,
                "-af", f"volume={pre_commentary_volume}:enable='between(t,0,{commentary_duration})',volume={post_commentary_volume}:enable='gt(t,{commentary_duration})'",
                "-c:v", "copy",  # Copy video without re-encoding
                "-y",  # Overwrite output
                output_path
            ]
            
            logger.info(f"Running FFmpeg volume adjustment: {' '.join(ffmpeg_command)}")
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Video audio level adjustment completed")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg volume adjustment failed: {e.stderr}")
            raise Exception(f"Volume adjustment failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Volume adjustment error: {e}")
            raise Exception(f"Volume adjustment error: {e}")
    
    def create_viral_style_short(self, 
                               video_path: str, 
                               commentary_audio_path: str, 
                               output_path: str) -> str:
        """
        Create a viral-style short with intelligent audio mixing
        This combines all the audio processing steps from viral-shorts-creator
        """
        try:
            logger.info("Creating viral-style short with intelligent audio mixing")
            
            # Get commentary duration for intelligent mixing
            commentary_duration = self.get_audio_duration(commentary_audio_path)
            
            # Step 1: Adjust original video audio levels based on commentary timing
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                temp_video_path = temp_video.name
            
            try:
                self.adjust_video_audio_levels(
                    video_path=video_path,
                    output_path=temp_video_path,
                    commentary_duration=commentary_duration
                )
                
                # Step 2: Mix the level-adjusted video with commentary
                final_output = self.mix_audio_with_video(
                    video_path=temp_video_path,
                    commentary_audio_path=commentary_audio_path,
                    output_path=output_path,
                    original_volume=1.0,  # Already adjusted in step 1
                    commentary_volume=1.5,  # Boost commentary
                    commentary_start_delay=0.0
                )
                
                logger.info(f"Viral-style short created: {final_output}")
                return final_output
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
            
        except Exception as e:
            logger.error(f"Failed to create viral-style short: {e}")
            raise Exception(f"Failed to create viral-style short: {e}")