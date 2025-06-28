from flask import Blueprint
from app_utils import *
import logging
from services.v1.video.video_overlay import video_overlay
from services.authentication import authenticate
from services.cloud_storage import upload_file

video_overlay_bp = Blueprint('video_overlay', __name__)
logger = logging.getLogger(__name__)

@video_overlay_bp.route('/add-video-overlay', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "base_image_url": {"type": "string", "format": "uri"},
        "overlay_videos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "x": {"type": "number", "minimum": 0, "maximum": 1},
                    "y": {"type": "number", "minimum": 0, "maximum": 1},
                    "width": {"type": "number", "minimum": 0, "maximum": 1},
                    "height": {"type": "number", "minimum": 0, "maximum": 1},
                    "start_time": {"type": "number", "minimum": 0},
                    "end_time": {"type": "number", "minimum": 0},
                    "loop": {"type": "boolean"},
                    "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                    "z_index": {"type": "integer"},
                    "volume": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["url", "x", "y"]
            }
        },
        "output_duration": {"type": "number", "minimum": 1},
        "frame_rate": {"type": "integer", "minimum": 15, "maximum": 60},
        "output_width": {"type": "integer"},
        "output_height": {"type": "integer"},
        "maintain_aspect_ratio": {"type": "boolean"},
        "background_audio_url": {"type": "string", "format": "uri"},
        "background_audio_volume": {"type": "number", "minimum": 0, "maximum": 1},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["base_image_url", "overlay_videos"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def add_video_overlay(job_id, data):
    logger.info(f"Job {job_id}: Received video overlay request")

    try:
        # Process video overlay
        output_filename = video_overlay(data)

        # Upload the resulting file using the unified upload_file() method
        cloud_url = upload_file(output_filename)

        # Log the successful upload
        logger.info(f"Job {job_id}: Converted video uploaded to cloud storage: {cloud_url}")

        # Return the cloud URL for the uploaded file
        return cloud_url, "/add-video-overlay", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error processing video overlay: {str(e)}", exc_info=True)
        return str(e), "/add-video-overlay", 500
