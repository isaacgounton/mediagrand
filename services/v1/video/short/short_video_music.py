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


# Global music manager instance
_music_manager = MusicManager()

# Function exports that the routes expect
def get_available_music_tags() -> List[Dict[str, str]]:
    """Get available music tags/moods for short videos."""
    moods = _music_manager.list_available_moods()
    return [{"tag": mood, "description": f"{mood.capitalize()} music"} for mood in moods]

def get_music_by_mood(mood: str) -> List[Dict[str, str]]:
    """Get music tags filtered by mood."""
    music_path = _music_manager.get_music_by_mood(mood)
    if music_path:
        return [{"tag": mood, "path": music_path, "description": f"{mood.capitalize()} music"}]
    return []

def get_music_by_tempo(tempo: str) -> List[Dict[str, str]]:
    """Get music tags filtered by tempo."""
    # Map tempo to moods
    tempo_to_mood = {
        "slow": ["calm", "sad"],
        "medium": ["happy", "chill"],
        "fast": ["energetic", "upbeat", "dramatic"]
    }
    
    moods = tempo_to_mood.get(tempo.lower(), ["happy"])
    results = []
    
    for mood in moods:
        music_path = _music_manager.get_music_by_mood(mood)
        if music_path:
            results.append({
                "tag": mood,
                "tempo": tempo,
                "path": music_path,
                "description": f"{mood.capitalize()} {tempo} tempo music"
            })
    
    return results

def get_music_recommendations(content_type: str) -> List[Dict[str, str]]:
    """Get music recommendations based on content type."""
    # Map content types to recommended moods
    content_to_moods = {
        "tutorial": ["calm", "upbeat"],
        "gaming": ["energetic", "epic"],
        "vlog": ["happy", "chill"],
        "product": ["upbeat", "happy"],
        "story": ["dramatic", "epic"],
        "comedy": ["happy", "upbeat"],
        "educational": ["calm", "happy"],
        "travel": ["upbeat", "epic"],
        "food": ["happy", "calm"],
        "fitness": ["energetic", "upbeat"]
    }
    
    moods = content_to_moods.get(content_type.lower(), ["happy", "upbeat"])
    recommendations = []
    
    for mood in moods:
        music_path = _music_manager.get_music_by_mood(mood)
        if music_path:
            recommendations.append({
                "tag": mood,
                "content_type": content_type,
                "path": music_path,
                "description": f"{mood.capitalize()} music recommended for {content_type} content"
            })
    
    return recommendations
