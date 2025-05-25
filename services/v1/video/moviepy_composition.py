import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    TextClip, concatenate_videoclips, concatenate_audioclips, ImageClip
)
from config import LOCAL_STORAGE_PATH
import tempfile
import requests

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
    
    def _get_caption_position(self, position: str, video_size: Tuple[int, int], 
                            has_person_overlay: bool = False) -> Tuple[str, str]:
        """Get caption position for MoviePy, adjusting for person overlays."""
        width, height = video_size
        
        if position == "top":
            # Move captions lower if person overlay present
            y_pos = 80 if has_person_overlay else 50
            return ("center", y_pos)
        elif position == "center":
            return ("center", "center")
        else:  # bottom
            # Default bottom position with more margin
            return ("center", height - 140)
    
    def _create_caption_clip(self, caption: Dict, video_size: Tuple[int, int], 
                           caption_position: str, bg_color: str, 
                           has_person_overlay: bool = False) -> TextClip:
        """Create a single caption clip."""
        width, height = video_size
        
        # Determine font size based on orientation
        font_size = 60 if video_size[1] > video_size[0] else 80  # Smaller for portrait
        
        # Get position with person overlay consideration
        pos = self._get_caption_position(caption_position, video_size, has_person_overlay)
        
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
    
    def _create_person_image_overlay(self, image_url: str, video_size: Tuple[int, int], 
                                   duration: float) -> ImageClip:
        """Create a person image overlay clip."""
        try:
            # Download and prepare image
            image_path = self._url_to_local_path(image_url)
            
            # Determine size based on video orientation
            width, height = video_size
            if width < height:  # Portrait
                overlay_size = (150, 150)  # Smaller to avoid subtitle conflicts
                position = (width - 170, 20)  # Top right with more margin
            else:  # Landscape
                overlay_size = (200, 200)  # Slightly smaller for landscape
                position = (width - 220, 20)  # Top right with more margin
            
            # Create image clip
            image_clip = ImageClip(image_path, duration=duration)
            
            # Resize image to fit overlay size while maintaining aspect ratio
            image_clip = image_clip.resized(height=overlay_size[1])
            
            # If image is too wide after height resize, resize by width instead
            if image_clip.w > overlay_size[0]:
                image_clip = image_clip.resized(width=overlay_size[0])
            
            # Position the image
            image_clip = image_clip.with_position(position)
            
            return image_clip
            
        except Exception as e:
            logger.error(f"Error creating person image overlay: {str(e)}")
            # Return a transparent clip as fallback
            return ImageClip(self._create_placeholder_image(), duration=duration).with_opacity(0)
    
    def _create_person_name_overlay(self, person_name: str, video_size: Tuple[int, int], 
                                  duration: float) -> TextClip:
        """Create a person name overlay clip."""
        try:
            width, height = video_size
            
            # Determine font size and position based on orientation
            # Position below person image but avoid subtitle area
            if width < height:  # Portrait
                font_size = 28  # Smaller font
                position = (width - 170, 180)  # Below person image, adjusted margin
            else:  # Landscape
                font_size = 32  # Slightly smaller font
                position = (width - 220, 230)  # Below person image, adjusted margin
            
            # Create name overlay with background
            name_clip = TextClip(
                text=person_name,
                font_size=font_size,
                font=self.default_font,
                color='white',
                stroke_color='black',
                stroke_width=1,
                method='caption',
                size=(150, None),  # Narrower width to avoid conflicts
                text_align='center'
            ).with_position(position).with_duration(duration)
            
            return name_clip
            
        except Exception as e:
            logger.error(f"Error creating person name overlay: {str(e)}")
            # Return empty text clip as fallback
            return TextClip("", font_size=1, color='transparent').with_duration(duration)
    
    def _create_placeholder_image(self) -> str:
        """Create a simple placeholder image when person image fails to load."""
        try:
            import numpy as np
            from PIL import Image
            
            # Create a simple gray placeholder
            placeholder = np.full((200, 200, 3), 128, dtype=np.uint8)
            img = Image.fromarray(placeholder)
            
            placeholder_path = os.path.join(LOCAL_STORAGE_PATH, "placeholder.png")
            img.save(placeholder_path)
            
            return placeholder_path
            
        except Exception:
            # If PIL is not available, return None and let MoviePy handle the error
            return None
    
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
                    orientation: str = "portrait",
                    person_image_url: Optional[str] = None,
                    person_name: Optional[str] = None) -> str:
        """
        Render a video using MoviePy.
        
        Args:
            video_url: URL or path of the background video
            audio_url: URL or path of the speech audio
            captions: List of caption objects with timing
            config: Configuration for video rendering
            output_path: Path where the rendered video should be saved
            orientation: 'portrait' or 'landscape'
            person_image_url: Optional URL to person image for overlay
            person_name: Optional person name for text overlay
            
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
            has_person_overlay = bool(person_image_url or person_name)
            
            for caption in captions:
                caption_clip = self._create_caption_clip(
                    caption, 
                    target_size, 
                    config.get("caption_position", "bottom"),
                    config.get("caption_background_color", "#000000"),
                    has_person_overlay
                )
                caption_clips.append(caption_clip)
            
            # Create person overlays if provided
            overlay_clips = []
            
            if person_image_url:
                logger.info("Creating person image overlay...")
                try:
                    person_image_clip = self._create_person_image_overlay(
                        person_image_url, target_size, duration
                    )
                    overlay_clips.append(person_image_clip)
                except Exception as e:
                    logger.warning(f"Failed to create person image overlay: {str(e)}")
            
            if person_name:
                logger.info("Creating person name overlay...")
                try:
                    person_name_clip = self._create_person_name_overlay(
                        person_name, target_size, duration
                    )
                    overlay_clips.append(person_name_clip)
                except Exception as e:
                    logger.warning(f"Failed to create person name overlay: {str(e)}")
            
            # Composite all video elements with proper z-ordering
            logger.info("Compositing final video...")
            # Layer order: background video (bottom) -> captions -> person overlays (top)
            video_clips = [background_video] + caption_clips + overlay_clips
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
            for clip in overlay_clips:
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
            # Add extension if missing
            if not any(filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mp3', '.wav', '.png', '.jpg', '.jpeg']):
                # Guess extension based on content type or default
                if 'image' in url_or_path.lower() or any(img_ext in url_or_path.lower() for img_ext in ['png', 'jpg', 'jpeg']):
                    filename += '.jpg'
                elif 'audio' in url_or_path.lower() or any(aud_ext in url_or_path.lower() for aud_ext in ['mp3', 'wav']):
                    filename += '.mp3'
                else:
                    filename += '.mp4'
            
            # Check if file exists in LOCAL_STORAGE_PATH
            local_path = os.path.join(LOCAL_STORAGE_PATH, filename)
            if os.path.exists(local_path):
                return local_path
            else:
                # Download the file
                response = requests.get(url_or_path, timeout=30)
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded {url_or_path} to {local_path}")
                return local_path
        else:
            return url_or_path
