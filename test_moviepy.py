#!/usr/bin/env python3
"""
Test script for MoviePy video composition
"""
import os
import sys
import tempfile
import logging

# Add the project root to Python path
sys.path.insert(0, '/workspaces/dahopevi')

from services.v1.video.moviepy_composition import MoviePyRenderer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_moviepy_renderer():
    """Test the MoviePy renderer with sample data."""
    try:
        # Initialize renderer
        renderer = MoviePyRenderer()
        logger.info("MoviePy renderer initialized successfully")
        
        # Test font detection
        font_path = renderer._get_default_font()
        logger.info(f"Default font: {font_path}")
        
        # Create test video file (if needed)
        test_video_path = "/tmp/test_video.mp4"
        if not os.path.exists(test_video_path):
            logger.info("Creating test video file...")
            os.system(f"ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=10 -c:v libx264 {test_video_path}")
        
        # Create test audio file (if needed)
        test_audio_path = "/tmp/test_audio.wav"
        if not os.path.exists(test_audio_path):
            logger.info("Creating test audio file...")
            os.system(f"ffmpeg -f lavfi -i 'sine=frequency=440:duration=5' {test_audio_path}")
        
        # Test captions
        test_captions = [
            {"text": "Hello from MoviePy!", "start": 0.0, "end": 2.5},
            {"text": "This is a test caption", "start": 2.5, "end": 5.0}
        ]
        
        # Test config
        test_config = {
            "caption_position": "bottom",
            "caption_background_color": "#000000",
            "music_volume": "medium",
            "orientation": "portrait",
            "duration": 5
        }
        
        # Output path
        output_path = "/tmp/moviepy_test_output.mp4"
        
        logger.info("Starting video rendering test...")
        
        # Test the renderer
        result_path = renderer.render_video(
            video_url=test_video_path,
            audio_url=test_audio_path,
            captions=test_captions,
            config=test_config,
            output_path=output_path,
            orientation="portrait"
        )
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            logger.info(f"✅ Test PASSED! Output video created: {result_path}")
            logger.info(f"File size: {file_size} bytes")
            
            # Get video info
            os.system(f"ffprobe -v quiet -print_format json -show_format -show_streams {result_path}")
            
        else:
            logger.error("❌ Test FAILED! Output video not created")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting MoviePy renderer test...")
    success = test_moviepy_renderer()
    
    if success:
        logger.info("🎉 All tests passed! MoviePy migration successful.")
    else:
        logger.error("💥 Tests failed! Check the errors above.")
        sys.exit(1)
