import os
import logging
import random
import shutil
from typing import Dict, List, Optional
from config import LOCAL_STORAGE_PATH

logger = logging.getLogger(__name__)

class MusicManager:
    """Manages background music for short videos."""
    
    def __init__(self):
        self.music_dir = os.path.join(LOCAL_STORAGE_PATH, "music")
        self.ensure_music_dir()
        
    def ensure_music_dir(self):
        """Ensure music directory exists and contains sample tracks."""
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
    
    def get_music_by_mood(self, mood: str) -> Optional[str]:
        """
        Get a music track path by mood.
        
        Args:
            mood: The desired mood/genre for the music (e.g., 'happy', 'sad', 'epic')
            
        Returns:
            Path to the selected music file or None if not found
        """
        # Map of moods to music file patterns
        mood_patterns = {
            "happy": ["happy_", "upbeat_"],
            "sad": ["sad_", "melancholic_"],
            "epic": ["epic_", "cinematic_"],
            "calm": ["calm_", "peaceful_"],
            "dark": ["dark_", "mysterious_"],
            "energetic": ["energetic_", "dynamic_"],
            "upbeat": ["upbeat_", "happy_"],
            "chill": ["chill_", "calm_"],
            "dramatic": ["dramatic_", "epic_"]
        }
        
        patterns = mood_patterns.get(mood.lower(), ["*"])
        
        # Find all matching music files
        matching_files = []
        for pattern in patterns:
            for file in os.listdir(self.music_dir):
                if file.lower().startswith(pattern) and file.endswith((".mp3", ".wav")):
                    matching_files.append(os.path.join(self.music_dir, file))
        
        # Return random matching file or None if none found
        return random.choice(matching_files) if matching_files else None
    
    def list_available_moods(self) -> List[str]:
        """Get list of available music moods."""
        return [
            "happy",
            "sad",
            "epic",
            "calm",
            "dark",
            "energetic",
            "upbeat",
            "chill",
            "dramatic"
        ]
    
    def add_music_file(self, file_path: str, mood: str) -> str:
        """
        Add a new music file to the collection.
        
        Args:
            file_path: Path to the music file
            mood: Mood/category for the music
            
        Returns:
            Path to the copied music file in the music directory
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Music file not found: {file_path}")
        
        filename = os.path.basename(file_path)
        new_filename = f"{mood.lower()}_{filename}"
        new_path = os.path.join(self.music_dir, new_filename)
        
        shutil.copy2(file_path, new_path)
        return new_path
