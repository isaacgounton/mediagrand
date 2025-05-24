import os
import json
import logging
import subprocess
from typing import Dict, List, Optional
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

class RemotionRenderer:
    """Service for rendering videos using Remotion."""
    
    def __init__(self):
        self.remotion_path = os.path.join(os.path.dirname(__file__), "../../../remotion")
        
    def _prepare_scene_data(self, 
                           video_url: str,
                           audio_url: str,
                           captions: List[Dict],
                           config: Dict) -> Dict:
        """Prepare scene data for Remotion."""
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

    def render_video(self,
                    video_url: str,
                    audio_url: str,
                    captions: List[Dict],
                    config: Dict,
                    output_path: str,
                    orientation: str = "portrait") -> str:
        """
        Render a video using Remotion.
        
        Args:
            video_url: URL of the background video
            audio_url: URL of the speech audio
            captions: List of caption objects with timing
            config: Configuration for video rendering
            output_path: Path where the rendered video should be saved
            orientation: 'portrait' or 'landscape'
            
        Returns:
            Path to the rendered video file
        """
        try:
            # Prepare scene data
            # Calculate duration from captions
            duration = max(caption["end"] for caption in captions) + 1.0  # Add 1 second padding
            
            scene_data = self._prepare_scene_data(
                video_url=video_url,
                audio_url=audio_url,
                captions=captions,
                config={
                    **config,
                    "orientation": orientation,
                    "duration": duration
                }
            )
            
            # Create temporary JSON file with scene data
            temp_data_path = os.path.join(LOCAL_STORAGE_PATH, "temp_scene_data.json")
            with open(temp_data_path, 'w') as f:
                json.dump(scene_data, f)
            
            # Determine composition ID based on orientation
            composition_id = "PortraitVideo" if orientation == "portrait" else "LandscapeVideo"
            
            # Execute render script
            cmd = [
                "node",
                os.path.join(self.remotion_path, "scripts/render.js"),
                temp_data_path,
                output_path
            ]
            
            # Execute render command
            logger.info(f"Starting Remotion render with props from {temp_data_path}")
            result = subprocess.run(
                cmd,
                cwd=self.remotion_path,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "NODE_ENV": "production",
                    "REMOTION_SAFE_MODE": "1"
                }
            )
            
            # Check for successful rendering
            if result.returncode != 0:
                logger.error(f"Remotion render failed: {result.stderr}")
                raise RuntimeError(f"Video rendering failed: {result.stderr}")
            
            # Clean up temporary file
            os.remove(temp_data_path)
            
            logger.info(f"Video rendered successfully to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in Remotion rendering: {str(e)}")
            raise RuntimeError(f"Video rendering failed: {str(e)}")
