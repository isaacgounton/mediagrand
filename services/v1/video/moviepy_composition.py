import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    TextClip, concatenate_videoclips, concatenate_audioclips
)
from config import LOCAL_STORAGE_PATH
import tempfile

logger = logging.getLogger(__name__)

class MoviePyRenderer:
    """Service for rendering videos using MoviePy."""
    
    def __init__(self):
        # Default video dimensions based on orientation
        self.portrait_size = (1080, 1920)  # 9:16
        self.landscape_size = (1920, 1080)  # 16:9
        
        # Default font path - fallback to system fonts
        self.default_font = self._get_default_font()
    
    def _get_default_font(self) -> str:
        """Get the default font path for text rendering."""
        font_paths = [
            "/app/fonts/Roboto-Regular.ttf",  # Docker container path
            "/app/fonts/Arial.ttf",  # Docker container path
            "/app/fonts/DejaVuSans.ttf",  # Docker container path
            "/workspaces/dahopevi/fonts/Roboto-Regular.ttf",  # Workspace path
            "/workspaces/dahopevi/fonts/Arial.ttf",  # Workspace path
            "/workspaces/dahopevi/fonts/DejaVuSans.ttf",  # Workspace path
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Common Linux path
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "arial.ttf"  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        logger.warning("No suitable font found, using default system font")
        return "Arial"  # Fallback to system font name
    
    def _prepare_scene_data(self, 
                           video_url: str,
                           audio_url: str,
                           captions: List[Dict],
                           config: Dict) -> Dict:
        """Prepare scene data for MoviePy."""
        return {
            "videoUrl": video_url,
            "audioUrl": audio_url,
            "captions": captions,
            "config": {
                "captionPosition": config.get("caption_position", "bottom"),
                "captionBackgroundColor": config.get("caption_background_color", "#000000"),
                "musicVolume": config.get("music_volume", "medium"),
                "orientation": config.get("orientation", "portrait"),
                "duration": config.get("duration", 30),
                "musicUrl": config.get("music_url"),
                "paddingBack": config.get("padding_back", 0.5)
            }
        }
    
    def _get_music_volume_factor(self, volume_setting: str) -> float:
        """Convert music volume setting to factor."""
        volume_map = {
            "high": 0.3,
            "medium": 0.2,
            "low": 0.1,
            "muted": 0.0
        }
        return volume_map.get(volume_setting, 0.2)
    
    def _get_caption_position(self, position: str, video_size: Tuple[int, int]) -> Tuple[str, str]:
        """Get caption position for MoviePy."""
        width, height = video_size
        
        if position == "top":
            return ("center", 50)
        elif position == "center":
            return ("center", "center")
        else:  # bottom
            return ("center", height - 120)
    
    def _create_caption_clip(self, caption: Dict, video_size: Tuple[int, int], 
                           caption_position: str, bg_color: str) -> TextClip:
        """Create a single caption clip."""
        width, height = video_size
        
        # Determine font size based on orientation
        font_size = 60 if video_size[1] > video_size[0] else 80  # Smaller for portrait
        
        # Get position
        pos = self._get_caption_position(caption_position, video_size)
        
        # Create text clip with background
        txt_clip = TextClip(
            text=caption["text"],
            font_size=font_size,
            font=self.default_font,
            color='white',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(width - 40, None),  # Leave 20px margin on each side
            text_align='center'
        ).with_position(pos).with_start(caption["start"]).with_end(caption["end"])
        
        return txt_clip
    
    def _prepare_background_video(self, video_path: str, target_size: Tuple[int, int], 
                                duration: float) -> VideoFileClip:
        """Prepare background video with proper sizing and duration."""
        try:
            # Load video
            video_clip = VideoFileClip(video_path)
            
            # Resize and crop to fit target dimensions while maintaining aspect ratio
            target_width, target_height = target_size
            target_ratio = target_width / target_height
            video_ratio = video_clip.w / video_clip.h
            
            if video_ratio > target_ratio:
                # Video is wider, crop width
                new_width = int(video_clip.h * target_ratio)
                x1 = (video_clip.w - new_width) // 2
                video_clip = video_clip.cropped(x1=x1, x2=x1+new_width)
            else:
                # Video is taller, crop height
                new_height = int(video_clip.w / target_ratio)
                y1 = (video_clip.h - new_height) // 2
                video_clip = video_clip.cropped(y1=y1, y2=y1+new_height)
            
            # Resize to exact target size
            video_clip = video_clip.resized(target_size)
            
            # Loop or trim video to match desired duration
            if video_clip.duration < duration:
                # Loop video if it's shorter than needed
                loops_needed = int(duration / video_clip.duration) + 1
                video_clip = concatenate_videoclips([video_clip] * loops_needed)
            
            # Trim to exact duration
            video_clip = video_clip.subclipped(0, duration)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error preparing background video: {str(e)}")
            raise
    
    def _prepare_audio(self, audio_path: str, music_path: Optional[str], 
                      music_volume: float, duration: float) -> CompositeAudioClip:
        """Prepare composite audio track."""
        try:
            # Load speech audio
            speech_audio = AudioFileClip(audio_path)
            
            audio_clips = [speech_audio]
            
            # Add background music if provided
            if music_path and os.path.exists(music_path) and music_volume > 0:
                music_audio = AudioFileClip(music_path)
                
                # Loop music if needed
                if music_audio.duration < duration:
                    loops_needed = int(duration / music_audio.duration) + 1
                    music_audio = concatenate_audioclips([music_audio] * loops_needed)
                
                # Trim music to duration and set volume
                music_audio = music_audio.subclipped(0, duration).with_volume_scaled(music_volume)
                audio_clips.append(music_audio)
            
            # Create composite audio
            composite_audio = CompositeAudioClip(audio_clips)
            
            return composite_audio
            
        except Exception as e:
            logger.error(f"Error preparing audio: {str(e)}")
            raise
    
    def render_video(self,
                    video_url: str,
                    audio_url: str,
                    captions: List[Dict],
                    config: Dict,
                    output_path: str,
                    orientation: str = "portrait") -> str:
        """
        Render a video using MoviePy.
        
        Args:
            video_url: URL or path of the background video
            audio_url: URL or path of the speech audio
            captions: List of caption objects with timing
            config: Configuration for video rendering
            output_path: Path where the rendered video should be saved
            orientation: 'portrait' or 'landscape'
            
        Returns:
            Path to the rendered video file
        """
        try:
            logger.info(f"Starting MoviePy video rendering to {output_path}")
            
            # Determine video dimensions
            target_size = self.portrait_size if orientation == "portrait" else self.landscape_size
            
            # Calculate duration from captions or config
            duration = config.get("duration", 30.0)
            if captions:
                caption_end = max(caption["end"] for caption in captions)
                padding = config.get("padding_back", 0.5)
                duration = max(duration, caption_end + padding)
            
            # Convert URLs to local paths if needed
            video_path = self._url_to_local_path(video_url)
            audio_path = self._url_to_local_path(audio_url)
            music_path = None
            if config.get("music_url"):
                music_path = self._url_to_local_path(config["music_url"])
            
            # Prepare background video
            logger.info("Preparing background video...")
            background_video = self._prepare_background_video(video_path, target_size, duration)
            
            # Prepare audio
            logger.info("Preparing audio...")
            music_volume = self._get_music_volume_factor(config.get("music_volume", "medium"))
            composite_audio = self._prepare_audio(audio_path, music_path, music_volume, duration)
            
            # Create caption clips
            logger.info("Creating caption clips...")
            caption_clips = []
            for caption in captions:
                caption_clip = self._create_caption_clip(
                    caption, 
                    target_size, 
                    config.get("caption_position", "bottom"),
                    config.get("caption_background_color", "#000000")
                )
                caption_clips.append(caption_clip)
            
            # Composite all video elements
            logger.info("Compositing final video...")
            video_clips = [background_video] + caption_clips
            final_video = CompositeVideoClip(video_clips, size=target_size)
            
            # Set audio
            final_video = final_video.with_audio(composite_audio)
            
            # Render final video
            logger.info("Rendering final video...")
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=f"{output_path}_temp_audio.m4a",
                remove_temp=True,
                logger=None  # Disable MoviePy's verbose logging
            )
            
            # Clean up
            background_video.close()
            composite_audio.close()
            for clip in caption_clips:
                clip.close()
            final_video.close()
            
            logger.info(f"Video rendered successfully to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in MoviePy rendering: {str(e)}")
            raise RuntimeError(f"Video rendering failed: {str(e)}")
    
    def _url_to_local_path(self, url_or_path: str) -> str:
        """Convert URL to local path or return path if already local."""
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            # Extract filename from URL
            filename = url_or_path.split("/")[-1]
            # Check if file exists in LOCAL_STORAGE_PATH
            local_path = os.path.join(LOCAL_STORAGE_PATH, filename)
            if os.path.exists(local_path):
                return local_path
            else:
                # Download the file
                import requests
                response = requests.get(url_or_path)
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return local_path
        else:
            return url_or_path
