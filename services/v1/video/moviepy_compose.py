"""
Flexible MoviePy composition service that allows creating custom video compositions.
This service provides a more flexible way to create videos using MoviePy, allowing
for custom layouts, effects, and compositions beyond the standard renderer.
"""

import os
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    TextClip, ImageClip, ColorClip, concatenate_videoclips, concatenate_audioclips
)
# Import moviepy.config instead of direct importing get_setting
import moviepy.config as mp_config
from config import LOCAL_STORAGE_PATH
import requests

logger = logging.getLogger(__name__)

class MoviePyComposer:
    """
    Flexible service for composing videos using MoviePy with custom layouts and effects.
    Allows for creating complex video compositions beyond standard templates.
    """
    
    def __init__(self):
        # Default video dimensions
        self.portrait_size = (1080, 1920)  # 9:16
        self.landscape_size = (1920, 1080)  # 16:9
        self.square_size = (1080, 1080)     # 1:1
        # Default font path - fallback to system fonts
        self.default_font = self._get_default_font()
    
    def _get_moviepy_setting(self, setting_name, default_value=None):
        """
        Get a setting from moviepy.config in a way that's compatible with different versions.
        
        Args:
            setting_name: The name of the setting to retrieve
            default_value: Value to return if setting doesn't exist
            
        Returns:
            The setting value or default value
        """
        # Try direct attribute access first (newer versions)
        if hasattr(mp_config, setting_name):
            return getattr(mp_config, setting_name)
        
        # Try get_setting if it exists (older versions)
        if hasattr(mp_config, 'get_setting'):
            try:
                return mp_config.get_setting(setting_name)
            except:
                pass
                
        # Finally, look in __dict__ 
        if setting_name in mp_config.__dict__:
            return mp_config.__dict__[setting_name]
            
        return default_value
    
    def _get_default_font(self) -> str:
        """Get the default font path for text rendering."""
        # Try to get font from MoviePy config first
        moviepy_font = self._get_moviepy_setting("FONT", None)
        
        # Create a list of font paths, excluding None values
        font_paths = []
        
        # Add MoviePy configured font if available
        if moviepy_font is not None:
            font_paths.append(moviepy_font)
            
        # Add standard system font paths
        font_paths.extend([
            # Coolify container paths
            "/var/lib/app/fonts/Roboto-Regular.ttf",
            "/var/lib/app/fonts/Arial.ttf",
            "/var/lib/app/fonts/DejaVuSans.ttf",
            # Fallback to common container paths
            "/app/fonts/Roboto-Regular.ttf",
            "/app/fonts/Arial.ttf",
            "/app/fonts/DejaVuSans.ttf",
            # Common Linux paths
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # System font names as fallbacks
            "DejaVuSans",
            "Arial",
            "Roboto-Regular"
        ])
        
        # Check each path for existence
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        logger.warning("No suitable font found, using default system font")
        return "Arial"  # Fallback to system font name
    
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
    
    def _create_clip(self, clip_config: Dict) -> Any:
        """
        Create a clip based on configuration.
        
        Args:
            clip_config: Dictionary with clip configuration
            
        Returns:
            MoviePy clip object
        """
        clip_type = clip_config.get("type", "").lower()
        
        if clip_type == "video":
            return self._create_video_clip(clip_config)
        elif clip_type == "audio":
            return self._create_audio_clip(clip_config)
        elif clip_type == "text":
            return self._create_text_clip(clip_config)
        elif clip_type == "image":
            return self._create_image_clip(clip_config)
        elif clip_type == "color":
            return self._create_color_clip(clip_config)
        elif clip_type == "composite":
            return self._create_composite_clip(clip_config)
        else:
            raise ValueError(f"Unsupported clip type: {clip_type}")
    
    def _create_video_clip(self, config: Dict) -> VideoFileClip:
        """Create a video clip from configuration."""
        # Get video path (from URL if needed)
        video_path = self._url_to_local_path(config.get("path", ""))
        
        # Create video clip
        video_clip = VideoFileClip(video_path)
        
        # Apply transformations
        video_clip = self._apply_clip_transformations(video_clip, config)
        
        return video_clip
    
    def _create_audio_clip(self, config: Dict) -> AudioFileClip:
        """Create an audio clip from configuration."""
        # Get audio path (from URL if needed)
        audio_path = self._url_to_local_path(config.get("path", ""))
        
        # Create audio clip
        audio_clip = AudioFileClip(audio_path)
        
        # Apply volume adjustment
        volume = config.get("volume", 1.0)
        if volume != 1.0:
            audio_clip = audio_clip.with_volume_scaled(volume)
        
        # Apply subclip if specified
        start_time = config.get("start_time")
        end_time = config.get("end_time")
        if start_time is not None or end_time is not None:
            audio_clip = audio_clip.subclip(start_time or 0, end_time)
        
        return audio_clip
    
    def _create_text_clip(self, config: Dict) -> TextClip:
        """Create a text clip from configuration."""
        # Get text properties
        text = config.get("text", "")
        font_size = config.get("font_size", 36)
        font = config.get("font", self.default_font)
        color = config.get("color", "white")
        bg_color = config.get("bg_color")
        stroke_color = config.get("stroke_color")
        stroke_width = config.get("stroke_width", 1)
        method = config.get("method", "caption")
        align = config.get("align", "center")
        
        # Size constraints
        width = config.get("width")
        height = config.get("height")
        size = None
        if width is not None:
            size = (width, height)
        
        # Create text clip
        text_clip = TextClip(
            text=text,
            font_size=font_size,
            font=font,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method=method,
            size=size,
            text_align=align
        )
        
        # Add background if specified
        if bg_color:
            # Parse background color if it's a string
            if isinstance(bg_color, str):
                if bg_color.startswith("rgba("):
                    # Parse RGBA format: rgba(r,g,b,a)
                    rgba_str = bg_color[5:-1]  # Remove "rgba(" and ")"
                    rgba_parts = [float(x.strip()) for x in rgba_str.split(",")]
                    if len(rgba_parts) == 4:
                        bg_color = (int(rgba_parts[0]), int(rgba_parts[1]), int(rgba_parts[2]))
                        # Apply opacity later
                        bg_opacity = rgba_parts[3]
                    else:
                        bg_color = (0, 0, 0)
                        bg_opacity = 0.5
                else:
                    # Use color conversion helper
                    color_map = {
                        "black": (0, 0, 0),
                        "white": (255, 255, 255),
                        "red": (255, 0, 0),
                        "green": (0, 255, 0),
                        "blue": (0, 0, 255),
                        "yellow": (255, 255, 0),
                        "cyan": (0, 255, 255),
                        "magenta": (255, 0, 255),
                        "gray": (128, 128, 128),
                        "grey": (128, 128, 128)
                    }
                    bg_color = color_map.get(bg_color.lower(), (0, 0, 0))
                    bg_opacity = 0.5
            else:
                bg_opacity = 1.0
                
            bg_clip = ColorClip(text_clip.size, color=bg_color, duration=text_clip.duration)
            if bg_opacity < 1.0:
                bg_clip = bg_clip.with_opacity(bg_opacity)
            text_clip = CompositeVideoClip([bg_clip, text_clip])
        
        # Apply transformations
        text_clip = self._apply_clip_transformations(text_clip, config)
        
        return text_clip
    
    def _create_image_clip(self, config: Dict) -> ImageClip:
        """Create an image clip from configuration."""
        # Get image path (from URL if needed)
        image_path = self._url_to_local_path(config.get("path", ""))
        
        # Create image clip
        image_clip = ImageClip(image_path)
        
        # Apply transformations
        image_clip = self._apply_clip_transformations(image_clip, config)
        
        return image_clip
    
    def _create_color_clip(self, config: Dict) -> ColorClip:
        """Create a color clip from configuration."""
        # Get color properties
        color = config.get("color", "black")
        width = config.get("width", 100)
        height = config.get("height", 100)
        
        # Convert color string to RGB tuple if needed
        if isinstance(color, str):
            color_map = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "red": (255, 0, 0),
                "green": (0, 255, 0),
                "blue": (0, 0, 255),
                "yellow": (255, 255, 0),
                "cyan": (0, 255, 255),
                "magenta": (255, 0, 255),
                "gray": (128, 128, 128),
                "grey": (128, 128, 128)
            }
            color = color_map.get(color.lower(), (0, 0, 0))  # Default to black
        
        # Create color clip
        color_clip = ColorClip((width, height), color=color)
        
        # Apply transformations
        color_clip = self._apply_clip_transformations(color_clip, config)
        
        return color_clip
    
    def _create_composite_clip(self, config: Dict) -> CompositeVideoClip:
        """Create a composite clip from configuration."""
        # Get clip configurations
        clips_config = config.get("clips", [])
        size = config.get("size")
        
        if not size:
            orientation = config.get("orientation", "landscape")
            if orientation == "portrait":
                size = self.portrait_size
            elif orientation == "square":
                size = self.square_size
            else:
                size = self.landscape_size
        
        # Create clips
        clips = []
        for clip_config in clips_config:
            try:
                clip = self._create_clip(clip_config)
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Error creating clip: {str(e)}")
        
        # Create composite clip
        composite_clip = CompositeVideoClip(clips, size=size)
        
        # Apply transformations
        composite_clip = self._apply_clip_transformations(composite_clip, config)
        
        return composite_clip
    
    def _apply_clip_transformations(self, clip, config: Dict) -> Any:
        """Apply transformations to a clip."""
        # Apply position
        position = config.get("position")
        if position:
            clip = clip.with_position(position)
        
        # Apply duration
        duration = config.get("duration")
        if duration is not None:
            clip = clip.with_duration(duration)
        
        # Apply timing (subclip for video/audio, subclipped for image/color clips)
        start_time = config.get("start_time")
        end_time = config.get("end_time")
        if start_time is not None or end_time is not None:
            # Check if clip has subclip method (VideoClip, AudioClip)
            if hasattr(clip, 'subclip'):
                clip = clip.subclip(start_time or 0, end_time)
            # For ImageClip and ColorClip, use subclipped
            elif hasattr(clip, 'subclipped'):
                clip = clip.subclipped(start_time or 0, end_time)
            # For clips that don't support timing, just set start time
            elif start_time is not None:
                clip = clip.with_start(start_time)
        
        # Apply resizing
        width = config.get("width")
        height = config.get("height")
        if width is not None and height is not None:
            clip = clip.resized(width=width, height=height)
        
        # Apply opacity
        opacity = config.get("opacity")
        if opacity is not None and opacity < 1.0:
            clip = clip.with_opacity(opacity)
        
        # Apply rotation
        rotation = config.get("rotation")
        if rotation:
            clip = clip.rotate(rotation)
        
        # Apply cross-fade
        crossfade_duration = config.get("crossfade_duration")
        if crossfade_duration:
            clip = clip.crossfadein(crossfade_duration)
        
        return clip
    
    def compose_video(self, composition: Dict, output_path: str) -> str:
        """
        Compose a video based on a flexible composition specification.
        
        Args:
            composition: Dictionary with composition specification
            output_path: Path where the rendered video should be saved
            
        Returns:
            Path to the rendered video file
        """
        try:
            logger.info(f"Starting MoviePy composition to {output_path}")
            
            # Create main composite clip
            main_clip = self._create_clip(composition)
            
            # Handle TTS voice generation if specified
            voice_config = composition.get("voice")
            if voice_config and voice_config.get("type") == "tts":
                try:
                    from services.v1.audio.speech import generate_tts
                    import uuid
                    
                    tts_text = voice_config.get("text", "")
                    tts_engine = voice_config.get("engine", "edge-tts:en-US-AriaNeural")
                    
                    if tts_text:
                        logger.info("Generating TTS audio...")
                        # Generate TTS audio file
                        job_id = str(uuid.uuid4())
                        tts_audio_path, _ = generate_tts(
                            tts=tts_engine.split(":")[0] if ":" in tts_engine else tts_engine,
                            text=tts_text,
                            voice=tts_engine.split(":")[1] if ":" in tts_engine else None,
                            job_id=job_id,
                            output_format="mp3",
                            rate=str(voice_config.get("speed", 1.0))
                        )
                        
                        # Add TTS audio to composition
                        if tts_audio_path and os.path.exists(tts_audio_path):
                            tts_audio_clip = AudioFileClip(tts_audio_path)
                            
                            # If there's existing audio, layer them
                            existing_audio = main_clip.audio
                            if existing_audio:
                                main_clip = main_clip.with_audio(CompositeAudioClip([existing_audio, tts_audio_clip]))
                            else:
                                main_clip = main_clip.with_audio(tts_audio_clip)
                            
                            logger.info("TTS audio added to composition")
                        else:
                            logger.warning("TTS audio generation failed")
                except Exception as e:
                    logger.warning(f"Failed to generate TTS audio: {str(e)}")
            
            # Add audio if specified
            audio_config = composition.get("audio")
            if audio_config:
                audio_clips = []
                
                # Handle multiple audio tracks
                if isinstance(audio_config, list):
                    for audio_track in audio_config:
                        audio_clip = self._create_audio_clip(audio_track)
                        audio_clips.append(audio_clip)
                else:
                    audio_clip = self._create_audio_clip(audio_config)
                    audio_clips.append(audio_clip)
                
                # Create composite audio or combine with existing
                if len(audio_clips) > 0:
                    new_audio = CompositeAudioClip(audio_clips) if len(audio_clips) > 1 else audio_clips[0]
                    
                    # Combine with existing audio if present
                    existing_audio = main_clip.audio
                    if existing_audio:
                        main_clip = main_clip.with_audio(CompositeAudioClip([existing_audio, new_audio]))
                    else:
                        main_clip = main_clip.with_audio(new_audio)
            
            # Get rendering parameters
            fps = composition.get("fps", 30)
            codec = composition.get("codec", "libx264")
            audio_codec = composition.get("audio_codec", "aac")
            bitrate = composition.get("bitrate")
            threads = composition.get("threads")
            
            # Write video file
            logger.info(f"Rendering composition to {output_path}")
            main_clip.write_videofile(
                output_path,
                fps=fps,
                codec=codec,
                audio_codec=audio_codec,
                bitrate=bitrate,
                threads=threads,
                temp_audiofile=f"{output_path}_temp_audio.m4a",
                remove_temp=True,
                logger=None  # Disable MoviePy's verbose logging
            )
            
            # Clean up
            main_clip.close()
            
            logger.info(f"Video composition rendered successfully to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in MoviePy composition: {str(e)}")
            raise RuntimeError(f"Video composition failed: {str(e)}")
