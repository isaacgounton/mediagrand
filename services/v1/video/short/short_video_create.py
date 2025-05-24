import os
import json
import logging
from services.v1.video.short.short_video_status import (
    update_processing_stage,
    update_video_status
)
from services.v1.video.video_composition import RemotionRenderer
from services.v1.video.short.short_video_music import MusicManager
from services.v1.audio.speech import generate_tts
from config import LOCAL_STORAGE_PATH
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PexelsAPI:
    """Wrapper for Pexels API to search and download background videos."""
    
    def __init__(self):
        self.api_key = os.environ.get('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY environment variable is required")
        self.base_url = "https://api.pexels.com/videos"
        
    def search_videos(self, query: str, orientation: str = "portrait", per_page: int = 10) -> List[Dict]:
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "orientation": orientation,
            "per_page": per_page,
            "size": "medium"
        }
        
        try:
            response = requests.get(f"{self.base_url}/search", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("videos", [])
        except Exception as e:
            logger.error(f"Error searching Pexels videos: {str(e)}")
            return []
    
    def download_video(self, video_url: str, output_path: str) -> str:
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return output_path
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise

def create_short_video(scenes: List[Dict], config: Dict, job_id: str) -> str:
    """
    Create a short video from text scenes with background videos, music, and captions.
    
    Args:
        scenes: List of scene objects with text and search_terms
        config: Configuration object for video rendering
        job_id: Unique job identifier
        
    Returns:
        Path to the generated video file
    """
    logger.info(f"Job {job_id}: Starting short video creation with {len(scenes)} scenes")
    
    try:
        # Initialize services
        pexels = PexelsAPI()
        remotion = RemotionRenderer()
        music_manager = MusicManager()
        
        # Set default config values
        voice = config.get("voice", "kokoro:af_sarah")  # Default to Kokoro TTS
        orientation = config.get("orientation", "portrait")
        caption_position = config.get("caption_position", "bottom")
        caption_bg_color = config.get("caption_background_color", "#000000")
        music_tag = config.get("music", "upbeat")
        music_volume = config.get("music_volume", "medium")
        padding_back = config.get("padding_back", 0.5)
        
        # Update initial status
        update_video_status(job_id, {
            "status": "processing",
            "progress": 0,
            "total_scenes": len(scenes)
        })
        
        processed_scenes = []
        
        # Step 1: Generate TTS audio and captions
        update_processing_stage(job_id, "tts_generation", "processing")
        
        for i, scene in enumerate(scenes):
            logger.info(f"Job {job_id}: Processing scene {i+1}/{len(scenes)} - TTS")
            
            # Update progress (0-30%)
            progress = int((i / len(scenes)) * 30)
            update_video_status(job_id, {"progress": progress})
            
            # Generate TTS audio and captions
            tts_engine, voice_name = voice.split(":") if ":" in voice else ("kokoro", voice)
            audio_path, subtitle_path = generate_tts(
                tts=tts_engine,
                text=scene["text"],
                voice=voice_name,
                job_id=f"{job_id}_scene_{i}"
            )
            
            # Read caption data
            with open(subtitle_path, 'r') as f:
                captions_raw = f.read()
            
            # Parse SRT format to get timing
            captions = []
            current_caption = {}
            for line in captions_raw.split('\n'):
                if line.strip() and '-->' in line:
                    times = line.split('-->')
                    current_caption['start'] = _srt_time_to_seconds(times[0].strip())
                    current_caption['end'] = _srt_time_to_seconds(times[1].strip())
                elif line.strip() and not line[0].isdigit():
                    current_caption['text'] = line.strip()
                    captions.append(current_caption.copy())
                    current_caption = {}
            
            scene_data = {
                "audio_path": audio_path,
                "captions": captions
            }
            processed_scenes.append(scene_data)
        
        update_processing_stage(job_id, "tts_generation", "completed")
        update_processing_stage(job_id, "video_search", "processing")
        update_video_status(job_id, {"progress": 30})
        
        # Step 2: Search and download background videos
        for i, scene_data in enumerate(processed_scenes):
            logger.info(f"Job {job_id}: Getting background video for scene {i+1}")
            
            # Update progress (30-60%)
            progress = 30 + int((i / len(processed_scenes)) * 30)
            update_video_status(job_id, {"progress": progress})
            
            # Search for background video
            videos = pexels.search_videos(" ".join(scenes[i]["search_terms"]), orientation=orientation)
            
            background_video_path = None
            if videos:
                video = videos[0]
                video_files = video.get("video_files", [])
                suitable_video = next(
                    (v for v in video_files if v.get("quality") in ["hd", "sd"]),
                    None
                )
                
                if suitable_video:
                    video_filename = f"background_{job_id}_scene_{i}.mp4"
                    video_path = os.path.join(LOCAL_STORAGE_PATH, video_filename)
                    pexels.download_video(suitable_video["link"], video_path)
                    background_video_path = video_path
            
            # Use default background video if no background video found
            if not background_video_path:
                default_video = os.environ.get('DEFAULT_BACKGROUND_VIDEO', '/tmp/assets/placeholder.mp4')
                if os.path.exists(default_video):
                    background_video_path = default_video
                    logger.warning(f"Job {job_id}: No background video found for scene {i+1}, using default background video")
                else:
                    raise Exception(f"No background video found for scene {i+1} and no default background video available")
            
            scene_data["background_video"] = background_video_path
        
        update_processing_stage(job_id, "video_search", "completed")
        update_processing_stage(job_id, "video_rendering", "processing")
        update_video_status(job_id, {"progress": 60})
        
        # Step 3: Render final video with Remotion
        output_filename = f"short_video_{job_id}.mp4"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # For multi-scene videos, we need to concatenate the scenes first
        # For now, we'll just use the first scene
        scene = processed_scenes[0]
        
        # Get background music based on mood
        background_music = None
        if music_tag and music_tag != "none":
            background_music = music_manager.get_music_by_mood(music_tag)
            if not background_music:
                logger.warning(f"No music found for mood: {music_tag}")
                # Try to use default background music from environment
                default_music = os.environ.get('DEFAULT_BACKGROUND_MUSIC')
                if default_music and os.path.exists(default_music):
                    background_music = default_music
                    logger.info(f"Using default background music: {default_music}")

        # Convert local paths to URLs that Remotion can access
        video_url = f"file://{scene['background_video']}"
        audio_url = f"file://{scene['audio_path']}"
        music_url = f"file://{background_music}" if background_music else None
        
        remotion_config = {
            "caption_position": caption_position,
            "caption_background_color": caption_bg_color,
            "music_volume": music_volume,
            "music_url": music_url
        }
        
        # Render with Remotion
        remotion.render_video(
            video_url=video_url,
            audio_url=audio_url,
            captions=scene["captions"],
            config=remotion_config,
            output_path=output_path,
            orientation=orientation
        )
        
        update_processing_stage(job_id, "video_rendering", "completed")
        update_video_status(job_id, {
            "status": "completed",
            "progress": 100,
            "output_file": output_filename
        })
        
        return output_path
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error creating short video: {str(e)}", exc_info=True)
        update_video_status(job_id, {
            "status": "failed",
            "error": str(e)
        })
        raise

def _srt_time_to_seconds(time_str: str) -> float:
    """Convert SRT timestamp to seconds."""
    parts = time_str.replace(',', '.').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds
