"""
Route for flexible MoviePy video composition.
This route allows for creating custom video compositions using MoviePy,
with more flexibility than the standard video renderer.
"""

from flask import Blueprint, jsonify, request
import os
import uuid
import logging
from services.v1.video.moviepy_compose import MoviePyComposer
from config import LOCAL_STORAGE_PATH
from services.file_management import get_presigned_url, upload_file_to_s3
from services.request_validation import validate_json_request
import json

logger = logging.getLogger(__name__)
moviepy_compose_bp = Blueprint('moviepy_compose', __name__)

@moviepy_compose_bp.route('/v1/video/moviepy/compose', methods=['POST'])
def compose_video():
    """
    Compose a video using MoviePy with a flexible configuration.
    
    Expected JSON body:
    {
        "composition": {
            "type": "composite",
            "orientation": "landscape",  # or "portrait" or "square"
            "clips": [
                {
                    "type": "video",
                    "path": "https://example.com/video.mp4",
                    "position": "center"
                },
                {
                    "type": "text",
                    "text": "Hello World",
                    "font_size": 36,
                    "position": ["center", "bottom"]
                }
                # ... more clips
            ],
            "audio": {
                "path": "https://example.com/audio.mp3",
                "volume": 0.8
            },
            "fps": 30,
            "codec": "libx264"
        }
    }
    
    Returns:
        JSON with video_url to the composed video
    """
    try:
        # Validate request
        request_data = validate_json_request(request)
        
        # Extract composition from request
        composition = request_data.get('composition')
        if not composition:
            return jsonify({"error": "Missing composition in request"}), 400
        
        # Generate job ID and output path
        job_id = str(uuid.uuid4())
        output_filename = f"{job_id}.mp4"
        output_path = os.path.join(LOCAL_STORAGE_PATH, output_filename)
        
        # Initialize composer
        composer = MoviePyComposer()
        
        # Compose video
        logger.info(f"Starting video composition for job {job_id}")
        result_path = composer.compose_video(composition, output_path)
        
        # Upload to S3 if configured
        video_url = get_presigned_url(result_path) if os.path.exists(result_path) else None
        
        # Return result
        return jsonify({
            "success": True,
            "job_id": job_id,
            "video_url": video_url
        })
        
    except Exception as e:
        logger.error(f"Error in video composition: {str(e)}")
        return jsonify({"error": str(e)}), 500


@moviepy_compose_bp.route('/v1/video/moviepy/compose/examples', methods=['GET'])
def get_composition_examples():
    """
    Get example compositions that demonstrate how to use the compose endpoint.
    
    Returns:
        JSON with example compositions
    """
    examples = {
        "basic_video": {
            "type": "video",
            "path": "https://example.com/video.mp4",
            "duration": 10
        },
        
        "text_overlay": {
            "type": "composite",
            "orientation": "landscape",
            "clips": [
                {
                    "type": "video",
                    "path": "https://example.com/video.mp4"
                },
                {
                    "type": "text",
                    "text": "Hello World",
                    "font_size": 48,
                    "color": "white",
                    "stroke_color": "black",
                    "stroke_width": 2,
                    "position": ["center", "bottom"],
                    "start_time": 1,
                    "end_time": 5
                }
            ]
        },
        
        "picture_in_picture": {
            "type": "composite",
            "orientation": "landscape",
            "clips": [
                {
                    "type": "video",
                    "path": "https://example.com/background.mp4"
                },
                {
                    "type": "video",
                    "path": "https://example.com/overlay.mp4",
                    "width": 480,
                    "height": 270,
                    "position": [20, 20]
                }
            ]
        },
        
        "slideshow": {
            "type": "composite",
            "orientation": "landscape",
            "clips": [
                {
                    "type": "color",
                    "color": "black",
                    "duration": 15
                },
                {
                    "type": "image",
                    "path": "https://example.com/image1.jpg",
                    "position": "center",
                    "duration": 5,
                    "start_time": 0
                },
                {
                    "type": "image",
                    "path": "https://example.com/image2.jpg",
                    "position": "center",
                    "duration": 5,
                    "start_time": 5
                },
                {
                    "type": "image",
                    "path": "https://example.com/image3.jpg",
                    "position": "center",
                    "duration": 5,
                    "start_time": 10
                }
            ],
            "audio": {
                "path": "https://example.com/music.mp3",
                "volume": 0.7
            }
        }
    }
    
    return jsonify({"examples": examples})